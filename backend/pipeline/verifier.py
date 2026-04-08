"""Claim verifier — checks every citation against its source via Sonnet."""

import logging

from backend.llm.client import LLMClientBase, get_llm_client
from backend.llm.router import get_model
from backend.models import Source, VerificationDetail, VerificationResult, VerificationSummary

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a research verifier. Your job is to check every cited claim in the document against its source.

For each claim with a citation [N]:
1. Find source [N] in the provided sources
2. Read the source content
3. Determine: does the source ACTUALLY support the SPECIFIC claim made?
4. Verdict: confirmed | weakened | unsupported

Rules:
- "Confirmed" = source directly states or clearly implies the claim
- "Weakened" = source partially supports but the claim overstates or misrepresents
- "Unsupported" = source does not support the claim, or says something different
- For "weakened": rewrite the claim to accurately reflect what the source says
- For "unsupported": remove the claim entirely
- NEVER add new claims. Only verify and correct existing ones.
- NEVER invent sources. Only use what is provided.
- Check for dead reasoning: claims that cite a source about Topic A but make a claim about Topic B

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "verified_document": "full corrected markdown document",
  "summary": {
    "confirmed": 15,
    "weakened": 2,
    "removed": 1,
    "details": [
      {"claim": "...", "source_id": 3, "verdict": "weakened", "reason": "source says X not Y", "correction": "revised claim text"}
    ]
  }
}"""


def _build_user_message(document: str, sources: list[Source]) -> str:
    """Format the document and sources for verification."""
    # Sort by relevance (highest first) to match the numbering used by synthesizer.
    ranked = sorted(sources, key=lambda s: s.relevance_score, reverse=True)

    parts: list[str] = [
        "Document to verify:",
        document,
        "\nSources:",
    ]
    for i, s in enumerate(ranked, 1):
        content = s.full_content or s.snippet
        parts.append(
            f"Source [{i}]: {s.title}\n"
            f"URL: {s.url}\n"
            f"Content: {content}"
        )

    return "\n".join(parts)


async def verify(
    document: str,
    sources: list[Source],
    *,
    client: LLMClientBase | None = None,
) -> VerificationResult:
    """Verify every cited claim in *document* against *sources*."""
    llm = client or get_llm_client()

    user_message = _build_user_message(document, sources)

    data = await llm.call(
        system=_SYSTEM_PROMPT,
        user_message=user_message,
        model=get_model("verification"),
        max_tokens=8192,
    )

    try:
        summary_raw = data["summary"]
        # Normalise verdict values — LLM sometimes returns "removed" instead of "unsupported".
        _VERDICT_MAP = {"removed": "unsupported"}
        raw_details = summary_raw.get("details", [])
        for d in raw_details:
            d["verdict"] = _VERDICT_MAP.get(d.get("verdict", ""), d.get("verdict", ""))
        details = [VerificationDetail(**d) for d in raw_details]
        summary = VerificationSummary(
            confirmed=summary_raw["confirmed"],
            weakened=summary_raw["weakened"],
            removed=summary_raw["removed"],
            details=details,
        )
        return VerificationResult(
            verified_document=data["verified_document"],
            summary=summary,
        )
    except Exception as exc:
        raise ValueError(
            f"Verifier returned invalid VerificationResult: {exc}\nRaw keys: {list(data.keys())}"
        ) from exc

"""Research synthesizer — produces a cited markdown document via Sonnet."""

import logging

from backend.llm.client import LLMClientBase, get_llm_client
from backend.llm.router import get_model
from backend.models import Source, SubQuestion

logger = logging.getLogger(__name__)

_MAX_CONTENT_CHARS = 80_000

_SYSTEM_PROMPT = """\
You are a research synthesizer. Write a comprehensive research document from the provided sources.

Rules:
- Every factual claim MUST have an inline citation [1], [2], etc.
- Separate facts from inferences — label inferences with "This suggests..." or "This implies..."
- Never state something as fact if it is your inference
- Structure:
  1. Executive Summary (2-3 paragraphs, key findings only)
  2. Sections organized by theme (NOT by source)
  3. Open Questions (what remains unanswered or contradictory)
  4. Sources (numbered list, every number must match at least one inline citation)
- No unsupported claims. If uncertain, say "Evidence is limited" or "Sources disagree"
- No orphan citations (every [N] in text must appear in Sources)
- No orphan sources (every source must be cited at least once)
- If sources contradict each other, present both sides with their citations

Respond with the full markdown document. No JSON wrapping."""


def _build_user_message(
    query: str,
    sub_questions: list[SubQuestion],
    sources: list[Source],
) -> str:
    """Format query, sub-questions, and sources for the LLM.

    If total content exceeds ~80K chars, truncate lowest-relevance sources
    to snippet-only.
    """
    # Sort a copy by relevance so we can trim the tail if needed.
    ranked = sorted(sources, key=lambda s: (-s.relevance_score, s.url))

    parts: list[str] = [
        f"RESEARCH QUERY: {query}\n",
        "SUB-QUESTIONS:",
    ]
    for sq in sub_questions:
        parts.append(f"  [{sq.id}] {sq.question}")

    parts.append("\nSOURCES:")

    total_chars = sum(len(p) for p in parts)
    source_blocks: list[str] = []

    for i, s in enumerate(ranked, 1):
        content = s.full_content or s.snippet
        block = (
            f"Source [{i}]: {s.title}\n"
            f"URL: {s.url}\n"
            f"Content: {content}"
        )

        if total_chars + len(block) > _MAX_CONTENT_CHARS:
            # Fall back to snippet only.
            block = (
                f"Source [{i}]: {s.title}\n"
                f"URL: {s.url}\n"
                f"Content: {s.snippet}"
            )
        total_chars += len(block)
        source_blocks.append(block)

    parts.extend(source_blocks)
    return "\n".join(parts)


async def synthesize(
    query: str,
    sub_questions: list[SubQuestion],
    sources: list[Source],
    *,
    client: LLMClientBase | None = None,
) -> str:
    """Produce a cited markdown research document from *sources*."""
    llm = client or get_llm_client()

    user_message = _build_user_message(query, sub_questions, sources)

    document = await llm.call_text(
        system=_SYSTEM_PROMPT,
        user_message=user_message,
        model=get_model("synthesis"),
        max_tokens=8192,
    )

    return document

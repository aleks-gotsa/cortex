"""Gap detector — evaluates source coverage per sub-question via Sonnet."""

import logging

from backend.llm.client import LLMClientBase, get_llm_client
from backend.llm.router import get_model
from backend.models import CoverageScore, GapReport, GapRecommendation, Source, SubQuestion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You evaluate research coverage. For each sub-question, assess how well the gathered sources answer it.

Rules:
- Score each sub-question from 0.0 (no coverage) to 1.0 (fully answered)
- For any score below 0.6, generate 2-3 NEW targeted search queries that would fill the specific gap
- New queries must be meaningfully different from the original search terms — use different angles, terminology, or specificity
- Do not repeat queries that already produced the current sources

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "coverage": [
    {"sub_question_id": "q1", "score": 0.9, "assessment": "well covered by sources 1,3,5"},
    {"sub_question_id": "q2", "score": 0.3, "assessment": "only surface-level info found", "follow_up_queries": ["specific query 1", "specific query 2"]}
  ],
  "overall_coverage": 0.65,
  "recommendation": "proceed" | "gather_more"
}"""


def _build_user_message(
    sub_questions: list[SubQuestion],
    sources: list[Source],
) -> str:
    """Format sub-questions and source summaries for the LLM."""
    parts: list[str] = ["SUB-QUESTIONS:"]
    for sq in sub_questions:
        parts.append(f"  [{sq.id}] {sq.question}")
        parts.append(f"    search_terms: {sq.search_terms}")

    parts.append("\nSOURCES:")
    for i, s in enumerate(sources, 1):
        content_preview = (s.full_content or "")[:500]
        parts.append(
            f"  [{i}] (sub_question: {s.sub_question_id}) {s.title}\n"
            f"      snippet: {s.snippet}\n"
            f"      content: {content_preview}"
        )

    return "\n".join(parts)


async def detect_gaps(
    sub_questions: list[SubQuestion],
    sources: list[Source],
    *,
    client: LLMClientBase | None = None,
) -> GapReport:
    """Evaluate how well *sources* cover each sub-question."""
    llm = client or get_llm_client()

    user_message = _build_user_message(sub_questions, sources)

    data = await llm.call(
        system=_SYSTEM_PROMPT,
        user_message=user_message,
        model=get_model("gap_detection"),
        max_tokens=2048,
    )

    try:
        coverage = [CoverageScore(**item) for item in data["coverage"]]
        overall = float(data["overall_coverage"])
        recommendation = (
            GapRecommendation.proceed
            if all(c.score >= 0.6 for c in coverage)
            else GapRecommendation.gather_more
        )
        return GapReport(
            coverage=coverage,
            overall_coverage=overall,
            recommendation=recommendation,
        )
    except Exception as exc:
        raise ValueError(
            f"Gap detector returned invalid GapReport: {exc}\nRaw data: {data}"
        ) from exc

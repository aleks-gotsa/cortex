"""Research planner — decomposes a query into sub-questions via Haiku."""

import logging

from backend.llm.client import LLMClientBase, get_llm_client
from backend.llm.router import get_model
from backend.models import ResearchPlan

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a research planner. Your job is to decompose a research query into independent sub-questions.

Rules:
- Generate 3-6 sub-questions that together fully answer the original query
- Each sub-question must be independently searchable
- For each sub-question, provide 2-3 specific search terms
- If prior research context is provided, account for what is already known and focus on gaps

Respond ONLY with valid JSON, no markdown fences, no preamble:
{
  "sub_questions": [
    {"id": "q1", "question": "...", "search_terms": ["term1", "term2"]}
  ],
  "strategy_notes": "brief note on research approach"
}"""


async def plan(
    query: str,
    prior_context: list[str] | None = None,
    *,
    client: LLMClientBase | None = None,
) -> ResearchPlan:
    """Decompose *query* into 3-6 independent sub-questions."""
    llm = client or get_llm_client()

    user_message = query
    if prior_context:
        context_block = "\n".join(prior_context)
        user_message += (
            f"\n\nPrior research context that may be relevant:\n{context_block}"
        )

    data = await llm.call(
        system=_SYSTEM_PROMPT,
        user_message=user_message,
        model=get_model("planning"),
        max_tokens=1024,
    )

    try:
        return ResearchPlan(**data)
    except Exception as exc:
        raise ValueError(
            f"Planner returned invalid ResearchPlan: {exc}\nRaw data: {data}"
        ) from exc

"""gap detector — the proceed/gather_more recommendation is recomputed in
Python from per-question scores; the LLM's own recommendation is ignored."""

import asyncio

from backend.models import GapRecommendation, SubQuestion
from backend.pipeline.gap_detector import detect_gaps
from tests.conftest import StubLLMClient

_QUESTIONS = [SubQuestion(id="q1", question="?", search_terms=["a"])]


def _payload(scores: list[float], llm_recommendation: str) -> dict:
    return {
        "coverage": [
            {"sub_question_id": f"q{i + 1}", "score": s, "assessment": "a"}
            for i, s in enumerate(scores)
        ],
        "overall_coverage": sum(scores) / len(scores),
        "recommendation": llm_recommendation,
    }


def test_all_scores_above_threshold_proceeds_despite_llm():
    client = StubLLMClient(payload=_payload([0.8, 0.6], "gather_more"))
    report = asyncio.run(detect_gaps(_QUESTIONS, [], client=client))
    assert report.recommendation == GapRecommendation.proceed


def test_any_score_below_threshold_gathers_more_despite_llm():
    client = StubLLMClient(payload=_payload([0.9, 0.59], "proceed"))
    report = asyncio.run(detect_gaps(_QUESTIONS, [], client=client))
    assert report.recommendation == GapRecommendation.gather_more


def test_boundary_score_exactly_at_threshold_proceeds():
    client = StubLLMClient(payload=_payload([0.6], "gather_more"))
    report = asyncio.run(detect_gaps(_QUESTIONS, [], client=client))
    assert report.recommendation == GapRecommendation.proceed

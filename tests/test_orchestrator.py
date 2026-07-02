"""orchestrator helpers — token accounting and follow-up construction."""

from backend.models import CoverageScore, SubQuestion
from backend.pipeline.orchestrator import _follow_up_questions, _token_diff


def test_token_diff_subtracts_snapshots_and_renames_calls():
    before = {"input_tokens": 100, "output_tokens": 50, "calls": 2}
    after = {"input_tokens": 400, "output_tokens": 250, "calls": 5}
    assert _token_diff(before, after) == {
        "input_tokens": 300,
        "output_tokens": 200,
        "llm_calls": 3,
    }


_PLAN_QUESTIONS = [
    SubQuestion(id="q1", question="What is X?", search_terms=["x"]),
    SubQuestion(id="q2", question="How does Y work?", search_terms=["y"]),
]


def test_follow_ups_built_from_low_coverage_with_original_question_text():
    coverage = [
        CoverageScore(sub_question_id="q1", score=0.3, assessment="thin", follow_up_queries=["x deep dive", "x internals"]),
        CoverageScore(sub_question_id="q2", score=0.9, assessment="good"),
    ]
    follow_ups = _follow_up_questions(coverage, _PLAN_QUESTIONS)
    assert len(follow_ups) == 1
    assert follow_ups[0].id == "q1"
    assert follow_ups[0].question == "What is X?"  # original text, new terms
    assert follow_ups[0].search_terms == ["x deep dive", "x internals"]


def test_low_coverage_without_follow_up_queries_is_skipped():
    coverage = [CoverageScore(sub_question_id="q1", score=0.2, assessment="thin")]
    assert _follow_up_questions(coverage, _PLAN_QUESTIONS) == []


def test_unknown_sub_question_id_falls_back_to_id_string():
    coverage = [
        CoverageScore(sub_question_id="q9", score=0.1, assessment="?", follow_up_queries=["z"]),
    ]
    follow_ups = _follow_up_questions(coverage, _PLAN_QUESTIONS)
    assert follow_ups[0].question == "q9"

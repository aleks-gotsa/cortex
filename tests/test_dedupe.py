"""URL dedup semantics — gatherer (first occurrence) vs orchestrator (max relevance)."""

from backend.models import SearchResult, Source
from backend.pipeline.gatherer import _dedupe
from backend.pipeline.orchestrator import _dedupe_keep_max_relevance


def _result(url: str, title: str = "t") -> SearchResult:
    return SearchResult(url=url, title=title, snippet="s", search_engine="serper")


def _source(url: str, score: float) -> Source:
    return Source(
        url=url, title="t", snippet="s", full_content=None,
        relevance_score=score, sub_question_id="q1", search_engine="serper",
    )


def test_gatherer_dedupe_keeps_first_occurrence():
    results = [_result("https://a", "first"), _result("https://b"), _result("https://a", "second")]
    deduped = _dedupe(results)
    assert [r.url for r in deduped] == ["https://a", "https://b"]
    assert deduped[0].title == "first"


def test_gatherer_dedupe_no_duplicates_passthrough():
    results = [_result("https://a"), _result("https://b")]
    assert _dedupe(results) == results


def test_orchestrator_dedupe_keeps_max_relevance_copy():
    sources = [_source("https://a", 0.3), _source("https://b", 0.5), _source("https://a", 0.9)]
    deduped = _dedupe_keep_max_relevance(sources)
    assert [s.url for s in deduped] == ["https://a", "https://b"]
    # First-occurrence position, but the higher-scored copy wins.
    assert deduped[0].relevance_score == 0.9


def test_orchestrator_dedupe_ties_keep_first_copy():
    first, second = _source("https://a", 0.5), _source("https://a", 0.5)
    deduped = _dedupe_keep_max_relevance([first, second])
    assert len(deduped) == 1
    assert deduped[0] is first

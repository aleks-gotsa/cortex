"""Source gatherer — search, scrape, and rerank for each sub-question."""

import asyncio
import logging

from sentence_transformers import CrossEncoder

from backend.models import SearchResult, Source, SubQuestion
from backend.search import serper, tavily
from backend.search.scraper import scrape_many

logger = logging.getLogger(__name__)

# Lazy-loaded singleton — heavy model, load once.
_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder model…")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def preload_reranker() -> None:
    """Pre-load the cross-encoder model. Call at startup to avoid first-request delay."""
    _get_reranker()
    logger.info("Cross-encoder reranker pre-loaded")


async def _search_for_question(
    sq: SubQuestion,
    serper_api_key: str | None = None,
    tavily_api_key: str | None = None,
) -> list[SearchResult]:
    """Run Serper (+ Tavily when available) for every search term in parallel."""
    tasks = []
    for term in sq.search_terms:
        tasks.append(serper.search(term, num_results=10, api_key=serper_api_key))
        tasks.append(tavily.search(term, num_results=10, api_key=tavily_api_key))
    results = await asyncio.gather(*tasks)
    flat: list[SearchResult] = []
    for batch in results:
        flat.extend(batch)
    return flat


def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
    """Keep the first occurrence of each URL."""
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            unique.append(r)
    return unique


def _rerank(question: str, sources: list[Source]) -> list[Source]:
    """Score each source against the question text with the cross-encoder."""
    if not sources:
        return sources

    reranker = _get_reranker()

    pairs = [(question, (s.full_content or s.snippet)[:512]) for s in sources]
    raw_scores = reranker.predict(pairs)

    lo = float(min(raw_scores))
    hi = float(max(raw_scores))
    span = hi - lo

    scored: list[Source] = []
    for src, raw in zip(sources, raw_scores):
        if span == 0:
            # Single source or all identical scores — treat as fully relevant
            normed = 1.0
        else:
            normed = (float(raw) - lo) / span
        scored.append(src.model_copy(update={"relevance_score": round(normed, 4)}))

    scored.sort(key=lambda s: (-s.relevance_score, s.url))
    return scored


async def gather(
    sub_questions: list[SubQuestion],
    pass_number: int = 1,
    serper_api_key: str | None = None,
    tavily_api_key: str | None = None,
) -> list[Source]:
    """Run the full search → scrape → rerank pipeline for one gathering pass."""

    # 1. Search in parallel for all sub-questions.
    search_tasks = [
        _search_for_question(sq, serper_api_key=serper_api_key, tavily_api_key=tavily_api_key)
        for sq in sub_questions
    ]
    per_sq_results: list[list[SearchResult]] = await asyncio.gather(*search_tasks)

    # 2. Dedupe + cap per sub-question, build Source shells.
    all_urls: list[str] = []
    global_seen_urls: set[str] = set()
    sources_by_sq: dict[str, list[Source]] = {}

    for sq, results in zip(sub_questions, per_sq_results):
        deduped = _dedupe(results)
        sources: list[Source] = []
        for r in deduped:
            if r.url in global_seen_urls:
                continue
            global_seen_urls.add(r.url)
            sources.append(
                Source(
                    url=r.url,
                    title=r.title,
                    snippet=r.snippet,
                    full_content=None,
                    relevance_score=0.0,
                    sub_question_id=sq.id,
                    search_engine=r.search_engine,
                )
            )
            all_urls.append(r.url)
            if len(sources) >= 8:
                break
        sources_by_sq[sq.id] = sources

    # 3. Scrape all unique URLs in parallel.
    unique_urls = list(dict.fromkeys(all_urls))
    scraped = await scrape_many(unique_urls, max_concurrent=5)

    # Attach content to sources.
    for sources in sources_by_sq.values():
        for i, src in enumerate(sources):
            content = scraped.get(src.url)
            if content:
                sources[i] = src.model_copy(update={"full_content": content})
            else:
                # Keep but deprioritise sources we couldn't scrape.
                sources[i] = src.model_copy(update={"relevance_score": 0.1})

    # 4. Rerank per sub-question, keep top 5.
    final: list[Source] = []
    for sq in sub_questions:
        sources = sources_by_sq.get(sq.id, [])
        if not sources:
            continue
        ranked = _rerank(sq.question, sources)
        final.extend(ranked[:5])

    logger.info(
        "Gather pass %d: %d sources across %d sub-questions",
        pass_number,
        len(final),
        len(sub_questions),
    )
    return final

"""Async web scraper using crawl4ai."""

import asyncio
import logging

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

logger = logging.getLogger(__name__)

_SKIP_EXTENSIONS = (".pdf", ".zip", ".tar", ".gz")
_MAX_CHARS = 4000


async def _scrape_one(crawler: AsyncWebCrawler, url: str, timeout: int = 10) -> str | None:
    """Scrape a single URL using an existing crawler. Returns None on error."""
    try:
        if any(url.lower().endswith(ext) for ext in _SKIP_EXTENSIONS):
            logger.info("Skipping unsupported file type: %s", url)
            return None

        config = CrawlerRunConfig(
            word_count_threshold=10,
            page_timeout=timeout * 1000,
        )
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            logger.warning("Scrape failed for %s: %s", url, result.error_message)
            return None

        content = result.markdown or ""
        if not content.strip():
            return None

        return content[:_MAX_CHARS]
    except Exception:
        logger.exception("Scrape error for %s", url)
        return None


async def scrape_many(
    urls: list[str], max_concurrent: int = 5
) -> dict[str, str | None]:
    """Scrape multiple URLs in parallel with a shared browser."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _limited(crawler: AsyncWebCrawler, url: str) -> tuple[str, str | None]:
        async with semaphore:
            content = await _scrape_one(crawler, url)
            return url, content

    async with AsyncWebCrawler() as crawler:
        results = await asyncio.gather(*[_limited(crawler, u) for u in urls])

    return dict(results)


async def scrape(url: str, timeout: int = 10) -> str | None:
    """Scrape a single URL. Convenience wrapper — prefer scrape_many for batches."""
    results = await scrape_many([url], max_concurrent=1)
    return results.get(url)

"""Async web scraper using crawl4ai."""

import asyncio
import logging

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

logger = logging.getLogger(__name__)

_SKIP_EXTENSIONS = (".pdf", ".zip", ".tar", ".gz")
_MAX_CHARS = 4000


async def scrape(url: str, timeout: int = 10) -> str | None:
    """Scrape a single URL and return its markdown content.

    Returns None on any error — never raises.
    """
    try:
        if any(url.lower().endswith(ext) for ext in _SKIP_EXTENSIONS):
            logger.info("Skipping unsupported file type: %s", url)
            return None

        config = CrawlerRunConfig(
            word_count_threshold=10,
            page_timeout=timeout * 1000,  # ms
        )
        async with AsyncWebCrawler() as crawler:
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
    """Scrape multiple URLs in parallel with a concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _limited(url: str) -> tuple[str, str | None]:
        async with semaphore:
            content = await scrape(url)
            return url, content

    results = await asyncio.gather(*[_limited(u) for u in urls])
    return dict(results)

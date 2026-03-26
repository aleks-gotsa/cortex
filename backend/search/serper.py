"""Serper.dev async search client."""

import logging

import httpx

from backend.config import settings
from backend.models import SearchResult

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/search"


async def search(query: str, num_results: int = 10) -> list[SearchResult]:
    """Run a web search via Serper.dev and return unified SearchResult list."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _SERPER_URL,
                headers={"X-API-KEY": settings.SERPER_API_KEY},
                json={"q": query, "num": num_results},
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        logger.exception("Serper search failed for query=%r", query)
        return []

    results: list[SearchResult] = []
    for item in data.get("organic", []):
        results.append(
            SearchResult(
                url=item.get("link", ""),
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                search_engine="serper",
            )
        )
    return results

"""Brave Search async client."""

import logging

import httpx

from backend.config import settings
from backend.models import SearchResult

logger = logging.getLogger(__name__)

_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"


async def search(query: str, num_results: int = 10) -> list[SearchResult]:
    """Run a web search via Brave Search API and return unified SearchResult list."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                _BRAVE_URL,
                headers={
                    "X-Subscription-Token": settings.BRAVE_API_KEY,
                    "Accept": "application/json",
                },
                params={"q": query, "count": num_results},
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        logger.exception("Brave search failed for query=%r", query)
        return []

    results: list[SearchResult] = []
    for item in data.get("web", {}).get("results", []):
        results.append(
            SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("description", ""),
                search_engine="brave",
            )
        )
    return results

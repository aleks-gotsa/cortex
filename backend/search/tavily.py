"""Tavily Search async client."""

import logging

import httpx

from backend.config import settings
from backend.models import SearchResult

logger = logging.getLogger(__name__)

_TAVILY_URL = "https://api.tavily.com/search"


async def search(query: str, num_results: int = 10) -> list[SearchResult]:
    """Run a web search via Tavily Search API and return unified SearchResult list."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _TAVILY_URL,
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "basic",
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        logger.exception("Tavily search failed for query=%r", query)
        return []

    results: list[SearchResult] = []
    for item in data.get("results", []):
        results.append(
            SearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                snippet=item.get("content", ""),
                search_engine="tavily",
            )
        )
    return results

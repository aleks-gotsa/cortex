"""Serper.dev async search client."""

import logging

import httpx

from backend.config import settings
from backend.models import SearchResult

logger = logging.getLogger(__name__)

_SERPER_URL = "https://google.serper.dev/search"

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def search(query: str, num_results: int = 10, api_key: str | None = None) -> list[SearchResult]:
    """Run a web search via Serper.dev and return unified SearchResult list."""
    resolved_key = api_key or settings.SERPER_API_KEY
    try:
        client = _get_client()
        response = await client.post(
            _SERPER_URL,
            headers={"X-API-KEY": resolved_key},
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

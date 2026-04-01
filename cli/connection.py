"""Backend connection — HTTP client and SSE stream parser."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SSEEvent:
    """A single parsed Server-Sent Event."""

    event: str
    data: dict[str, Any]


class ConnectionError(Exception):
    """Raised when the backend is unreachable."""


class StreamError(Exception):
    """Raised when the SSE stream fails mid-research."""


async def check_backend(backend_url: str) -> bool:
    """Return True if the backend is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{backend_url}/research/history")
            return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        return False


async def stream_research(
    backend_url: str,
    query: str,
    depth: str = "standard",
    use_memory: bool = True,
) -> Any:
    """POST /research and yield SSEEvent objects as they arrive."""
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
    body = {"query": query, "depth": depth, "use_memory": use_memory}

    if os.environ.get("ANTHROPIC_API_KEY"):
        body["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    if os.environ.get("SERPER_API_KEY"):
        body["serper_api_key"] = os.environ["SERPER_API_KEY"]
    if os.environ.get("TAVILY_API_KEY"):
        body["tavily_api_key"] = os.environ["TAVILY_API_KEY"]

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{backend_url}/research",
                json=body,
            ) as response:
                response.raise_for_status()
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n\n" in buffer:
                        frame, buffer = buffer.split("\n\n", 1)
                        event = _parse_sse_frame(frame)
                        if event is not None:
                            yield event
    except httpx.ConnectError as exc:
        raise ConnectionError(str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise StreamError(f"Timed out after 300s: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise StreamError(f"Backend error: {exc.response.status_code}") from exc


async def fetch_history(backend_url: str, limit: int = 50) -> list[dict[str, Any]]:
    """GET /research/history."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{backend_url}/research/history", params={"limit": limit}
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_detail(backend_url: str, research_id: str) -> dict[str, Any] | None:
    """GET /research/{id}. Returns None on 404."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{backend_url}/research/{research_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


def _parse_sse_frame(frame: str) -> SSEEvent | None:
    """Parse a single SSE frame into an SSEEvent, or None on error."""
    event_name = ""
    data_lines: list[str] = []

    for line in frame.strip().splitlines():
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:") :].strip())

    if not event_name:
        return None

    raw_data = "\n".join(data_lines)
    try:
        data = json.loads(raw_data) if raw_data else {}
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in SSE event %r: %s", event_name, raw_data)
        return None

    return SSEEvent(event=event_name, data=data)

"""
Cortex MCP Server — exposes the research pipeline as MCP tools.

Tools:
    research      — Run the full Cortex deep research pipeline (30-90s)
    recall        — Search Qdrant memory for relevant prior research chunks
    history       — List past research runs
    get_research  — Retrieve a specific past research result

Run:
    python mcp_server.py
    fastmcp run mcp_server.py
"""

# ── Load .env BEFORE any backend imports ────────────────────────────────────
# backend/config.py reads env vars at import time via pydantic-settings,
# so dotenv must be loaded first.

from dotenv import load_dotenv

load_dotenv()

# ── Imports ─────────────────────────────────────────────────────────────────

import asyncio
import json
import logging

from fastmcp import FastMCP

from backend.models import Depth, ResearchRequest
from backend.pipeline.gatherer import preload_reranker
from backend.pipeline.memory import recall as _recall
from backend.pipeline.orchestrator import run_research
from backend.storage import db

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("cortex.mcp")

# ── MCP Server ──────────────────────────────────────────────────────────────

mcp = FastMCP(
    "Cortex",
    instructions=(
        "Cortex is a deep research engine. Use the 'research' tool to run a "
        "full research pipeline on any topic. Use 'recall' to search prior "
        "research memory. Use 'history' and 'get_research' to browse past runs."
    ),
)

_db_initialized = False
_db_lock = asyncio.Lock()


_reranker_loaded = False


async def _ensure_db() -> None:
    """Initialize the SQLite database and pre-load models once."""
    global _db_initialized, _reranker_loaded  # noqa: PLW0603
    if _db_initialized:
        return
    async with _db_lock:
        if not _db_initialized:
            await db.init_db()
            if not _reranker_loaded:
                preload_reranker()
                _reranker_loaded = True
            _db_initialized = True


# ── Tool: research ──────────────────────────────────────────────────────────


@mcp.tool()
async def research(
    query: str,
    depth: str = "standard",
    use_memory: bool = True,
) -> str:
    """Run the full Cortex deep research pipeline.

    Searches the web, detects knowledge gaps, iteratively gathers more
    sources, synthesizes a document with inline citations, and verifies
    every claim against its source.

    Args:
        query: The research question or topic.
        depth: Research depth — "quick" (1 pass, ~30s), "standard"
               (2 passes, ~60s), or "deep" (3 passes, ~90s).
        use_memory: Whether to recall prior research from Qdrant and
                    store this result for future recall.

    Returns:
        JSON with document, sources, verification summary, cost, and
        research_id.
    """
    try:
        depth_enum = Depth(depth)
    except ValueError:
        valid = [d.value for d in Depth]
        return json.dumps({"error": f"Invalid depth '{depth}'. Valid values: {valid}"})

    try:
        await _ensure_db()

        request = ResearchRequest(
            query=query,
            depth=depth_enum,
            use_memory=use_memory,
        )

        # Consume the full async generator; keep only the final event.
        final_event = None
        async for event in run_research(request):
            if event.stage == "complete":
                final_event = event

        if final_event is None:
            return json.dumps({"error": "Pipeline completed without a final event."})

        return json.dumps(final_event.data, ensure_ascii=False)

    except Exception as exc:
        logger.exception("research tool failed")
        return json.dumps({"error": f"Research failed: {exc}"})


# ── Tool: recall ────────────────────────────────────────────────────────────


@mcp.tool()
async def recall(query: str, top_k: int = 5) -> str:
    """Search Qdrant vector memory for relevant prior research chunks.

    Use this to check what Cortex already knows before running a new
    research pipeline.

    Args:
        query: The search query to match against prior research.
        top_k: Maximum number of chunks to return (default 5).

    Returns:
        JSON list of text chunks from prior research, ranked by
        relevance.
    """
    try:
        top_k = max(1, min(top_k, 50))
        chunks = await _recall(query, top_k=top_k)
        return json.dumps({"chunks": chunks, "count": len(chunks)}, ensure_ascii=False)

    except Exception as exc:
        logger.exception("recall tool failed")
        return json.dumps({"error": f"Recall failed: {exc}"})


# ── Tool: history ───────────────────────────────────────────────────────────


@mcp.tool()
async def history(limit: int = 20) -> str:
    """List past Cortex research runs.

    Args:
        limit: Maximum number of runs to return (default 20).

    Returns:
        JSON list of run metadata (id, query, depth, status, cost,
        timestamps).
    """
    try:
        await _ensure_db()
        limit = max(1, min(limit, 100))
        runs = await db.list_runs(limit=limit)
        return json.dumps({"runs": runs, "count": len(runs)}, default=str)

    except Exception as exc:
        logger.exception("history tool failed")
        return json.dumps({"error": f"History failed: {exc}"})


# ── Tool: get_research ──────────────────────────────────────────────────────


@mcp.tool()
async def get_research(research_id: str) -> str:
    """Retrieve a specific past research result by ID.

    Args:
        research_id: The research run ID (from history or a previous
                     research result).

    Returns:
        JSON with the full research document, sources, verification
        data, and run metadata.
    """
    try:
        await _ensure_db()

        run = await db.get_run(research_id)
        if run is None:
            return json.dumps({"error": f"No research run found with id '{research_id}'."})

        result = await db.get_result(research_id)
        if result is None:
            return json.dumps(
                {
                    "error": f"Run '{research_id}' exists but has no result (status: {run.get('status', 'unknown')}).",
                    "run": run,
                },
                default=str,
            )

        return json.dumps(
            {
                "run": run,
                "document": result.get("document_md"),
                "sources": result.get("sources_json"),
                "verification": result.get("verification_json"),
            },
            default=str,
            ensure_ascii=False,
        )

    except Exception as exc:
        logger.exception("get_research tool failed")
        return json.dumps({"error": f"Get research failed: {exc}"})


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()

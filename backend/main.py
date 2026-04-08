"""FastAPI application — SSE endpoint for research pipeline."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.models import ResearchRequest
from backend.pipeline.gatherer import preload_reranker
from backend.pipeline.orchestrator import run_research
from backend.storage import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Path("data").mkdir(exist_ok=True)
    await db.init_db()
    preload_reranker()
    yield
    # Shutdown (nothing needed)


app = FastAPI(title="Cortex", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ── SSE research endpoint ────────────────────────────────────────────────


async def _sse_stream(request: ResearchRequest):
    """Yield SSE-formatted events from the research pipeline."""
    async for event in run_research(request):
        payload = json.dumps(event.data, ensure_ascii=False)
        yield f"event: {event.stage}\ndata: {payload}\n\n"


@app.post("/research")
async def research(request: ResearchRequest) -> StreamingResponse:
    anthropic_key = request.anthropic_api_key or settings.ANTHROPIC_API_KEY
    serper_key = request.serper_api_key or settings.SERPER_API_KEY
    tavily_key = request.tavily_api_key or settings.TAVILY_API_KEY

    if not anthropic_key or not serper_key or not tavily_key:
        raise HTTPException(
            status_code=400,
            detail="API keys required. Provide anthropic_api_key, serper_api_key, and tavily_api_key in the request body.",
        )

    # Write resolved keys back so the pipeline always reads from request
    request.anthropic_api_key = anthropic_key
    request.serper_api_key = serper_key
    request.tavily_api_key = tavily_key

    return StreamingResponse(
        _sse_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── History / retrieval endpoints ────────────────────────────────────────


@app.get("/research/history")
async def research_history(limit: int = 50) -> list[dict]:
    return await db.list_runs(limit=limit)


@app.delete("/research/{research_id}")
async def research_delete(research_id: str) -> dict:
    deleted = await db.delete_run(research_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Research run not found")
    return {"deleted": True}


@app.get("/research/{research_id}")
async def research_detail(research_id: str) -> dict:
    run = await db.get_run(research_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")
    result = await db.get_result(research_id)
    return {"run": run, "result": result}

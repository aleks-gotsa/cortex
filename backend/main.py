"""FastAPI application — SSE endpoint for research pipeline."""

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.models import ResearchRequest
from backend.pipeline.orchestrator import run_research

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="Cortex", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    Path("data").mkdir(exist_ok=True)


async def _sse_stream(request: ResearchRequest):
    """Yield SSE-formatted events from the research pipeline."""
    async for event in run_research(request):
        payload = json.dumps(event.data, ensure_ascii=False)
        yield f"event: {event.stage}\ndata: {payload}\n\n"


@app.post("/research")
async def research(request: ResearchRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

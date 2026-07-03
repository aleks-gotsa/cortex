"""Smoke test for the local backend (LLM_BACKEND=local).

Verifies one JSON call() and one call_text() against the configured
OpenAI-compatible endpoint, then — if a Serper key is available — runs the
full research pipeline end-to-end. Zero hosted-API usage for inference.

Usage: python scripts/local_smoke.py
"""

import asyncio
import os
import sys
from pathlib import Path

os.environ["LLM_BACKEND"] = "local"  # must win before backend.config is imported

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings  # noqa: E402
from backend.llm.client import get_llm_client  # noqa: E402
from backend.llm.router import get_model, local_task_model  # noqa: E402


async def smoke_calls() -> None:
    client = get_llm_client()
    print(f"client: {type(client).__name__} @ {settings.LOCAL_BASE_URL}")
    print(f"task→model map: {local_task_model()}")

    data = await client.call(
        system="You are a JSON API. Answer with a single JSON object.",
        user_message='Return {"status": "ok", "answer": <the value of 2+2>}.',
        model=get_model("planning"),
        max_tokens=200,
    )
    assert isinstance(data, dict) and data, data
    print(f"call() JSON ok: {data}")

    text = await client.call_text(
        system="You are a concise technical writer.",
        user_message="In one sentence: what does a cross-encoder reranker do?",
        model=get_model("synthesis"),
        max_tokens=2048,
    )
    assert text.strip(), "empty call_text() response"
    print(f"call_text() ok ({len(text)} chars): {text.strip()[:160]}")

    usage = client.get_usage()
    assert usage["calls"] >= 2 and usage["output_tokens"] > 0, usage
    print(f"usage: {usage}")
    print(f"usage by model: {client.get_usage_by_model()}")
    await client.close()


async def smoke_pipeline() -> None:
    from backend.models import Depth, ResearchRequest
    from backend.pipeline.orchestrator import run_research

    request = ResearchRequest(
        query="What is retrieval-augmented generation?",
        depth=Depth.quick,
        use_memory=False,
    )
    async for event in run_research(request):
        keys = ", ".join(sorted(event.data)) or "—"
        print(f"[{event.stage}] {keys}")
        if event.stage == "error":
            raise SystemExit(f"pipeline error: {event.data}")


async def main() -> None:
    await smoke_calls()
    if settings.SERPER_API_KEY:
        print("\nSERPER_API_KEY found — running the full pipeline (depth=quick)…")
        await smoke_pipeline()
    else:
        print("\nNo SERPER_API_KEY — full-pipeline smoke deferred to the frozen-corpus fixtures.")


if __name__ == "__main__":
    asyncio.run(main())

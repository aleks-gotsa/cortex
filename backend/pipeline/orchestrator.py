"""Pipeline orchestrator — runs the full research loop and yields SSE events."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from backend.llm.client import get_llm_client
from backend.llm.router import calculate_cost
from backend.models import (
    Depth,
    GapRecommendation,
    ResearchEvent,
    ResearchRequest,
    SubQuestion,
)
from backend.config import settings
from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather
from backend.pipeline.gap_detector import detect_gaps
from backend.pipeline.memory import recall, store_research
from backend.pipeline.synthesizer import synthesize
from backend.pipeline.verifier import verify
from backend.storage import db

logger = logging.getLogger(__name__)

_MAX_PASSES = {
    Depth.quick: 1,
    Depth.standard: 2,
    Depth.deep: 3,
}


def _token_diff(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    """Return the token delta between two usage snapshots."""
    return {
        "input_tokens": after["input_tokens"] - before["input_tokens"],
        "output_tokens": after["output_tokens"] - before["output_tokens"],
        "llm_calls": after["calls"] - before["calls"],
    }


async def _emit(research_id: str, event: ResearchEvent) -> ResearchEvent:
    """Persist event to SQLite and return it for yielding."""
    await db.save_event(research_id, event.stage, json.dumps(event.data, ensure_ascii=False))
    return event


async def run_research(
    request: ResearchRequest,
) -> AsyncGenerator[ResearchEvent, None]:
    """Execute the full Cortex pipeline, yielding events for each stage."""
    research_id = uuid.uuid4().hex[:12]
    client = get_llm_client(api_key=request.anthropic_api_key)
    client.reset_usage()
    max_passes = _MAX_PASSES[request.depth]
    serper_key = request.serper_api_key
    tavily_key = request.tavily_api_key

    # Persist the run.
    await db.create_run(research_id, request.query, request.depth.value)

    try:
        # ── 0. RECALL prior context ──────────────────────────────────────
        prior_context: list[str] | None = None
        if request.use_memory:
            prior_context = await recall(request.query)
            if prior_context:
                logger.info("Recalled %d chunks from prior research", len(prior_context))

        # ── 1. PLAN ──────────────────────────────────────────────────────
        _before = client.get_usage()
        research_plan = await plan(request.query, prior_context=prior_context, client=client)
        _plan_tokens = _token_diff(_before, client.get_usage())
        yield await _emit(
            research_id,
            ResearchEvent(
                stage="planning",
                data={
                    "sub_questions": [sq.question for sq in research_plan.sub_questions],
                    "strategy": research_plan.strategy_notes,
                    "tokens": _plan_tokens,
                },
            ),
        )

        # ── 2. GATHER (iterative) ────────────────────────────────────────
        all_sources = []
        current_questions = research_plan.sub_questions

        for pass_num in range(1, max_passes + 1):
            sources = await gather(
                current_questions,
                pass_number=pass_num,
                serper_api_key=serper_key,
                tavily_api_key=tavily_key,
            )
            all_sources.extend(sources)

            yield await _emit(
                research_id,
                ResearchEvent(
                    stage="gathering",
                    data={
                        "pass": pass_num,
                        "sources_found": len(sources),
                        "queries_used": [
                            term
                            for sq in current_questions
                            for term in sq.search_terms
                        ],
                    },
                ),
            )

            # Skip gap detection for quick depth or final pass.
            if request.depth == Depth.quick or pass_num == max_passes:
                break

            # ── 3. GAP DETECT ────────────────────────────────────────────
            _before = client.get_usage()
            gap_report = await detect_gaps(
                research_plan.sub_questions, all_sources, client=client
            )
            _gap_tokens = _token_diff(_before, client.get_usage())

            coverage_dict = {c.sub_question_id: c.score for c in gap_report.coverage}
            gaps = [
                c.assessment
                for c in gap_report.coverage
                if c.score < 0.6
            ]

            yield await _emit(
                research_id,
                ResearchEvent(
                    stage="gap_detection",
                    data={
                        "coverage": coverage_dict,
                        "gaps": gaps,
                        "tokens": _gap_tokens,
                    },
                ),
            )

            if gap_report.recommendation == GapRecommendation.proceed:
                break

            # Build follow-up sub-questions for the next pass.
            follow_ups: list[SubQuestion] = []
            for c in gap_report.coverage:
                if c.score < 0.6 and c.follow_up_queries:
                    follow_ups.append(
                        SubQuestion(
                            id=c.sub_question_id,
                            question=next(
                                (sq.question for sq in research_plan.sub_questions if sq.id == c.sub_question_id),
                                c.sub_question_id,
                            ),
                            search_terms=c.follow_up_queries,
                        )
                    )

            if not follow_ups:
                break
            current_questions = follow_ups

        # ── 4. SYNTHESIZE ────────────────────────────────────────────────
        yield await _emit(research_id, ResearchEvent(stage="synthesizing", data={}))

        _before = client.get_usage()
        document = await synthesize(
            request.query,
            research_plan.sub_questions,
            all_sources,
            client=client,
        )
        _synth_tokens = _token_diff(_before, client.get_usage())
        yield await _emit(
            research_id,
            ResearchEvent(stage="synthesis", data={"tokens": _synth_tokens}),
        )

        # ── 5. VERIFY ────────────────────────────────────────────────────
        _before = client.get_usage()
        verification = await verify(document, all_sources, client=client)
        _verify_tokens = _token_diff(_before, client.get_usage())

        yield await _emit(
            research_id,
            ResearchEvent(
                stage="verifying",
                data={
                    "claims_total": (
                        verification.summary.confirmed
                        + verification.summary.weakened
                        + verification.summary.removed
                    ),
                    "confirmed": verification.summary.confirmed,
                    "weakened": verification.summary.weakened,
                    "removed": verification.summary.removed,
                    "tokens": _verify_tokens,
                },
            ),
        )

        # ── 6. MEMORY ───────────────────────────────────────────────────
        if request.use_memory:
            chunks_stored = await store_research(
                research_id, request.query, verification.verified_document
            )
            yield await _emit(
                research_id,
                ResearchEvent(
                    stage="memory",
                    data={
                        "chunks_stored": chunks_stored,
                        "collection": settings.QDRANT_COLLECTION,
                    },
                ),
            )

        # ── 7. COST ─────────────────────────────────────────────────────
        usage_by_model = client.get_usage_by_model()
        cost_usd = round(
            sum(
                calculate_cost(model, c["input_tokens"], c["output_tokens"])
                for model, c in usage_by_model.items()
                if not model.startswith("_")  # skip internal keys like _dynamo_worker_calls
            ),
            4,
        )

        # ── 8. PERSIST RESULT ────────────────────────────────────────────
        sources_list = [
            {"url": s.url, "title": s.title, "relevance_score": s.relevance_score}
            for s in all_sources
        ]

        await db.save_result(
            research_id=research_id,
            document_md=verification.verified_document,
            sources_json=json.dumps(sources_list, ensure_ascii=False),
            verification_json=json.dumps(verification.summary.model_dump(), ensure_ascii=False),
        )
        await db.update_run(
            research_id,
            status="completed",
            cost_usd=cost_usd,
            completed_at=datetime.now(timezone.utc),
        )

        # ── 9. COMPLETE ─────────────────────────────────────────────────
        yield await _emit(
            research_id,
            ResearchEvent(
                stage="complete",
                data={
                    "document": verification.verified_document,
                    "sources": sources_list,
                    "cost_usd": cost_usd,
                    "research_id": research_id,
                },
            ),
        )
    except Exception as exc:
        logger.exception("Pipeline failed for %s", research_id)
        await db.update_run(research_id, status="failed")
        yield await _emit(
            research_id,
            ResearchEvent(
                stage="error",
                data={"error": str(exc)},
            ),
        )
    finally:
        await client.close()

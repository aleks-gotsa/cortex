"""Pipeline orchestrator — runs the full research loop and yields SSE events."""

import logging
import uuid
from collections.abc import AsyncGenerator

from backend.llm.client import LLMClient
from backend.llm.router import calculate_cost, PRICING_PER_MILLION
from backend.models import (
    Depth,
    GapRecommendation,
    ResearchEvent,
    ResearchRequest,
    SubQuestion,
)
from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather
from backend.pipeline.gap_detector import detect_gaps
from backend.pipeline.synthesizer import synthesize
from backend.pipeline.verifier import verify

logger = logging.getLogger(__name__)

_MAX_PASSES = {
    Depth.quick: 1,
    Depth.standard: 2,
    Depth.deep: 3,
}


async def run_research(
    request: ResearchRequest,
) -> AsyncGenerator[ResearchEvent, None]:
    """Execute the full Cortex pipeline, yielding events for each stage."""
    research_id = uuid.uuid4().hex[:12]
    client = LLMClient()
    client.reset_usage()
    max_passes = _MAX_PASSES[request.depth]

    # ── 1. PLAN ──────────────────────────────────────────────────────────
    research_plan = await plan(request.query, client=client)
    yield ResearchEvent(
        stage="planning",
        data={
            "sub_questions": [sq.question for sq in research_plan.sub_questions],
            "strategy": research_plan.strategy_notes,
        },
    )

    # ── 2. GATHER (iterative) ────────────────────────────────────────────
    all_sources = []
    current_questions = research_plan.sub_questions

    for pass_num in range(1, max_passes + 1):
        sources = await gather(current_questions, pass_number=pass_num)
        all_sources.extend(sources)

        yield ResearchEvent(
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
        )

        # Skip gap detection for quick depth or final pass.
        if request.depth == Depth.quick or pass_num == max_passes:
            break

        # ── 3. GAP DETECT ────────────────────────────────────────────────
        gap_report = await detect_gaps(
            research_plan.sub_questions, all_sources, client=client
        )

        coverage_dict = {c.sub_question_id: c.score for c in gap_report.coverage}
        gaps = [
            c.assessment
            for c in gap_report.coverage
            if c.score < 0.6
        ]

        yield ResearchEvent(
            stage="gap_detection",
            data={
                "coverage": coverage_dict,
                "gaps": gaps,
            },
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

    # ── 4. SYNTHESIZE ────────────────────────────────────────────────────
    yield ResearchEvent(stage="synthesizing", data={})

    document = await synthesize(
        request.query,
        research_plan.sub_questions,
        all_sources,
        client=client,
    )

    # ── 5. VERIFY ────────────────────────────────────────────────────────
    verification = await verify(document, all_sources, client=client)

    yield ResearchEvent(
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
        },
    )

    # ── 6. COST ──────────────────────────────────────────────────────────
    usage = client.get_usage()
    # Estimate cost: attribute all tokens to the most-used model (Sonnet)
    # for a reasonable upper-bound. Exact per-call tracking is in client logs.
    cost_usd = 0.0
    for model, prices in PRICING_PER_MILLION.items():
        # Simple heuristic: planning tokens are cheap, rest is Sonnet.
        pass
    # Use aggregate: assume mix is ~80% Sonnet, ~20% Haiku.
    cost_usd = (
        calculate_cost(
            "claude-sonnet-4-20250514",
            int(usage["input_tokens"] * 0.8),
            int(usage["output_tokens"] * 0.8),
        )
        + calculate_cost(
            "claude-haiku-4-5-20251001",
            int(usage["input_tokens"] * 0.2),
            int(usage["output_tokens"] * 0.2),
        )
    )

    # ── 7. COMPLETE ──────────────────────────────────────────────────────
    sources_json = [
        {"url": s.url, "title": s.title, "relevance_score": s.relevance_score}
        for s in all_sources
    ]

    yield ResearchEvent(
        stage="complete",
        data={
            "document": verification.verified_document,
            "sources": sources_json,
            "cost_usd": round(cost_usd, 4),
            "research_id": research_id,
        },
    )

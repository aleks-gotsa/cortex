"""Pydantic models for the entire Cortex pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class Depth(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class Verdict(str, Enum):
    confirmed = "confirmed"
    weakened = "weakened"
    unsupported = "unsupported"


class GapRecommendation(str, Enum):
    proceed = "proceed"
    gather_more = "gather_more"


# ── Request / Response ───────────────────────────────────────────────────────


class ResearchRequest(BaseModel):
    query: str
    depth: Depth = Depth.standard
    use_memory: bool = True
    # BYOK — override env vars when provided
    anthropic_api_key: str | None = None
    serper_api_key: str | None = None
    tavily_api_key: str | None = None


# ── Planner ──────────────────────────────────────────────────────────────────


class SubQuestion(BaseModel):
    id: str
    question: str
    search_terms: list[str]


class ResearchPlan(BaseModel):
    sub_questions: list[SubQuestion]
    strategy_notes: str


# ── Search / Gatherer ────────────────────────────────────────────────────────


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    search_engine: str  # "serper" | "tavily"


class Source(BaseModel):
    url: str
    title: str
    snippet: str
    full_content: str | None = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    sub_question_id: str
    search_engine: str  # "serper" | "tavily" | "qdrant"


# ── Gap Detector ─────────────────────────────────────────────────────────────


class CoverageScore(BaseModel):
    sub_question_id: str
    score: float = Field(ge=0.0, le=1.0)
    assessment: str
    follow_up_queries: list[str] | None = None


class GapReport(BaseModel):
    coverage: list[CoverageScore]
    overall_coverage: float = Field(ge=0.0, le=1.0)
    recommendation: GapRecommendation


# ── Verifier ─────────────────────────────────────────────────────────────────


class VerificationDetail(BaseModel):
    claim: str
    source_id: int
    verdict: Verdict
    reason: str
    correction: str | None = None


class VerificationSummary(BaseModel):
    confirmed: int
    weakened: int
    removed: int
    details: list[VerificationDetail]


class VerificationResult(BaseModel):
    verified_document: str
    summary: VerificationSummary


# ── SSE Events / Final Output ────────────────────────────────────────────────


class ResearchEvent(BaseModel):
    stage: str
    data: dict[str, Any]


class ResearchResult(BaseModel):
    research_id: str
    document: str
    sources: list[Source]
    verification: VerificationResult
    cost_usd: float

"""Layer 1 test: config + models"""
import sys
sys.path.insert(0, '.')

# Test 1: Config loads without crash
from backend.config import settings
assert hasattr(settings, 'ANTHROPIC_API_KEY'), "Missing ANTHROPIC_API_KEY"
assert hasattr(settings, 'SERPER_API_KEY'), "Missing SERPER_API_KEY"
assert hasattr(settings, 'BRAVE_API_KEY'), "Missing BRAVE_API_KEY"
assert hasattr(settings, 'QDRANT_URL'), "Missing QDRANT_URL"
print("✓ Config loads correctly")

# Test 2: All models importable
from backend.models import (
    ResearchRequest, ResearchPlan, SubQuestion, SearchResult,
    Source, CoverageScore, GapReport, VerificationDetail,
    VerificationResult, ResearchEvent, ResearchResult
)
print("✓ All models import correctly")

# Test 3: Models validate correctly
req = ResearchRequest(query="test query", depth="standard", use_memory=True)
assert req.depth == "standard"
print("✓ ResearchRequest validates")

sq = SubQuestion(id="q1", question="What is X?", search_terms=["X", "define X"])
assert len(sq.search_terms) == 2
print("✓ SubQuestion validates")

plan = ResearchPlan(sub_questions=[sq], strategy_notes="test")
assert len(plan.sub_questions) == 1
print("✓ ResearchPlan validates")

sr = SearchResult(url="https://example.com", title="Test", snippet="test snippet", search_engine="serper")
assert sr.search_engine == "serper"
print("✓ SearchResult validates")

source = Source(url="https://example.com", title="Test", snippet="snip", full_content="full", relevance_score=0.85, sub_question_id="q1", search_engine="serper")
assert source.relevance_score == 0.85
print("✓ Source validates")

# Test 4: Invalid depth rejected
try:
    bad = ResearchRequest(query="test", depth="invalid", use_memory=True)
    print("✗ Should have rejected invalid depth")
except Exception:
    print("✓ Invalid depth rejected correctly")

print("\n=== LAYER 1: ALL TESTS PASSED ===")

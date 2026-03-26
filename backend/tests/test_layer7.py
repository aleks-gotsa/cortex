"""Layer 7 test: gap detector"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather
from backend.pipeline.gap_detector import detect_gaps

async def test_gap_detector():
    # Setup: get real plan and sources
    research_plan = await plan("What is RLHF, how does it compare to DPO, and what are the latest alternatives?")
    sources = await gather(research_plan.sub_questions, pass_number=1)
    print(f"Setup: {len(research_plan.sub_questions)} sub-questions, {len(sources)} sources")

    # Test 1: Full coverage detection
    gap_report = await detect_gaps(research_plan.sub_questions, sources)
    assert gap_report.coverage is not None, "Missing coverage"
    assert len(gap_report.coverage) == len(research_plan.sub_questions), "Coverage count mismatch"
    print(f"✓ Coverage scores for all {len(gap_report.coverage)} sub-questions:")
    for c in gap_report.coverage:
        has_gaps = " ← GAP" if c.score < 0.6 else ""
        print(f"  [{c.sub_question_id}] {c.score:.2f} — {c.assessment[:60]}{has_gaps}")

    # Test 2: Overall coverage is reasonable
    assert 0.0 <= gap_report.overall_coverage <= 1.0, "Invalid overall coverage"
    print(f"✓ Overall coverage: {gap_report.overall_coverage:.2f}")

    # Test 3: Recommendation is valid
    assert gap_report.recommendation in ("proceed", "gather_more"), f"Invalid recommendation: {gap_report.recommendation}"
    print(f"✓ Recommendation: {gap_report.recommendation}")

    # Test 4: Simulate gap by removing sources for one sub-question
    target_sq = research_plan.sub_questions[0].id
    filtered_sources = [s for s in sources if s.sub_question_id != target_sq]
    print(f"\nSimulated gap: removed all sources for {target_sq}")

    gap_report_with_hole = await detect_gaps(research_plan.sub_questions, filtered_sources)
    target_coverage = next(c for c in gap_report_with_hole.coverage if c.sub_question_id == target_sq)
    assert target_coverage.score < 0.6, f"Gap not detected: score={target_coverage.score}"
    assert target_coverage.follow_up_queries and len(target_coverage.follow_up_queries) > 0, "No follow-up queries for gap"
    print(f"✓ Gap detected for {target_sq}: score={target_coverage.score:.2f}")
    print(f"  Follow-up queries: {target_coverage.follow_up_queries}")

    # Test 5: Recommendation should be "gather_more" with gap
    assert gap_report_with_hole.recommendation == "gather_more", "Should recommend gathering more"
    print(f"✓ Correctly recommends: {gap_report_with_hole.recommendation}")

asyncio.run(test_gap_detector())
print("\n=== LAYER 7: ALL TESTS PASSED ===")

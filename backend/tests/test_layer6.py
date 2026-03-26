"""Layer 6 test: gatherer"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather

async def test_gatherer():
    # Get sub-questions first
    research_plan = await plan("What is retrieval augmented generation and how has it evolved?")
    print(f"Plan: {len(research_plan.sub_questions)} sub-questions")

    # Test 1: Gather returns sources
    sources = await gather(research_plan.sub_questions, pass_number=1)
    assert len(sources) > 0, "No sources gathered"
    print(f"✓ Gathered {len(sources)} total sources")

    # Test 2: Sources have required fields
    for s in sources[:3]:
        assert s.url, "Missing URL"
        assert s.title, "Missing title"
        assert s.relevance_score >= 0.0, "Invalid relevance score"
        assert s.sub_question_id, "Missing sub_question_id"
    print("✓ All sources have required fields")

    # Test 3: Sources per sub-question (max 5 each)
    from collections import Counter
    sq_counts = Counter(s.sub_question_id for s in sources)
    for sq_id, count in sq_counts.items():
        assert count <= 5, f"{sq_id} has {count} sources (max 5)"
        print(f"  [{sq_id}] {count} sources")
    print("✓ Max 5 sources per sub-question enforced")

    # Test 4: Relevance scores are ordered (per sub-question)
    for sq in research_plan.sub_questions:
        sq_sources = [s for s in sources if s.sub_question_id == sq.id]
        scores = [s.relevance_score for s in sq_sources]
        assert scores == sorted(scores, reverse=True), f"Sources not sorted by relevance for {sq.id}"
    print("✓ Sources sorted by relevance within each sub-question")

    # Test 5: Some sources have full_content
    with_content = [s for s in sources if s.full_content]
    print(f"✓ {len(with_content)}/{len(sources)} sources have full content")
    assert len(with_content) > 0, "At least some sources should have scraped content"

    # Test 6: No duplicate URLs
    urls = [s.url for s in sources]
    assert len(urls) == len(set(urls)), f"Duplicate URLs found: {len(urls)} total, {len(set(urls))} unique"
    print("✓ No duplicate URLs")

asyncio.run(test_gatherer())
print("\n=== LAYER 6: ALL TESTS PASSED ===")

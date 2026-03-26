"""Layer 5 test: planner"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.pipeline.planner import plan

async def test_planner():
    # Test 1: Basic decomposition
    query = "How does transformer attention work and what are the latest improvements?"
    result = await plan(query)
    assert len(result.sub_questions) >= 3, f"Expected 3+ sub-questions, got {len(result.sub_questions)}"
    assert len(result.sub_questions) <= 6, f"Expected max 6 sub-questions, got {len(result.sub_questions)}"
    print(f"✓ Decomposed into {len(result.sub_questions)} sub-questions:")
    for sq in result.sub_questions:
        assert len(sq.search_terms) >= 1, f"Sub-question {sq.id} has no search terms"
        print(f"  [{sq.id}] {sq.question}")
        print(f"       Search terms: {sq.search_terms}")

    # Test 2: Each sub-question has required fields
    for sq in result.sub_questions:
        assert sq.id, "Missing id"
        assert sq.question, "Missing question"
        assert len(sq.search_terms) > 0, "Missing search terms"
    print("✓ All sub-questions have id, question, and search_terms")

    # Test 3: Strategy notes present
    assert result.strategy_notes is not None, "Missing strategy_notes"
    print(f"✓ Strategy notes: {result.strategy_notes[:100]}...")

    # Test 4: With prior context
    prior = ["RAG combines retrieval with generation. It was introduced in 2020 by Lewis et al."]
    result_with_context = await plan("What are alternatives to RAG?", prior_context=prior)
    assert len(result_with_context.sub_questions) >= 3, "Should still produce sub-questions with context"
    print(f"✓ With prior context: {len(result_with_context.sub_questions)} sub-questions")

    # Test 5: Short query
    short_result = await plan("What is RLHF?")
    assert len(short_result.sub_questions) >= 3, "Even short queries need decomposition"
    print(f"✓ Short query decomposed into {len(short_result.sub_questions)} sub-questions")

asyncio.run(test_planner())
print("\n=== LAYER 5: ALL TESTS PASSED ===")

"""Layer 9 test: verifier"""
import asyncio
import re
import sys
sys.path.insert(0, '.')

from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather
from backend.pipeline.synthesizer import synthesize
from backend.pipeline.verifier import verify

async def test_verifier():
    # Setup: full pipeline to get document + sources
    query = "What is retrieval augmented generation?"
    research_plan = await plan(query)
    sources = await gather(research_plan.sub_questions)
    document = await synthesize(query, research_plan.sub_questions, sources)
    print(f"Setup: document={len(document)} chars, {len(sources)} sources")

    # Test 1: Verifier returns result
    result = await verify(document, sources)
    assert result.verified_document, "Missing verified document"
    assert result.summary, "Missing summary"
    print(f"✓ Verification complete")

    # Test 2: Summary has counts
    assert result.summary.confirmed >= 0, "Invalid confirmed count"
    assert result.summary.weakened >= 0, "Invalid weakened count"
    assert result.summary.removed >= 0, "Invalid removed count"
    total = result.summary.confirmed + result.summary.weakened + result.summary.removed
    print(f"✓ Results: {result.summary.confirmed} confirmed, {result.summary.weakened} weakened, {result.summary.removed} removed (total: {total})")

    # Test 3: Verified document still has citations
    citations = re.findall(r'\[(\d+)\]', result.verified_document)
    assert len(citations) > 0, "Verified document lost all citations"
    print(f"✓ Verified document retains {len(citations)} citations")

    # Test 4: Verified document still has Sources section
    assert "source" in result.verified_document.lower(), "Verified document lost Sources section"
    print("✓ Verified document retains Sources section")

    # Test 5: Document wasn't expanded (verifier shouldn't add claims)
    original_citations = len(re.findall(r'\[(\d+)\]', document))
    verified_citations = len(citations)
    assert verified_citations <= original_citations + 2, "Verifier added too many new citations — it should only verify, not expand"
    print(f"✓ Citation count stable: {original_citations} ��� {verified_citations}")

    # Test 6: Details list
    if result.summary.details:
        print(f"✓ Verification details ({len(result.summary.details)} items):")
        for d in result.summary.details[:3]:
            print(f"  - [{d.verdict.upper()}] {d.claim[:60]}...")
    else:
        print("✓ No detailed issues flagged (all confirmed)")

asyncio.run(test_verifier())
print("\n=== LAYER 9: ALL TESTS PASSED ===")

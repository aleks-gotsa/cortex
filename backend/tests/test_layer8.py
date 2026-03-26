"""Layer 8 test: synthesizer"""
import asyncio
import re
import sys
sys.path.insert(0, '.')

from backend.pipeline.planner import plan
from backend.pipeline.gatherer import gather
from backend.pipeline.synthesizer import synthesize

async def test_synthesizer():
    # Setup
    query = "What is retrieval augmented generation?"
    research_plan = await plan(query)
    sources = await gather(research_plan.sub_questions)
    print(f"Setup: {len(sources)} sources gathered")

    # Test 1: Synthesize produces output
    document = await synthesize(query, research_plan.sub_questions, sources)
    assert isinstance(document, str), "Document should be a string"
    assert len(document) > 500, f"Document too short: {len(document)} chars"
    print(f"✓ Document generated: {len(document)} chars")

    # Test 2: Has executive summary
    assert "executive summary" in document.lower() or "## executive" in document.lower(), "Missing Executive Summary"
    print("✓ Has Executive Summary section")

    # Test 3: Has inline citations
    citations = re.findall(r'\[(\d+)\]', document)
    assert len(citations) > 0, "No inline citations found"
    unique_citations = set(citations)
    print(f"✓ Found {len(citations)} inline citations ({len(unique_citations)} unique)")

    # Test 4: Has Sources section
    assert "## sources" in document.lower() or "## source" in document.lower(), "Missing Sources section"
    print("✓ Has Sources section")

    # Test 5: Citations reference actual sources
    source_section = document.lower().split("## source")[1] if "## source" in document.lower() else ""
    for cite_num in unique_citations:
        assert cite_num in source_section or f"[{cite_num}]" in source_section or f"{cite_num}." in source_section, f"Citation [{cite_num}] not found in Sources"
    print("✓ All citations have corresponding sources")

    # Test 6: Has multiple sections (not just one blob)
    heading_count = len(re.findall(r'^##\s', document, re.MULTILINE))
    assert heading_count >= 3, f"Only {heading_count} sections — expected at least 3"
    print(f"✓ Document has {heading_count} sections")

    # Print preview
    print(f"\n--- Document preview (first 400 chars) ---")
    print(document[:400])

asyncio.run(test_synthesizer())
print("\n=== LAYER 8: ALL TESTS PASSED ===")

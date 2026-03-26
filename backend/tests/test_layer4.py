"""Layer 4 test: scraper"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.search.scraper import scrape, scrape_many

TEST_URLS = [
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    "https://docs.anthropic.com/en/docs/about-claude/models",
    "https://python.langchain.com/docs/concepts/rag/",
]

async def test_scraper():
    # Test 1: Single page scrape
    content = await scrape(TEST_URLS[0])
    assert content is not None, f"Failed to scrape {TEST_URLS[0]}"
    assert len(content) > 100, "Content too short"
    assert len(content) <= 4000, f"Content not truncated: {len(content)} chars"
    print(f"✓ Single scrape: {len(content)} chars from Wikipedia")
    print(f"  Preview: {content[:150]}...")

    # Test 2: Parallel scrape
    results = await scrape_many(TEST_URLS, max_concurrent=3)
    assert isinstance(results, dict), "scrape_many should return dict"
    assert len(results) == len(TEST_URLS), "Should have entry for each URL"
    success_count = sum(1 for v in results.values() if v is not None)
    print(f"✓ Parallel scrape: {success_count}/{len(TEST_URLS)} succeeded")
    for url, content in results.items():
        status = f"{len(content)} chars" if content else "FAILED"
        print(f"  - {url[:50]}... → {status}")

    # Test 3: Invalid URL doesn't crash
    bad_content = await scrape("https://thisdomaindoesnotexist12345.com/page")
    assert bad_content is None, "Invalid URL should return None"
    print("✓ Invalid URL returns None (no crash)")

    # Test 4: PDF URL skipped
    pdf_content = await scrape("https://example.com/document.pdf")
    assert pdf_content is None, "PDF should be skipped"
    print("✓ PDF URL correctly skipped")

    # Test 5: Truncation works
    long_content = await scrape("https://en.wikipedia.org/wiki/Artificial_intelligence")
    if long_content:
        assert len(long_content) <= 4000, f"Not truncated: {len(long_content)}"
        print(f"✓ Long page truncated to {len(long_content)} chars")

asyncio.run(test_scraper())
print("\n=== LAYER 4: ALL TESTS PASSED ===")

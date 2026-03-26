"""Layer 3 test: Serper + Brave search clients."""
import asyncio
import logging
import sys

sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO)

from backend.search import serper, brave

QUERY = "latest AI research 2026"


async def test_search() -> None:
    # Test 1: Serper
    serper_results = await serper.search(QUERY, num_results=5)
    print(f"\n--- Serper: {len(serper_results)} results ---")
    for r in serper_results[:3]:
        print(f"  {r.title}")
        assert r.search_engine == "serper"
        assert r.url.startswith("http")
    if serper_results:
        print("✓ Serper returned results")
    else:
        print("⚠ Serper returned 0 results (check SERPER_API_KEY)")

    # Test 2: Brave
    brave_results = await brave.search(QUERY, num_results=5)
    print(f"\n--- Brave: {len(brave_results)} results ---")
    for r in brave_results[:3]:
        print(f"  {r.title}")
        assert r.search_engine == "brave"
        assert r.url.startswith("http")
    if brave_results:
        print("✓ Brave returned results")
    else:
        print("⚠ Brave returned 0 results (check BRAVE_API_KEY)")

    # At least one engine must work
    total = len(serper_results) + len(brave_results)
    assert total > 0, "Both search engines returned 0 results"
    print(f"\n✓ Total results: {total}")


asyncio.run(test_search())
print("\n=== LAYER 3: ALL TESTS PASSED ===")

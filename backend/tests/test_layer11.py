"""Layer 11 test: SQLite persistence"""
import asyncio
import json
import sys
sys.path.insert(0, '.')

import httpx

BACKEND_URL = "http://localhost:8000"

async def test_persistence():
    # Run a research first (if not already done in layer 10)
    research_id = None
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST", f"{BACKEND_URL}/research",
            json={"query": "What is gradient descent?", "depth": "quick", "use_memory": False}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line.replace("data:", "").strip())
                    if "research_id" in data:
                        research_id = data["research_id"]

    assert research_id, "No research_id from pipeline"
    print(f"✓ Research completed: {research_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: History endpoint
        history = await client.get(f"{BACKEND_URL}/research/history")
        assert history.status_code == 200
        runs = history.json()
        assert len(runs) > 0, "History is empty"
        print(f"✓ History: {len(runs)} research runs")

        # Test 2: Specific run
        run = await client.get(f"{BACKEND_URL}/research/{research_id}")
        assert run.status_code == 200
        run_data = run.json()
        result = run_data.get("result", {})
        assert result and result.get("document_md"), "Missing document in stored result"
        print(f"✓ Retrieved run {research_id} with document ({len(result['document_md'])} chars)")

        # Test 3: History has required fields
        latest = runs[0]
        assert "query" in latest, "Missing query in history"
        assert "created_at" in latest or "date" in latest, "Missing date in history"
        print(f"✓ History entry has query and date")

asyncio.run(test_persistence())
print("\n=== LAYER 11: ALL TESTS PASSED ===")

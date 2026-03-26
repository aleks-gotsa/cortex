"""Layer 10 test: full pipeline E2E via SSE"""
import asyncio
import json
import sys
sys.path.insert(0, '.')

import httpx

BACKEND_URL = "http://localhost:8000"

async def test_e2e():
    stages_received = []
    final_data = None

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{BACKEND_URL}/research",
            json={"query": "What is prompt engineering?", "depth": "quick", "use_memory": False}
        ) as response:
            assert response.status_code == 200, f"Bad status: {response.status_code}"

            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                elif line.startswith("data:"):
                    data = json.loads(line.replace("data:", "").strip())
                    stages_received.append(current_event)
                    print(f"  ← {current_event}: {str(data)[:100]}")
                    if current_event == "complete":
                        final_data = data

    # Test 1: All expected stages received
    assert "planning" in stages_received, "Missing planning stage"
    assert "gathering" in stages_received, "Missing gathering stage"
    assert "synthesizing" in stages_received, "Missing synthesizing stage"
    assert "verifying" in stages_received, "Missing verifying stage"
    assert "complete" in stages_received, "Missing complete stage"
    print(f"\n✓ All stages received: {stages_received}")

    # Test 2: Final data has document
    assert final_data, "No complete event data"
    assert final_data.get("document"), "Missing document in complete event"
    assert len(final_data["document"]) > 200, "Document too short"
    print(f"✓ Final document: {len(final_data['document'])} chars")

    # Test 3: Final data has research_id
    assert final_data.get("research_id"), "Missing research_id"
    print(f"✓ Research ID: {final_data['research_id']}")

    # Test 4: Cost is tracked
    assert "cost_usd" in final_data, "Missing cost_usd"
    print(f"✓ Cost: ${final_data['cost_usd']:.4f}")

asyncio.run(test_e2e())
print("\n=== LAYER 10: ALL TESTS PASSED ===")

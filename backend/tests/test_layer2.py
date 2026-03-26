"""Layer 2 test: LLM client + router"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.llm.client import LLMClient
from backend.llm.router import get_model, calculate_cost, TASK_MODEL, PRICING_PER_MILLION

# Test 1: Router returns correct models
assert get_model("planning") == "claude-haiku-4-5-20251001", "Wrong model for planning"
assert get_model("synthesis") == "claude-sonnet-4-20250514", "Wrong model for synthesis"
assert get_model("verification") == "claude-sonnet-4-20250514", "Wrong model for verification"
assert get_model("gap_detection") == "claude-sonnet-4-20250514", "Wrong model for gap_detection"
print("✓ Router returns correct models for all task types")

# Test 2: Cost calculation
cost = calculate_cost("claude-haiku-4-5-20251001", input_tokens=1000, output_tokens=500)
assert cost > 0, "Cost should be positive"
assert cost < 0.01, "Haiku cost for 1.5K tokens should be under $0.01"
print(f"✓ Cost calculation works: 1K in + 500 out on Haiku = ${cost:.6f}")

# Test 3: LLM client calls Haiku successfully
async def test_llm_call():
    client = LLMClient()
    try:
        result = await client.call(
            system="You are a test assistant. Respond ONLY with valid JSON, no markdown.",
            user_message='Return this exact JSON: {"status": "ok", "message": "hello from haiku"}',
            model=get_model("planning"),
            max_tokens=100
        )
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "status" in result, f"Missing 'status' key in response: {result}"
        print(f"✓ Haiku responds with valid JSON: {result}")
    finally:
        await client.close()

    # Test 4: Token tracking
    usage = client.get_usage()
    assert usage["input_tokens"] > 0, "Input tokens should be tracked"
    assert usage["output_tokens"] > 0, "Output tokens should be tracked"
    assert usage["calls"] == 1, "Should have 1 call"
    print(f"✓ Token tracking works: {usage}")

    # Test 5: Usage reset
    client.reset_usage()
    usage = client.get_usage()
    assert usage["calls"] == 0, "Calls should reset to 0"
    print("✓ Usage reset works")

asyncio.run(test_llm_call())
print("\n=== LAYER 2: ALL TESTS PASSED ===")

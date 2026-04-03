"""Model routing and cost calculation."""

TASK_MODEL: dict[str, str] = {
    "planning": "claude-haiku-4-5-20251001",
    "gap_detection": "claude-sonnet-4-20250514",
    "synthesis": "claude-sonnet-4-20250514",
    "verification": "claude-sonnet-4-20250514",
}

PRICING_PER_MILLION: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
}


def get_model(task_type: str) -> str:
    """Return the model string for a given pipeline task type."""
    return TASK_MODEL[task_type]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for the given token counts."""
    prices = PRICING_PER_MILLION[model]
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


# Worker type mapping for Dynamo disaggregated inference
# prefill = compute-heavy prompt processing, short output
# decode  = long token generation
TASK_WORKER_TYPE: dict[str, str] = {
    "planning": "prefill",       # Haiku: short JSON output
    "gap_detection": "prefill",  # Sonnet: reads sources, short JSON
    "synthesis": "decode",       # Sonnet: generates long document
    "verification": "decode",    # Sonnet: generates corrected document
}


def get_worker_type(task_type: str) -> str:
    """Return 'prefill' or 'decode' for the given pipeline task."""
    return TASK_WORKER_TYPE.get(task_type, "decode")

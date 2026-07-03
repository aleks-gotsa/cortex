"""Model routing and cost calculation."""

import logging

from backend.config import settings

logger = logging.getLogger(__name__)

TASK_MODEL: dict[str, str] = {
    "planning": "claude-haiku-4-5-20251001",
    "gap_detection": "claude-sonnet-4-20250514",
    "synthesis": "claude-sonnet-4-20250514",
    "verification": "claude-sonnet-4-20250514",
}

PRICING_PER_MILLION: dict[str, dict[str, float]] = {
    # Anthropic models
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    # Dynamo self-hosted (estimated based on Lambda Labs A10G @ $0.75/hr)
    "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.05, "output": 0.10},
    "meta-llama/Llama-3.1-70B-Instruct": {"input": 0.40, "output": 0.80},
    # local inference — no marginal cost
    "llama3.2:3b": {"input": 0.0, "output": 0.0},
    "llama3.1:8b": {"input": 0.0, "output": 0.0},
    "qwen3:8b": {"input": 0.0, "output": 0.0},
    "qwen2.5:7b-instruct": {"input": 0.0, "output": 0.0},
}


def local_task_model() -> dict[str, str]:
    """Task→model map for the local backend, read from settings."""
    return {
        "planning": settings.LOCAL_MODEL_PLANNING,
        "gap_detection": settings.LOCAL_MODEL_GAP_DETECTION,
        "synthesis": settings.LOCAL_MODEL_SYNTHESIS,
        "verification": settings.LOCAL_MODEL_VERIFICATION,
    }


def get_model(task_type: str) -> str:
    """Return the model string for a given pipeline task type."""
    if settings.LLM_BACKEND == "local":
        return local_task_model()[task_type]
    return TASK_MODEL[task_type]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for the given token counts."""
    prices = PRICING_PER_MILLION.get(model)
    if prices is None:
        logger.warning("Unknown model for cost calculation: %s", model)
        return 0.0
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

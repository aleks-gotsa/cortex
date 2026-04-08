"""Worker type routing for Dynamo disaggregated inference."""

import logging

logger = logging.getLogger(__name__)

PREFILL_TASKS = frozenset({"planning", "gap_detection"})
DECODE_TASKS = frozenset({"synthesis", "verification"})


def get_dynamo_endpoint(task_type: str, settings) -> str:
    """Route task to the appropriate Dynamo worker endpoint."""
    if task_type in PREFILL_TASKS:
        return settings.DYNAMO_PREFILL_URL
    return settings.DYNAMO_DECODE_URL


def get_dynamo_model(task_type: str, settings) -> str:
    """Return the model name for the appropriate worker tier."""
    if task_type in PREFILL_TASKS:
        return settings.DYNAMO_PREFILL_MODEL
    return settings.DYNAMO_DECODE_MODEL


# ── Model-based routing (reverse mapping) ───────────────────────────────


def _build_prefill_models() -> frozenset[str]:
    """Build set of Anthropic model strings that correspond to prefill tasks.

    Only includes a model if ALL tasks using that model are prefill tasks.
    Models shared between prefill and decode default to decode (safe fallback).
    """
    try:
        from backend.llm.router import TASK_MODEL, TASK_WORKER_TYPE
        model_workers: dict[str, set[str]] = {}
        for task, worker in TASK_WORKER_TYPE.items():
            model = TASK_MODEL.get(task)
            if model:
                model_workers.setdefault(model, set()).add(worker)
        return frozenset(
            model for model, workers in model_workers.items()
            if workers == {"prefill"}
        )
    except ImportError:
        return frozenset()


_PREFILL_MODELS = _build_prefill_models()


def infer_worker_type(model: str) -> str:
    """Infer 'prefill' or 'decode' from the Anthropic model string.

    Falls back to 'decode' for unknown models (safe default — decode
    workers handle longer generation).
    """
    if model in _PREFILL_MODELS:
        return "prefill"
    # Also check by substring for flexibility
    if "haiku" in model.lower():
        return "prefill"
    return "decode"


def get_dynamo_endpoint_for_model(model: str, settings) -> str:
    """Route to the correct Dynamo endpoint based on Anthropic model string."""
    worker = infer_worker_type(model)
    if worker == "prefill":
        return settings.DYNAMO_PREFILL_URL
    return settings.DYNAMO_DECODE_URL


def get_dynamo_model_for_model(model: str, settings) -> str:
    """Return the Dynamo model name based on Anthropic model string."""
    worker = infer_worker_type(model)
    if worker == "prefill":
        return settings.DYNAMO_PREFILL_MODEL
    return settings.DYNAMO_DECODE_MODEL

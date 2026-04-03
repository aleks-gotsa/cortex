"""Worker type routing for Dynamo disaggregated inference."""

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

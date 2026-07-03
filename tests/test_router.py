"""router — cost math, unknown-model behavior, pricing invariants, backend dispatch."""

import logging

from backend.config import settings
from backend.llm.router import (
    PRICING_PER_MILLION,
    TASK_MODEL,
    calculate_cost,
    get_model,
    local_task_model,
)


def test_known_model_cost_math():
    cost = calculate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
    assert cost == 0.80 + 4.00
    assert calculate_cost("claude-sonnet-4-20250514", 500_000, 0) == 1.50


def test_unknown_model_returns_zero_with_warning(caplog):
    with caplog.at_level(logging.WARNING):
        assert calculate_cost("not-a-model", 1000, 1000) == 0.0
    assert "Unknown model" in caplog.text


def test_task_models_all_priced():
    for task, model in TASK_MODEL.items():
        assert model in PRICING_PER_MILLION, f"{task} model {model} missing from pricing"


def test_local_task_models_all_priced():
    for task, model in local_task_model().items():
        assert model in PRICING_PER_MILLION, f"local {task} model {model} missing from pricing"


def test_local_models_priced_at_zero():
    for model in set(local_task_model().values()):
        assert calculate_cost(model, 1_000_000, 1_000_000) == 0.0


def test_get_model_dispatches_on_backend(monkeypatch):
    monkeypatch.setattr(settings, "LLM_BACKEND", "anthropic")
    assert get_model("planning") == TASK_MODEL["planning"]
    monkeypatch.setattr(settings, "LLM_BACKEND", "local")
    assert get_model("planning") == settings.LOCAL_MODEL_PLANNING
    assert get_model("synthesis") == settings.LOCAL_MODEL_SYNTHESIS

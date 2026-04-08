"""Mock Dynamo client for local development and architecture testing."""

import asyncio
import logging
import time
from collections import defaultdict

from backend.llm.anthropic_client import AnthropicLLMClient
from backend.llm.base import LLMClientBase
from dynamo.config import dynamo_settings
from dynamo.worker_types import (
    infer_worker_type,
    get_dynamo_endpoint_for_model,
    get_dynamo_model_for_model,
)

logger = logging.getLogger(__name__)

ROUTING_OVERHEAD_S = 0.05  # 50ms simulated routing latency


class MockDynamoClient(LLMClientBase):
    """
    Mock Dynamo client for local development and architecture testing.

    Routes calls to the correct worker type (prefill/decode) based on
    the model parameter and logs what the real Dynamo client would do,
    but delegates actual inference to AnthropicLLMClient underneath.

    Replace AnthropicLLMClient calls with real Dynamo HTTP calls
    in dynamo/real_client.py when running on actual GPU hardware.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._delegate = AnthropicLLMClient(api_key=api_key)
        self._worker_usage: dict[str, dict[str, int]] = defaultdict(
            lambda: {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        )
        self._routing_overhead_total = 0.0

    def _log_routing(self, model: str) -> str:
        """Determine worker type from model string and log routing decision."""
        worker = infer_worker_type(model)
        endpoint = get_dynamo_endpoint_for_model(model, dynamo_settings)
        dynamo_model = get_dynamo_model_for_model(model, dynamo_settings)
        logger.info(
            "[MockDynamo] model=%s → worker=%s endpoint=%s dynamo_model=%s",
            model, worker, endpoint, dynamo_model,
        )
        return worker

    async def call(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> dict:
        worker = self._log_routing(model)
        t0 = time.monotonic()
        await asyncio.sleep(ROUTING_OVERHEAD_S)
        result = await self._delegate.call(system, user_message, model, max_tokens)
        self._routing_overhead_total += (time.monotonic() - t0 - ROUTING_OVERHEAD_S)
        self._worker_usage[worker]["calls"] += 1
        return result

    async def call_text(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> str:
        worker = self._log_routing(model)
        await asyncio.sleep(ROUTING_OVERHEAD_S)
        result = await self._delegate.call_text(system, user_message, model, max_tokens)
        self._worker_usage[worker]["calls"] += 1
        return result

    def get_usage(self) -> dict[str, int]:
        return self._delegate.get_usage()

    def get_usage_by_model(self) -> dict[str, dict[str, int]]:
        usage = self._delegate.get_usage_by_model()
        usage["_dynamo_worker_calls"] = dict(self._worker_usage)
        return usage

    def reset_usage(self) -> None:
        self._delegate.reset_usage()
        self._worker_usage.clear()
        self._routing_overhead_total = 0.0

    async def close(self) -> None:
        await self._delegate.close()

    def get_worker_usage(self) -> dict:
        return {
            "worker_calls": dict(self._worker_usage),
            "routing_overhead_s": round(self._routing_overhead_total, 4),
        }

"""Real Dynamo client — calls Dynamo workers via OpenAI-compatible API."""

import json
import logging
import re
from collections import defaultdict

import httpx

from backend.llm.base import LLMClientBase
from dynamo.config import dynamo_settings
from dynamo.worker_types import (
    get_dynamo_endpoint_for_model,
    get_dynamo_model_for_model,
)

logger = logging.getLogger(__name__)


class DynamoLLMClient(LLMClientBase):
    """
    Real Dynamo client. Calls Dynamo workers via OpenAI-compatible API.
    Prefill worker handles planning + gap_detection (Llama 8B).
    Decode worker handles synthesis + verification (Llama 70B).
    Routes based on the model parameter passed to call()/call_text().
    """

    def __init__(self) -> None:
        self._input_tokens = 0
        self._output_tokens = 0
        self._calls = 0
        self._per_model: dict[str, dict[str, int]] = defaultdict(
            lambda: {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        )

    def _get_endpoint_and_model(self, model: str) -> tuple[str, str]:
        return (
            get_dynamo_endpoint_for_model(model, dynamo_settings),
            get_dynamo_model_for_model(model, dynamo_settings),
        )

    async def _post(self, endpoint: str, model: str, system: str, user_message: str, max_tokens: int) -> dict:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        }
        timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{endpoint}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def _track(self, model: str, data: dict) -> None:
        usage = data.get("usage", {})
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        self._input_tokens += inp
        self._output_tokens += out
        self._calls += 1
        m = self._per_model[model]
        m["input_tokens"] += inp
        m["output_tokens"] += out
        m["calls"] += 1

    @staticmethod
    def _parse_json(text: str) -> dict:
        stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
        stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
        if stripped:
            return json.loads(stripped)
        raise ValueError("Empty response text")

    async def call(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> dict:
        endpoint, dynamo_model = self._get_endpoint_and_model(model)
        data = await self._post(endpoint, dynamo_model, system, user_message, max_tokens)
        self._track(dynamo_model, data)
        text = data["choices"][0]["message"]["content"]
        try:
            return self._parse_json(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("JSON parse failed, retrying with JSON instruction")
            retry_system = system + "\n\nRespond ONLY with valid JSON, no markdown fences."
            data = await self._post(endpoint, dynamo_model, retry_system, user_message, max_tokens)
            self._track(dynamo_model, data)
            return self._parse_json(data["choices"][0]["message"]["content"])

    async def call_text(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> str:
        endpoint, dynamo_model = self._get_endpoint_and_model(model)
        data = await self._post(endpoint, dynamo_model, system, user_message, max_tokens)
        self._track(dynamo_model, data)
        return data["choices"][0]["message"]["content"]

    def get_usage(self) -> dict[str, int]:
        return {"input_tokens": self._input_tokens, "output_tokens": self._output_tokens, "calls": self._calls}

    def get_usage_by_model(self) -> dict[str, dict[str, int]]:
        return {k: v.copy() for k, v in self._per_model.items()}

    def reset_usage(self) -> None:
        self._input_tokens = 0
        self._output_tokens = 0
        self._calls = 0
        self._per_model.clear()

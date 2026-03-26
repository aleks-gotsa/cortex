"""Thin async wrapper around the Anthropic SDK with JSON parsing and token tracking."""

import json
import logging
import re

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Calls Claude models and tracks cumulative token usage."""

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._input_tokens = 0
        self._output_tokens = 0
        self._calls = 0
        self._per_model: dict[str, dict[str, int]] = {}

    # ── Public API ───────────────────────────────────────────────────────

    async def call(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a message to *model* and return the parsed JSON response.

        On JSON parse failure the request is retried **once** with an
        explicit JSON-only instruction appended to the system prompt.
        """
        response = await self._send(system, user_message, model, max_tokens)
        text = response.content[0].text
        self._track(model, response.usage)

        try:
            return self._parse_json(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "JSON parse failed for model=%s — retrying with JSON instruction",
                model,
            )

        retry_system = system + "\n\nRespond ONLY with valid JSON, no markdown fences."
        response = await self._send(retry_system, user_message, model, max_tokens)
        text = response.content[0].text
        self._track(model, response.usage)

        return self._parse_json(text)  # raises on second failure

    def get_usage(self) -> dict[str, int]:
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "calls": self._calls,
        }

    def get_usage_by_model(self) -> dict[str, dict[str, int]]:
        """Return per-model token usage. Returns a fresh dict (safe to diff)."""
        return {
            model: counters.copy()
            for model, counters in self._per_model.items()
        }

    def reset_usage(self) -> None:
        self._input_tokens = 0
        self._output_tokens = 0
        self._calls = 0
        self._per_model = {}

    async def call_text(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 4096,
    ) -> str:
        """Send a message and return the raw text response (no JSON parsing)."""
        response = await self._send(system, user_message, model, max_tokens)
        self._track(model, response.usage)
        return response.content[0].text

    async def close(self) -> None:
        await self._client.close()

    # ── Internals ────────────────────────────────────────────────────────

    async def _send(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int,
    ) -> anthropic.types.Message:
        return await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract and parse JSON from model output, stripping markdown fences."""
        # Strip ```json ... ``` or ``` ... ``` wrappers
        stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
        stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
        if stripped:
            return json.loads(stripped)
        raise ValueError("Empty response text")

    def _track(self, model: str, usage: anthropic.types.Usage) -> None:
        self._input_tokens += usage.input_tokens
        self._output_tokens += usage.output_tokens
        self._calls += 1

        if model not in self._per_model:
            self._per_model[model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self._per_model[model]["input_tokens"] += usage.input_tokens
        self._per_model[model]["output_tokens"] += usage.output_tokens
        self._per_model[model]["calls"] += 1

        logger.info(
            "LLM call: model=%s input_tokens=%d output_tokens=%d",
            model,
            usage.input_tokens,
            usage.output_tokens,
        )

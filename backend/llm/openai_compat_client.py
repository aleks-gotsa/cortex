"""Async client for OpenAI-compatible endpoints (Ollama, vLLM) with JSON parsing and token tracking."""

import json
import logging
import re

import httpx

from backend.config import settings
from backend.llm.base import LLMClientBase

logger = logging.getLogger(__name__)

# Local generation is slow — a full synthesis pass on laptop hardware can
# take minutes, so the read timeout is far above hosted-API norms.
_TIMEOUT = httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0)

# Reasoning models (e.g. qwen3) may emit chain-of-thought inline in the
# response body; strip it so callers only ever see the answer.
_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class OpenAICompatLLMClient(LLMClientBase):
    """Calls an OpenAI-compatible chat-completions endpoint and tracks cumulative token usage."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.LOCAL_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)
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

        JSON-expecting calls constrain decoding with
        ``response_format={"type": "json_object"}`` — small local models
        need the grammar constraint far more than hosted ones do. On JSON
        parse failure the request is retried **once** with an explicit
        JSON-only instruction appended to the system prompt.
        """
        text = await self._send(system, user_message, model, max_tokens, json_mode=True)

        try:
            return self._parse_json(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "JSON parse failed for model=%s — retrying with JSON instruction",
                model,
            )

        retry_system = system + "\n\nRespond ONLY with valid JSON, no markdown fences."
        text = await self._send(retry_system, user_message, model, max_tokens, json_mode=True)

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
        """Send a message and return the raw text response (no JSON constraint)."""
        return await self._send(system, user_message, model, max_tokens, json_mode=False)

    async def close(self) -> None:
        await self._client.aclose()

    # ── Internals ────────────────────────────────────────────────────────

    async def _send(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post(
                f"{self._base_url}/chat/completions", json=payload
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot reach LLM endpoint at {self._base_url} — is Ollama running? "
                "Start it with `ollama serve`."
            ) from exc

        data = response.json()
        text = data["choices"][0]["message"]["content"] or ""
        text = _THINK_BLOCK.sub("", text).strip()
        self._track(model, data.get("usage") or {})
        return text

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract and parse JSON from model output, stripping markdown fences."""
        # Strip ```json ... ``` or ``` ... ``` wrappers
        stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
        stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
        if stripped:
            return json.loads(stripped)
        raise ValueError("Empty response text")

    def _track(self, model: str, usage: dict) -> None:
        # Local servers may omit or truncate the usage block — count what exists.
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)

        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._calls += 1

        if model not in self._per_model:
            self._per_model[model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self._per_model[model]["input_tokens"] += input_tokens
        self._per_model[model]["output_tokens"] += output_tokens
        self._per_model[model]["calls"] += 1

        logger.info(
            "LLM call: model=%s input_tokens=%d output_tokens=%d",
            model,
            input_tokens,
            output_tokens,
        )

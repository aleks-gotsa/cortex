"""Async client for OpenAI-compatible endpoints (Ollama, vLLM) with JSON parsing and token tracking."""

import json
import logging
import re

import httpx

from backend.config import settings
from backend.llm.base import LLMClientBase

logger = logging.getLogger(__name__)

# Local generation is slow — a long-document verify pass on laptop hardware
# can take 10+ minutes, so the read timeout is far above hosted-API norms.
_TIMEOUT = httpx.Timeout(connect=10.0, read=1800.0, write=30.0, pool=10.0)

# Reasoning models (e.g. qwen3) may emit chain-of-thought inline in the
# response body; strip it so callers only ever see the answer.
_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)

# Total attempts for a JSON-expecting call() before giving up. Small local
# models fail JSON non-deterministically, so a few extra attempts materially
# lifts reliability. Raising this never changes a call that already succeeded.
_MAX_JSON_ATTEMPTS = 3


class OpenAICompatLLMClient(LLMClientBase):
    """Calls an OpenAI-compatible chat-completions endpoint and tracks cumulative token usage."""

    def __init__(
        self,
        base_url: str | None = None,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> None:
        self._base_url = (base_url or settings.LOCAL_BASE_URL).rstrip("/")
        self._temperature = temperature
        self._seed = seed
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)
        self._input_tokens = 0
        self._output_tokens = 0
        self._calls = 0
        self._json_retries = 0
        self._per_model: dict[str, dict[str, int]] = {}

    # ── Public API ───────────────────────────────────────────────────────

    @property
    def json_retries(self) -> int:
        """How many call() invocations needed the JSON-retry fallback."""
        return self._json_retries

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
        need the grammar constraint far more than hosted ones do. Small
        models also fail JSON non-deterministically (a whole-document value
        occasionally degenerates into a repetition loop or overruns the token
        budget), so a parse failure is retried up to ``_MAX_JSON_ATTEMPTS``
        times, the retries carrying an explicit JSON-only instruction.
        """
        last_error: Exception | None = None
        for attempt in range(_MAX_JSON_ATTEMPTS):
            attempt_system = system
            if attempt > 0:
                attempt_system = system + "\n\nRespond ONLY with valid JSON, no markdown fences."
            text = await self._send(attempt_system, user_message, model, max_tokens, json_mode=True)
            try:
                return self._parse_json(text)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < _MAX_JSON_ATTEMPTS:
                    self._json_retries += 1
                    logger.warning(
                        "JSON parse failed for model=%s (attempt %d/%d) — retrying",
                        model, attempt + 1, _MAX_JSON_ATTEMPTS,
                    )

        raise last_error  # exhausted attempts

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
        self._json_retries = 0
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
        # Streaming is load-bearing, not cosmetic: local servers cap
        # non-streaming requests (Ollama 500s them at 10 minutes), and long
        # verify/synthesis generations on laptop hardware run past that.
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        # Deterministic decoding for evals — omitted entirely unless configured.
        if self._temperature is not None:
            payload["temperature"] = self._temperature
        if self._seed is not None:
            payload["seed"] = self._seed

        text_parts: list[str] = []
        usage: dict = {}
        try:
            async with self._client.stream(
                "POST", f"{self._base_url}/chat/completions", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    choices = chunk.get("choices") or []
                    if choices:
                        content = (choices[0].get("delta") or {}).get("content")
                        if content:
                            text_parts.append(content)
        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot reach LLM endpoint at {self._base_url} — is Ollama running? "
                "Start it with `ollama serve`."
            ) from exc

        text = _THINK_BLOCK.sub("", "".join(text_parts)).strip()
        self._track(model, usage)
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

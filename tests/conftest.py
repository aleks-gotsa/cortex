"""Shared test fixtures — a stub LLM client for exercising pipeline stages offline."""

import pytest

from backend.llm.base import LLMClientBase


class StubLLMClient(LLMClientBase):
    """Returns a canned payload; never touches the network."""

    def __init__(self, payload: dict | None = None, text: str = "") -> None:
        self._payload = payload or {}
        self._text = text

    async def call(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> dict:
        return self._payload

    async def call_text(self, system: str, user_message: str, model: str, max_tokens: int = 4096) -> str:
        return self._text

    def get_usage(self) -> dict[str, int]:
        return {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def get_usage_by_model(self) -> dict[str, dict[str, int]]:
        return {}

    def reset_usage(self) -> None:
        pass


@pytest.fixture
def stub_client():
    return StubLLMClient

"""OpenAICompatLLMClient.call() JSON retry loop — recover on a later attempt,
raise after exhausting attempts. _send is stubbed so no network is touched."""

import asyncio

import pytest

from backend.llm.openai_compat_client import OpenAICompatLLMClient, _MAX_JSON_ATTEMPTS


def _client_with_responses(responses: list[str]) -> OpenAICompatLLMClient:
    client = OpenAICompatLLMClient.__new__(OpenAICompatLLMClient)
    client._json_retries = 0
    client._input_tokens = client._output_tokens = client._calls = 0
    client._per_model = {}
    it = iter(responses)

    async def fake_send(system, user_message, model, max_tokens, json_mode):
        return next(it)

    client._send = fake_send  # type: ignore[method-assign]
    return client


def test_recovers_on_second_attempt():
    client = _client_with_responses(["not json", '{"ok": 1}'])
    result = asyncio.run(client.call("s", "u", "m"))
    assert result == {"ok": 1}
    assert client.json_retries == 1  # one failed attempt before success


def test_recovers_on_third_attempt():
    assert _MAX_JSON_ATTEMPTS >= 3
    client = _client_with_responses(["bad", "still bad", '{"ok": 2}'])
    result = asyncio.run(client.call("s", "u", "m"))
    assert result == {"ok": 2}
    assert client.json_retries == 2


def test_raises_after_exhausting_attempts():
    client = _client_with_responses(["bad"] * _MAX_JSON_ATTEMPTS)
    with pytest.raises((ValueError, __import__("json").JSONDecodeError)):
        asyncio.run(client.call("s", "u", "m"))
    assert client.json_retries == _MAX_JSON_ATTEMPTS - 1

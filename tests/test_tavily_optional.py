"""Tavily-optional behavior — no API key means [], no exception, no request."""

import asyncio

import httpx

from backend.search import tavily


def test_no_key_returns_empty_list_without_network(monkeypatch):
    monkeypatch.setattr(tavily.settings, "TAVILY_API_KEY", "")

    def _fail(*args, **kwargs):
        raise AssertionError("network request attempted without an API key")

    monkeypatch.setattr(httpx.AsyncClient, "post", _fail)
    assert asyncio.run(tavily.search("anything")) == []


def test_explicit_key_argument_beats_missing_settings(monkeypatch):
    # With a key present the client proceeds to the HTTP call — stub it out.
    monkeypatch.setattr(tavily.settings, "TAVILY_API_KEY", "")

    async def _fake_post(self, url, json=None):
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"results": []}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)
    assert asyncio.run(tavily.search("anything", api_key="k")) == []

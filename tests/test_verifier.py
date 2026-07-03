"""verifier — verdict normalization and malformed-payload handling."""

import asyncio

import pytest

from backend.models import Source, Verdict
from backend.pipeline.verifier import verify
from tests.conftest import StubLLMClient

_SOURCES = [
    Source(
        url="https://a", title="t", snippet="s", full_content="content",
        relevance_score=0.9, sub_question_id="q1", search_engine="serper",
    )
]


def _payload(verdict: str) -> dict:
    return {
        "verified_document": "doc [1]",
        "summary": {
            "confirmed": 0,
            "weakened": 0,
            "removed": 1,
            "details": [
                {"claim": "c", "source_id": 1, "verdict": verdict, "reason": "r"},
            ],
        },
    }


def test_removed_verdict_normalized_to_unsupported():
    client = StubLLMClient(payload=_payload("removed"))
    result = asyncio.run(verify("doc [1]", _SOURCES, client=client))
    assert result.summary.details[0].verdict == Verdict.unsupported


def test_known_verdicts_pass_through():
    client = StubLLMClient(payload=_payload("weakened"))
    result = asyncio.run(verify("doc [1]", _SOURCES, client=client))
    assert result.summary.details[0].verdict == Verdict.weakened


def test_malformed_payload_raises_value_error():
    client = StubLLMClient(payload={"unexpected": True})
    with pytest.raises(ValueError, match="invalid VerificationResult"):
        asyncio.run(verify("doc", _SOURCES, client=client))


def test_unknown_verdict_string_raises_value_error():
    client = StubLLMClient(payload=_payload("maybe"))
    with pytest.raises(ValueError):
        asyncio.run(verify("doc", _SOURCES, client=client))


def test_truncated_verified_document_falls_back_to_original():
    original = "x" * 1000
    payload = _payload("confirmed")
    payload["verified_document"] = "y" * 500  # 50% of original — below the guard
    client = StubLLMClient(payload=payload)
    result = asyncio.run(verify(original, _SOURCES, client=client))
    assert result.verified_document == original


def test_non_truncated_verified_document_is_kept():
    original = "x" * 1000
    payload = _payload("confirmed")
    payload["verified_document"] = "y" * 800  # 80% — above the guard
    client = StubLLMClient(payload=payload)
    result = asyncio.run(verify(original, _SOURCES, client=client))
    assert result.verified_document == "y" * 800

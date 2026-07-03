"""_parse_json — fenced, bare-fenced, plain, and empty model output.

Both LLM clients must parse identically; parametrized over the two
implementations to pin that contract.
"""

import pytest

from backend.llm.anthropic_client import AnthropicLLMClient
from backend.llm.openai_compat_client import OpenAICompatLLMClient

PARSERS = [AnthropicLLMClient._parse_json, OpenAICompatLLMClient._parse_json]


@pytest.mark.parametrize("parse", PARSERS)
def test_fenced_json(parse):
    assert parse('```json\n{"a": 1}\n```') == {"a": 1}


@pytest.mark.parametrize("parse", PARSERS)
def test_bare_fences(parse):
    assert parse('```\n{"a": [1, 2]}\n```') == {"a": [1, 2]}


@pytest.mark.parametrize("parse", PARSERS)
def test_plain_json_with_whitespace(parse):
    assert parse('  {"nested": {"b": true}}  ') == {"nested": {"b": True}}


@pytest.mark.parametrize("parse", PARSERS)
def test_empty_raises_value_error(parse):
    with pytest.raises(ValueError):
        parse("")
    with pytest.raises(ValueError):
        parse("```json\n```")

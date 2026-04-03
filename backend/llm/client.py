# Backward-compatible alias — all existing imports still work
from backend.llm.anthropic_client import AnthropicLLMClient as LLMClient
from backend.llm.base import LLMClientBase

__all__ = ["LLMClient", "get_llm_client"]


def get_llm_client(api_key: str | None = None) -> LLMClientBase:
    """
    Return the appropriate LLM client based on environment config.
    DYNAMO_ENABLED=false (default) -> AnthropicLLMClient (no change)
    DYNAMO_ENABLED=true           -> MockDynamoClient (logs routing)
    """
    try:
        from dynamo.config import dynamo_settings
        if dynamo_settings.DYNAMO_ENABLED:
            from dynamo.mock_client import MockDynamoClient
            return MockDynamoClient(api_key=api_key)
    except ImportError:
        pass
    return LLMClient(api_key=api_key)

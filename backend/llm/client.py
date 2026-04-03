# Backward-compatible alias — all existing imports still work
from backend.llm.anthropic_client import AnthropicLLMClient as LLMClient
from backend.llm.base import LLMClientBase

__all__ = ["LLMClient", "get_llm_client"]


def get_llm_client(api_key: str | None = None) -> LLMClientBase:
    """
    Return the appropriate LLM client based on environment config.
    DYNAMO_ENABLED=false (default) -> AnthropicLLMClient (no change)
    DYNAMO_ENABLED=true DYNAMO_MODE=mock -> MockDynamoClient (logs routing)
    DYNAMO_ENABLED=true DYNAMO_MODE=real -> DynamoLLMClient (real HTTP calls)
    """
    try:
        from dynamo.config import dynamo_settings
        if dynamo_settings.DYNAMO_ENABLED:
            if dynamo_settings.DYNAMO_MODE == "real":
                from dynamo.real_client import DynamoLLMClient
                return DynamoLLMClient()
            else:
                from dynamo.mock_client import MockDynamoClient
                return MockDynamoClient(api_key=api_key)
    except ImportError:
        pass
    return LLMClient(api_key=api_key)

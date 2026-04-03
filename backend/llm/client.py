# Backward-compatible alias — all existing imports still work
from backend.llm.anthropic_client import AnthropicLLMClient as LLMClient

__all__ = ["LLMClient"]

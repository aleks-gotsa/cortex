"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    @abstractmethod
    async def call(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Send message, return parsed JSON response."""
        ...

    @abstractmethod
    async def call_text(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 4096,
    ) -> str:
        """Send message, return raw text response."""
        ...

    @abstractmethod
    def get_usage(self) -> dict[str, int]:
        ...

    @abstractmethod
    def get_usage_by_model(self) -> dict[str, dict[str, int]]:
        ...

    @abstractmethod
    def reset_usage(self) -> None:
        ...

    async def close(self) -> None:
        """Optional cleanup. Default no-op."""
        pass

"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is loaded from .env or environment variables."""

    # --- API Keys (optional — BYOK users provide keys per-request) ---
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    SERPER_API_KEY: str = Field(default="", validation_alias="SERPER_API_KEY")
    TAVILY_API_KEY: str = Field(default="", validation_alias="TAVILY_API_KEY")

    # --- LLM backend: "anthropic" (default) or "local" (OpenAI-compatible) ---
    LLM_BACKEND: str = Field(default="anthropic", validation_alias="LLM_BACKEND")
    LOCAL_BASE_URL: str = Field(default="http://localhost:11434/v1", validation_alias="LOCAL_BASE_URL")
    LOCAL_MODEL_PLANNING: str = Field(default="llama3.2:3b", validation_alias="LOCAL_MODEL_PLANNING")
    LOCAL_MODEL_GAP_DETECTION: str = Field(default="llama3.2:3b", validation_alias="LOCAL_MODEL_GAP_DETECTION")
    LOCAL_MODEL_SYNTHESIS: str = Field(default="qwen3:8b", validation_alias="LOCAL_MODEL_SYNTHESIS")
    LOCAL_MODEL_VERIFICATION: str = Field(default="qwen3:8b", validation_alias="LOCAL_MODEL_VERIFICATION")

    # --- Qdrant ---
    QDRANT_URL: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    QDRANT_COLLECTION: str = Field(default="cortex_research", validation_alias="QDRANT_COLLECTION")
    QDRANT_API_KEY: str = Field(default="", validation_alias="QDRANT_API_KEY")

    # --- SQLite ---
    DATABASE_PATH: str = Field(default="./data/cortex.db", validation_alias="DATABASE_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

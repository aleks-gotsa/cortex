"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration is loaded from .env or environment variables."""

    # --- API Keys (required) ---
    ANTHROPIC_API_KEY: str = Field(validation_alias="ANTHROPIC_API_KEY")
    SERPER_API_KEY: str = Field(validation_alias="SERPER_API_KEY")
    TAVILY_API_KEY: str = Field(validation_alias="TAVILY_API_KEY")

    # --- Qdrant ---
    QDRANT_URL: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    QDRANT_COLLECTION: str = Field(default="cortex_research", validation_alias="QDRANT_COLLECTION")
    QDRANT_API_KEY: str = Field(default="", validation_alias="QDRANT_API_KEY")

    # --- SQLite ---
    DATABASE_PATH: str = Field(default="./data/cortex.db", validation_alias="DATABASE_PATH")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

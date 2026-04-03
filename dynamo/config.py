"""Dynamo disaggregated inference configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DynamoSettings(BaseSettings):
    DYNAMO_ENABLED: bool = False
    DYNAMO_PREFILL_URL: str = "http://localhost:8001/v1"
    DYNAMO_DECODE_URL: str = "http://localhost:8002/v1"
    DYNAMO_TRITON_URL: str = "http://localhost:8003"
    DYNAMO_PREFILL_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct"
    DYNAMO_DECODE_MODEL: str = "meta-llama/Llama-3.1-70B-Instruct"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


dynamo_settings = DynamoSettings()

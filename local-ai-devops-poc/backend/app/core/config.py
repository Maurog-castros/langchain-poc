from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config. Secrets come from env, never code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "local-ai-devops-poc"
    environment: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_prefix: str = Field(default="local-ai-devops-poc", alias="S3_PREFIX")

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    local_llm_api_base_url: str | None = Field(
        default=None,
        alias="LOCAL_LLM_API_BASE_URL",
    )
    openai_compatible_base_url: str | None = Field(
        default=None,
        alias="OPENAI_COMPATIBLE_BASE_URL",
    )
    openai_compatible_api_key: str | None = Field(
        default=None,
        alias="OPENAI_COMPATIBLE_API_KEY",
    )

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    chroma_path: Path = Field(default=Path("data/chroma"), alias="CHROMA_PATH")
    documents_path: Path = Field(
        default=Path("data/documents"),
        alias="DOCUMENTS_PATH",
    )
    reports_path: Path = Field(default=Path("reports"), alias="REPORTS_PATH")
    request_timeout_seconds: float = Field(default=60.0, alias="REQUEST_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""
Application settings for local-ai-devops-poc.

All secrets and environment-specific values come from environment variables
or a ``.env`` file — NEVER from source code.

Environment separation
----------------------
- ``APP_ENV=local``  → defaults tuned for single-machine development.
- ``APP_ENV=dev``    → can point to shared dev infra (e.g., dev S3 bucket).
- ``APP_ENV=prod``   → strict timeouts, JSON logs, real bucket required.

pydantic-settings reads ``APP_ENV`` first, then applies ``env_file=".env"``.
The ``.env`` file is git-ignored; ``.env.example`` is committed.

CloudWatch / SSM integration note
----------------------------------
In ECS or Lambda you would inject these values via:
  - SSM Parameter Store (``/local-ai-devops-poc/<key>``)
  - AWS Secrets Manager for ``OPENAI_COMPATIBLE_API_KEY``

Never print the ``openai_compatible_api_key`` value in logs.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.  Secrets come from env/SSM, never from code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    app_name: str = "local-ai-devops-poc"
    environment: Literal["local", "dev", "prod"] = Field(
        default="local",
        alias="APP_ENV",
        description="Controls log format, strictness of validations, etc.",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def json_logs(self) -> bool:
        """Emit JSON logs in non-local environments (Docker / ECS / Lambda)."""
        return self.environment != "local"

    # ── AWS ─────────────────────────────────────────────────────────────────
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket: str | None = Field(
        default=None,
        alias="S3_BUCKET",
        description="Target S3 bucket.  Required for upload/download operations.",
    )
    s3_prefix: str = Field(
        default="local-ai-devops-poc",
        alias="S3_PREFIX",
        description="All objects are stored under s3://<bucket>/<prefix>/.",
    )

    # ── Model providers ──────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Ollama REST API base URL.  Change to Docker service name in Compose.",
    )
    local_llm_api_base_url: str | None = Field(
        default=None,
        alias="LOCAL_LLM_API_BASE_URL",
        description="OpenAI-style API served locally (e.g., vLLM, LM Studio).",
    )
    openai_compatible_base_url: str | None = Field(
        default=None,
        alias="OPENAI_COMPATIBLE_BASE_URL",
        description="Remote OpenAI-compatible endpoint (Together AI, Anyscale, etc.).",
    )
    openai_compatible_api_key: str | None = Field(
        default=None,
        alias="OPENAI_COMPATIBLE_API_KEY",
        description="API key for the remote OpenAI-compatible provider.  Store in SSM/Secrets Manager.",
    )

    # ── RAG ──────────────────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
        description="HuggingFace model id for sentence-transformers.  Downloaded on first use.",
    )
    chroma_path: Path = Field(
        default=Path("data/chroma"),
        alias="CHROMA_PATH",
        description="Local directory for ChromaDB persistent storage.",
    )
    documents_path: Path = Field(
        default=Path("data/documents"),
        alias="DOCUMENTS_PATH",
        description="Directory from which RAG ingestion reads documents.",
    )

    # ── General ──────────────────────────────────────────────────────────────
    reports_path: Path = Field(
        default=Path("reports"),
        alias="REPORTS_PATH",
        description="Output directory for benchmark and evaluation reports.",
    )
    request_timeout_seconds: float = Field(
        default=60.0,
        alias="REQUEST_TIMEOUT_SECONDS",
        description="HTTP timeout (seconds) for calls to LLM providers.",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton per process)."""
    return Settings()

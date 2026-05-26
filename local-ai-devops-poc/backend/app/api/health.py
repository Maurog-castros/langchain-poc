"""
Health check endpoint.

GET /health
-----------
Returns:
  - Application name and version.
  - Runtime environment.
  - Status of each optional integration: Ollama, S3 bucket, ChromaDB.

The integrations are checked asynchronously with a short timeout so the
health endpoint stays fast even when a provider is unreachable.  The overall
``status`` field is:

  - ``ok``      → all checked integrations reachable.
  - ``degraded`` → at least one optional integration is down (the API is
                   still usable for the integrations that are up).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter

from app.api.deps import s3_service, settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger("local_ai_devops")


async def _check_ollama() -> dict[str, Any]:
    """Ping the Ollama server and return status."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"status": "ok", "models": models}
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc)}


def _check_s3() -> dict[str, Any]:
    """Verify the S3 bucket is accessible (head-bucket, no data read)."""
    if not settings.s3_bucket:
        return {"status": "not_configured"}
    try:
        s3_service.client.head_bucket(Bucket=settings.s3_bucket)
        return {"status": "ok", "bucket": settings.s3_bucket}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _check_chroma() -> dict[str, Any]:
    """Verify ChromaDB path exists and is accessible."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(settings.chroma_path))
        collections = [c.name for c in client.list_collections()]
        return {"status": "ok", "collections": collections}
    except ImportError:
        return {"status": "not_installed"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Return application health and integration status.

    The response always includes ``status``, ``app``, and ``environment``.
    The ``integrations`` dict contains per-service diagnostics.
    """
    ollama_check = await _check_ollama()
    s3_check = _check_s3()
    chroma_check = _check_chroma()

    integrations = {
        "ollama": ollama_check,
        "s3": s3_check,
        "chroma": chroma_check,
    }

    # Degraded if any integration has a non-ok status (excluding not_configured).
    degraded = any(
        v.get("status") not in ("ok", "not_configured", "not_installed")
        for v in integrations.values()
    )
    status = "degraded" if degraded else "ok"

    logger.info("health_check", extra={"status": status, "integrations": integrations})

    return HealthResponse(
        status=status,
        app="local-ai-devops-poc",
        environment=settings.environment,
        integrations=integrations,
    )

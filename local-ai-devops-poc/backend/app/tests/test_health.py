"""
Tests for the health endpoint.

Uses FastAPI TestClient (synchronous wrapper around HTTPX).
No external services are needed — Ollama/S3/Chroma probes are mocked.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    with (
        patch("app.api.health._check_ollama", new_callable=AsyncMock, return_value={"status": "ok", "models": []}),
        patch("app.api.health._check_s3", return_value={"status": "not_configured"}),
        patch("app.api.health._check_chroma", return_value={"status": "not_installed"}),
    ):
        response = client.get("/health")
    assert response.status_code == 200


def test_health_body_fields() -> None:
    with (
        patch("app.api.health._check_ollama", new_callable=AsyncMock, return_value={"status": "ok", "models": ["llama3.2"]}),
        patch("app.api.health._check_s3", return_value={"status": "not_configured"}),
        patch("app.api.health._check_chroma", return_value={"status": "not_installed"}),
    ):
        response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "local-ai-devops-poc"
    assert "integrations" in data
    assert data["integrations"]["ollama"]["models"] == ["llama3.2"]


def test_health_degraded_when_ollama_unreachable() -> None:
    with (
        patch("app.api.health._check_ollama", new_callable=AsyncMock, return_value={"status": "unreachable", "error": "connection refused"}),
        patch("app.api.health._check_s3", return_value={"status": "not_configured"}),
        patch("app.api.health._check_chroma", return_value={"status": "not_installed"}),
    ):
        response = client.get("/health")
    data = response.json()
    assert data["status"] == "degraded"

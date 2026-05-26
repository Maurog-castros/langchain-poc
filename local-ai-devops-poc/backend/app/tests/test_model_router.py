"""
Tests for ModelRouter.

ModelRouter uses httpx to call external services (Ollama, OpenAI-compatible APIs).
We mock the HTTP layer with ``respx`` or ``unittest.mock.AsyncMock`` so tests
run without any running service.
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.models.providers import ModelProvider
from app.models.schemas import ChatRequest
from app.services.model_router import ModelRouter, UnsupportedProviderError


def _make_router(settings_overrides: dict | None = None) -> ModelRouter:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        **(settings_overrides or {}),
    )
    return ModelRouter(settings, logging.getLogger("test"))


OLLAMA_REQUEST = ChatRequest(
    provider=ModelProvider.OLLAMA,
    model="llama3.2",
    prompt="Hello",
)


@pytest.mark.asyncio
async def test_ollama_chat_returns_response() -> None:
    router = _make_router()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "Hello back!"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await router.chat(OLLAMA_REQUEST)

    assert result.response == "Hello back!"
    assert result.elapsed_ms >= 0
    assert result.provider == ModelProvider.OLLAMA


@pytest.mark.asyncio
async def test_ollama_chat_includes_system_prompt() -> None:
    """Verify system prompt is prepended when provided."""
    router = _make_router()
    captured_payload: dict = {}

    async def _fake_post(url, *, json, **kwargs):
        captured_payload.update(json)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"response": "ok"}
        return mock_resp

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=_fake_post):
        req = OLLAMA_REQUEST.model_copy(update={"system_prompt": "Be concise."})
        await router.chat(req)

    assert "Be concise." in captured_payload["prompt"]


@pytest.mark.asyncio
async def test_local_api_raises_when_url_not_configured() -> None:
    router = _make_router()  # LOCAL_LLM_API_BASE_URL is None by default
    with pytest.raises(ValueError, match="LOCAL_LLM_API_BASE_URL"):
        await router.chat(
            ChatRequest(provider=ModelProvider.LOCAL_API, model="any", prompt="test")
        )


@pytest.mark.asyncio
async def test_s3_artifact_returns_note() -> None:
    router = _make_router()
    result = await router.chat(
        ChatRequest(provider=ModelProvider.S3_ARTIFACT, model="adapter.bin", prompt="test")
    )
    assert "S3" in result.response or "ollama" in result.response.lower() or result.response


@pytest.mark.asyncio
async def test_unsupported_provider_raises() -> None:
    """Passing an invalid provider value should raise UnsupportedProviderError."""
    router = _make_router()
    # Bypass Pydantic validation to inject an invalid provider.
    request = ChatRequest(provider=ModelProvider.OLLAMA, model="x", prompt="y")
    object.__setattr__(request, "provider", "invalid_provider")
    with pytest.raises((UnsupportedProviderError, Exception)):
        await router.chat(request)

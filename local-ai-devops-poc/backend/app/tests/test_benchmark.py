"""
Tests for BenchmarkService.

Uses AsyncMock to simulate ModelRouter responses without calling any LLM.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.providers import ModelProvider
from app.models.schemas import BenchmarkRequest, ChatRequest, ChatResponse
from app.services.benchmark_service import BenchmarkService


def _mock_router(response_text: str = "ok", elapsed_ms: float = 150.0) -> MagicMock:
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=ChatResponse(
            provider=ModelProvider.OLLAMA,
            model="llama3.2",
            response=response_text,
            elapsed_ms=elapsed_ms,
        )
    )
    return router


def _mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.s3_bucket = None
    settings.reports_path = MagicMock()
    return settings


@pytest.mark.asyncio
async def test_benchmark_returns_results_for_each_combination() -> None:
    """2 models × 2 prompts → 4 results."""
    router = _mock_router()
    service = BenchmarkService(router, _mock_settings())

    request = BenchmarkRequest(
        prompts=["prompt A", "prompt B"],
        models=[
            ChatRequest(provider=ModelProvider.OLLAMA, model="llama3.2", prompt="x"),
            ChatRequest(provider=ModelProvider.OLLAMA, model="mistral", prompt="x"),
        ],
    )
    report = await service.run(request)
    assert len(report.results) == 4


@pytest.mark.asyncio
async def test_benchmark_captures_error_without_raising() -> None:
    router = MagicMock()
    router.chat = AsyncMock(side_effect=RuntimeError("connection refused"))
    service = BenchmarkService(router, _mock_settings())

    request = BenchmarkRequest(
        prompts=["hello"],
        models=[ChatRequest(provider=ModelProvider.OLLAMA, model="llama3.2", prompt="x")],
    )
    report = await service.run(request)
    assert len(report.results) == 1
    assert not report.results[0].ok
    assert "connection refused" in report.results[0].error


@pytest.mark.asyncio
async def test_benchmark_summary_has_correct_keys() -> None:
    router = _mock_router(elapsed_ms=200.0)
    service = BenchmarkService(router, _mock_settings())

    request = BenchmarkRequest(
        prompts=["p1"],
        models=[ChatRequest(provider=ModelProvider.OLLAMA, model="llama3.2", prompt="x")],
    )
    report = await service.run(request)
    key = "ollama/llama3.2"
    assert key in report.summary
    assert report.summary[key]["avg_ms"] == pytest.approx(200.0, rel=1e-3)
    assert report.summary[key]["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_benchmark_summary_success_rate_with_errors() -> None:
    """1 success + 1 error for the same model → 50% success rate."""
    call_count = 0

    async def _alternating(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:
            raise RuntimeError("fail")
        return ChatResponse(
            provider=ModelProvider.OLLAMA,
            model="llama3.2",
            response="ok",
            elapsed_ms=100.0,
        )

    router = MagicMock()
    router.chat = _alternating
    service = BenchmarkService(router, _mock_settings())

    request = BenchmarkRequest(
        prompts=["p1", "p2"],
        models=[ChatRequest(provider=ModelProvider.OLLAMA, model="llama3.2", prompt="x")],
    )
    report = await service.run(request)
    assert report.summary["ollama/llama3.2"]["success_rate"] == pytest.approx(0.5)

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import benchmark_service
from app.models.schemas import BenchmarkRequest, BenchmarkResult

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.post("", response_model=list[BenchmarkResult])
async def benchmark(request: BenchmarkRequest) -> list[BenchmarkResult]:
    return await benchmark_service.run(request)

"""
Benchmark API route.

POST /benchmark
    Run a set of models against a set of prompts and return timing results.
    Pass ``save_report=true`` as query parameter to persist a JSON report.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import benchmark_service
from app.models.schemas import BenchmarkReport, BenchmarkRequest

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.post(
    "",
    response_model=BenchmarkReport,
    summary="Benchmark models",
    description=(
        "Runs every prompt against every model and returns latency statistics. "
        "Models that fail are included as ok=False results. "
        "Pass save_report=true to persist results to disk (and S3 if configured)."
    ),
)
async def benchmark(
    request: BenchmarkRequest,
    save_report: bool = Query(
        default=False,
        description="Write report JSON to reports/ and optionally upload to S3.",
    ),
) -> BenchmarkReport:
    return await benchmark_service.run(request, save_report=save_report)

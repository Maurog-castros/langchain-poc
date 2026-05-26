"""
Benchmark service: measures latency and quality across multiple LLM providers.

What it does
------------
1. For each (model, prompt) combination, sends a chat request via ModelRouter.
2. Records elapsed_ms, whether the request succeeded, and a preview of the response.
3. Aggregates per-model statistics: avg, min, max latency and success rate.
4. Optionally writes a JSON report to disk and uploads it to S3.

Benchmark design principles
----------------------------
- Tests run sequentially (not concurrently) to avoid throttling local runtimes.
- Errors are captured as ``ok=False`` results, not exceptions — so a single
  failing provider does not abort the whole benchmark.
- Report files are timestamped and stored under ``reports/``.

How to interpret results
------------------------
- ``elapsed_ms`` is wall-clock time from HTTP request to complete response body.
  It includes model loading time if the model was cold.
- For fair comparisons, run at least 3 iterations per prompt and discard the first
  (warm-up).
- See ``docs/BENCHMARKING.md`` for a full methodology guide.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.schemas import BenchmarkReport, BenchmarkRequest, BenchmarkResult
from app.services.model_router import ModelRouter

logger = logging.getLogger("local_ai_devops")


class BenchmarkService:
    def __init__(self, router: ModelRouter, settings: Settings) -> None:
        self.router = router
        self.settings = settings

    async def run(
        self,
        request: BenchmarkRequest,
        *,
        save_report: bool = False,
    ) -> BenchmarkReport:
        """Run all (model × prompt) combinations and return a ``BenchmarkReport``.

        Parameters
        ----------
        request:
            Contains the list of models and prompts to benchmark.
        save_report:
            When ``True``, write the report as JSON to ``reports/`` and
            optionally upload it to S3 if S3_BUCKET is configured.
        """
        results: list[BenchmarkResult] = []

        for model_request in request.models:
            for prompt in request.prompts:
                current = model_request.model_copy(update={"prompt": prompt})
                try:
                    response = await self.router.chat(current)
                    results.append(
                        BenchmarkResult(
                            provider=current.provider,
                            model=current.model,
                            prompt=prompt,
                            elapsed_ms=response.elapsed_ms,
                            ok=True,
                            response_preview=response.response[:240],
                        )
                    )
                    logger.info(
                        "benchmark_result",
                        extra={
                            "provider": current.provider.value,
                            "model": current.model,
                            "elapsed_ms": response.elapsed_ms,
                            "ok": True,
                        },
                    )
                except Exception as exc:
                    results.append(
                        BenchmarkResult(
                            provider=current.provider,
                            model=current.model,
                            prompt=prompt,
                            elapsed_ms=0.0,
                            ok=False,
                            error=str(exc),
                        )
                    )
                    logger.warning(
                        "benchmark_error",
                        extra={
                            "provider": current.provider.value,
                            "model": current.model,
                            "error": str(exc),
                        },
                    )

        summary = self._summarise(results)
        report = BenchmarkReport(results=results, summary=summary)

        if save_report:
            report = self._persist(report)

        return report

    @staticmethod
    def _summarise(results: list[BenchmarkResult]) -> dict[str, Any]:
        """Compute per-model statistics from raw results."""
        by_model: dict[str, list[BenchmarkResult]] = {}
        for result in results:
            key = f"{result.provider.value}/{result.model}"
            by_model.setdefault(key, []).append(result)

        stats: dict[str, Any] = {}
        for model_key, model_results in by_model.items():
            ok_results = [r for r in model_results if r.ok]
            latencies = [r.elapsed_ms for r in ok_results]
            stats[model_key] = {
                "total": len(model_results),
                "success": len(ok_results),
                "success_rate": len(ok_results) / len(model_results) if model_results else 0.0,
                "avg_ms": sum(latencies) / len(latencies) if latencies else None,
                "min_ms": min(latencies) if latencies else None,
                "max_ms": max(latencies) if latencies else None,
            }
        return stats

    def _persist(self, report: BenchmarkReport) -> BenchmarkReport:
        """Write report JSON to disk; try S3 upload if configured."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        reports_dir = self.settings.reports_path
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"benchmark_{timestamp}.json"

        payload = report.model_dump(mode="json")
        report_file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("benchmark_report_saved", extra={"path": str(report_file)})
        report = report.model_copy(update={"report_path": str(report_file)})

        # Try S3 upload; non-fatal if bucket is not configured.
        if self.settings.s3_bucket:
            try:
                from app.models.providers import ArtifactKind
                from app.services.s3_service import S3Service

                s3 = S3Service(self.settings, logger)
                s3_resp = s3.upload(report_file, ArtifactKind.REPORT)
                report = report.model_copy(update={"s3_uri": s3_resp.uri})
                logger.info("benchmark_report_uploaded", extra={"s3_uri": s3_resp.uri})
            except Exception as exc:
                logger.warning("benchmark_s3_upload_skipped", extra={"reason": str(exc)})

        return report

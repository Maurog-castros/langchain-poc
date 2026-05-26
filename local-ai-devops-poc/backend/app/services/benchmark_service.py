from __future__ import annotations

from app.models.schemas import BenchmarkRequest, BenchmarkResult
from app.services.model_router import ModelRouter


class BenchmarkService:
    def __init__(self, router: ModelRouter) -> None:
        self.router = router

    async def run(self, request: BenchmarkRequest) -> list[BenchmarkResult]:
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
        return results

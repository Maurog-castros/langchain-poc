from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import get_settings
from app.models.providers import ModelProvider
from app.models.schemas import BenchmarkRequest, ChatRequest
from app.services.benchmark_service import BenchmarkService
from app.services.model_router import ModelRouter


async def run() -> None:
    parser = argparse.ArgumentParser(description="Benchmark one model against prompts")
    parser.add_argument("--provider", choices=[provider.value for provider in ModelProvider], default=ModelProvider.OLLAMA.value)
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--prompt", action="append", required=True)
    args = parser.parse_args()

    router = ModelRouter(get_settings(), logging.getLogger("benchmark_cli"))
    service = BenchmarkService(router)
    results = await service.run(
        BenchmarkRequest(
            prompts=args.prompt,
            models=[ChatRequest(provider=ModelProvider(args.provider), model=args.model, prompt=args.prompt[0])],
        )
    )
    print(json.dumps([result.model_dump() for result in results], indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(run())

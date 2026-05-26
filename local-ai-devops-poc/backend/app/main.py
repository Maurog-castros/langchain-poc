"""
FastAPI application entry point.

Startup order
-------------
1. Read Settings from environment / .env.
2. Configure logging (text in local, JSON in prod for CloudWatch).
3. Register CORS middleware.
4. Mount all API routers.

CORS
----
Origins are restricted to the local Vite dev server in development.
In production, replace with your actual frontend domain or use an
API Gateway / CloudFront CORS policy instead.

Lifespan events
---------------
FastAPI's ``lifespan`` context manager is used (instead of deprecated
``on_event``) to run startup validation cleanly.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import benchmark, chat, fine_tuning, health, models, rag
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level, json_logs=settings.json_logs)

logger = logging.getLogger("local_ai_devops")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Run startup validation, then yield to serve requests."""
    logger.info(
        "startup",
        extra={
            "environment": settings.environment,
            "ollama_url": settings.ollama_base_url,
            "s3_bucket": settings.s3_bucket or "(not configured)",
            "embedding_model": settings.embedding_model,
        },
    )
    if not settings.s3_bucket:
        logger.warning(
            "s3_bucket_not_configured",
            extra={"hint": "Set S3_BUCKET in .env to enable upload/download operations."},
        )
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Local-first AI/DevOps PoC: multi-provider LLM routing, RAG over local "
        "documents, S3 artifact sync, benchmark, personality evaluation and "
        "fine-tuning preparation."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the local Vite dev server.  In prod, tighten this list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(rag.router)
app.include_router(benchmark.router)
app.include_router(fine_tuning.router)

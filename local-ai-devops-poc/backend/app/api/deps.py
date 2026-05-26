"""
Dependency injection for the API layer.

All services are instantiated once at module load time (module-level singletons).
This is acceptable for a PoC; in a production multi-tenant deployment you would
use FastAPI's ``Depends`` with proper scoping.

Order matters: config and logger must exist before services that need them.
"""
from __future__ import annotations

import logging

from app.core.config import Settings, get_settings
from app.services.benchmark_service import BenchmarkService
from app.services.embedding_service import EmbeddingService
from app.services.fine_tuning_service import FineTuningService
from app.services.model_router import ModelRegistry, ModelRouter
from app.services.personality_service import PersonalityService
from app.services.rag_service import RagService
from app.services.s3_service import S3Service

# ── Bootstrap ────────────────────────────────────────────────────────────────

settings: Settings = get_settings()
logger = logging.getLogger("local_ai_devops")

# ── Service instances ─────────────────────────────────────────────────────────

# Model registry: in-memory store for model descriptors.
registry = ModelRegistry()

# Model router: dispatches chat requests to the correct provider.
router = ModelRouter(settings, logger)

# Embedding service: lazy-loads the sentence-transformers model on first use.
embeddings = EmbeddingService(settings)

# RAG service: ingest documents and query the vector store.
rag_service = RagService(settings, embeddings, logger)

# S3 service: upload, download and list artifacts.
s3_service = S3Service(settings, logger)

# Benchmark service: run models against prompts and produce reports.
benchmark_service = BenchmarkService(router, settings)

# Personality service: evaluate chatbot compliance with a persona profile.
personality_service = PersonalityService()

# Fine-tuning service: prepare LoRA training commands.
fine_tuning_service = FineTuningService()

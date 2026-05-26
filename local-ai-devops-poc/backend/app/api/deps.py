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

settings: Settings = get_settings()
logger = logging.getLogger("local_ai_devops")
registry = ModelRegistry()
router = ModelRouter(settings, logger)
embeddings = EmbeddingService(settings)
rag_service = RagService(settings, embeddings, logger)
s3_service = S3Service(settings, logger)
benchmark_service = BenchmarkService(router)
personality_service = PersonalityService()
fine_tuning_service = FineTuningService()

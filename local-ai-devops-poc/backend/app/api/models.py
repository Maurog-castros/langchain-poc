from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.api.deps import registry, s3_service
from app.models.schemas import ModelDescriptor, ModelRegistrationRequest, S3ArtifactResponse, S3DownloadRequest, S3UploadRequest

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/register", response_model=ModelDescriptor)
async def register_model(request: ModelRegistrationRequest) -> ModelDescriptor:
    return registry.register(request)


@router.get("", response_model=list[ModelDescriptor])
async def list_models() -> list[ModelDescriptor]:
    return registry.list()


@router.post("/s3/upload", response_model=S3ArtifactResponse)
async def upload_model(request: S3UploadRequest) -> S3ArtifactResponse:
    return s3_service.upload(Path(request.local_path), request.kind, request.s3_key)


@router.post("/s3/download", response_model=S3ArtifactResponse)
async def download_model(request: S3DownloadRequest) -> S3ArtifactResponse:
    return s3_service.download(request.s3_key, Path(request.local_path))

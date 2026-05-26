"""
Models API: model registry and S3 artifact management.

Endpoints
---------
POST /models/register        Register a model in the in-memory registry.
GET  /models                 List registered models.
POST /models/s3/upload       Upload a local file to S3.
POST /models/s3/download     Download an S3 object locally.
GET  /models/s3/list         List objects in the project S3 prefix.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query

from app.api.deps import registry, s3_service
from app.models.schemas import (
    ModelDescriptor,
    ModelRegistrationRequest,
    S3ArtifactResponse,
    S3DownloadRequest,
    S3ListResponse,
    S3UploadRequest,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post(
    "/register",
    response_model=ModelDescriptor,
    summary="Register a model",
    description="Add a model to the in-memory registry so it can be referenced by name in benchmarks.",
)
async def register_model(request: ModelRegistrationRequest) -> ModelDescriptor:
    return registry.register(request)


@router.get(
    "",
    response_model=list[ModelDescriptor],
    summary="List registered models",
)
async def list_models() -> list[ModelDescriptor]:
    return registry.list()


@router.post(
    "/s3/upload",
    response_model=S3ArtifactResponse,
    summary="Upload artifact to S3",
    description=(
        "Upload a local file to S3 under the configured project prefix. "
        "Requires S3_BUCKET to be set. "
        "Do NOT upload model weights to Git — use this endpoint instead."
    ),
)
async def upload_artifact(request: S3UploadRequest) -> S3ArtifactResponse:
    return s3_service.upload(Path(request.local_path), request.kind, request.s3_key)


@router.post(
    "/s3/download",
    response_model=S3ArtifactResponse,
    summary="Download artifact from S3",
)
async def download_artifact(request: S3DownloadRequest) -> S3ArtifactResponse:
    return s3_service.download(request.s3_key, Path(request.local_path))


@router.get(
    "/s3/list",
    response_model=S3ListResponse,
    summary="List S3 artifacts",
    description="List all objects in the project S3 prefix.  Optionally filter by sub-prefix (e.g. 'models', 'datasets').",
)
async def list_s3_artifacts(
    prefix: str | None = Query(
        default=None,
        description="Sub-prefix to filter (e.g. 'models', 'datasets', 'reports').",
    ),
) -> S3ListResponse:
    return s3_service.list_objects(prefix_override=prefix)

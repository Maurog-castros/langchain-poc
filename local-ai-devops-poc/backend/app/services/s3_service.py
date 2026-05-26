from __future__ import annotations

import logging
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.models.providers import ArtifactKind
from app.models.schemas import S3ArtifactResponse


class S3ConfigurationError(RuntimeError):
    pass


class S3Service:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.client = boto3.client("s3", region_name=settings.aws_region)

    def _bucket(self) -> str:
        if not self.settings.s3_bucket:
            raise S3ConfigurationError("S3_BUCKET is required")
        return self.settings.s3_bucket

    def build_key(self, kind: ArtifactKind, local_path: Path, s3_key: str | None) -> str:
        if s3_key:
            return s3_key.lstrip("/")
        return f"{self.settings.s3_prefix}/{kind.value}/{local_path.name}"

    def upload(self, local_path: Path, kind: ArtifactKind, s3_key: str | None = None) -> S3ArtifactResponse:
        if not local_path.exists() or not local_path.is_file():
            raise FileNotFoundError(str(local_path))

        bucket = self._bucket()
        key = self.build_key(kind, local_path, s3_key)
        try:
            self.client.upload_file(str(local_path), bucket, key)
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception("s3_upload_failed", extra={"bucket": bucket, "key": key})
            raise RuntimeError(f"S3 upload failed: {exc}") from exc

        self.logger.info("s3_upload_ok", extra={"bucket": bucket, "key": key})
        return S3ArtifactResponse(bucket=bucket, key=key, uri=f"s3://{bucket}/{key}")

    def download(self, s3_key: str, local_path: Path) -> S3ArtifactResponse:
        bucket = self._bucket()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.client.download_file(bucket, s3_key, str(local_path))
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception("s3_download_failed", extra={"bucket": bucket, "key": s3_key})
            raise RuntimeError(f"S3 download failed: {exc}") from exc

        self.logger.info("s3_download_ok", extra={"bucket": bucket, "key": s3_key})
        return S3ArtifactResponse(bucket=bucket, key=s3_key, uri=f"s3://{bucket}/{s3_key}")

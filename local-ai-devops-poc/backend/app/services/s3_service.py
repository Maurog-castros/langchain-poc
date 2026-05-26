"""
S3 service for artifact management.

Responsibilities
----------------
- Upload local files to S3 under a structured prefix.
- Download files from S3 to a local path.
- List objects in the project prefix.

Key naming convention
---------------------
All objects follow the pattern::

    s3://<bucket>/<s3_prefix>/<kind>/<filename>

Unless ``s3_key`` is explicitly provided to override the auto-generated key.

IAM minimum permissions required
---------------------------------
See ``infra/iam-policy-s3-minimal.json`` for the exact policy.
The service identity (IAM user / ECS task role) needs:

  - ``s3:ListBucket`` on the bucket (with condition on prefix).
  - ``s3:GetObject``, ``s3:PutObject``, ``s3:DeleteObject`` on the prefix.
  - ``s3:HeadBucket`` on the bucket (for health check).

Cost note
---------
- PUT requests: $0.005 / 1,000 requests (us-east-1).
- GET requests: $0.0004 / 1,000 requests.
- Storage: ~$0.023 / GB / month.
- Data transfer out: first 100 GB/month free, then $0.09/GB.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.models.providers import ArtifactKind
from app.models.schemas import S3ArtifactResponse, S3ListResponse


class S3ConfigurationError(RuntimeError):
    """Raised when S3_BUCKET is required but not configured."""


class S3Service:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        # boto3 reads credentials from the standard chain:
        #   1. Environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY).
        #   2. ~/.aws/credentials (local dev).
        #   3. ECS task role / EC2 instance profile (prod).
        # Never hardcode credentials here.
        self.client = boto3.client("s3", region_name=settings.aws_region)

    def _bucket(self) -> str:
        if not self.settings.s3_bucket:
            raise S3ConfigurationError(
                "S3_BUCKET environment variable is required for this operation."
            )
        return self.settings.s3_bucket

    def build_key(self, kind: ArtifactKind, local_path: Path, s3_key: str | None) -> str:
        """Derive the S3 object key from the artifact kind and filename."""
        if s3_key:
            return s3_key.lstrip("/")
        return f"{self.settings.s3_prefix}/{kind.value}/{local_path.name}"

    def upload(
        self,
        local_path: Path,
        kind: ArtifactKind,
        s3_key: str | None = None,
    ) -> S3ArtifactResponse:
        """Upload a local file to S3 and return its URI.

        Raises
        ------
        FileNotFoundError
            If the local file does not exist.
        RuntimeError
            If the S3 upload fails (wraps botocore errors).
        """
        if not local_path.exists() or not local_path.is_file():
            raise FileNotFoundError(f"File not found: {local_path}")

        bucket = self._bucket()
        key = self.build_key(kind, local_path, s3_key)
        size = local_path.stat().st_size

        try:
            # Use multipart upload automatically for large files via upload_file.
            self.client.upload_file(str(local_path), bucket, key)
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception("s3_upload_failed", extra={"bucket": bucket, "key": key})
            raise RuntimeError(f"S3 upload failed: {exc}") from exc

        self.logger.info(
            "s3_upload_ok",
            extra={"bucket": bucket, "key": key, "size_bytes": size},
        )
        return S3ArtifactResponse(
            bucket=bucket,
            key=key,
            uri=f"s3://{bucket}/{key}",
            size_bytes=size,
        )

    def download(self, s3_key: str, local_path: Path) -> S3ArtifactResponse:
        """Download an S3 object to a local path.

        Parent directories of ``local_path`` are created automatically.

        Raises
        ------
        RuntimeError
            If the S3 download fails.
        """
        bucket = self._bucket()
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.client.download_file(bucket, s3_key, str(local_path))
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception("s3_download_failed", extra={"bucket": bucket, "key": s3_key})
            raise RuntimeError(f"S3 download failed: {exc}") from exc

        size = local_path.stat().st_size
        self.logger.info(
            "s3_download_ok",
            extra={"bucket": bucket, "key": s3_key, "size_bytes": size},
        )
        return S3ArtifactResponse(
            bucket=bucket,
            key=s3_key,
            uri=f"s3://{bucket}/{s3_key}",
            size_bytes=size,
        )

    def list_objects(self, prefix_override: str | None = None) -> S3ListResponse:
        """List all objects under the project prefix.

        Parameters
        ----------
        prefix_override:
            Sub-prefix to filter (e.g. ``"models"`` will list
            ``<s3_prefix>/models/``).  Omit to list everything under the project.
        """
        bucket = self._bucket()
        base_prefix = self.settings.s3_prefix
        prefix = f"{base_prefix}/{prefix_override}/" if prefix_override else f"{base_prefix}/"

        paginator = self.client.get_paginator("list_objects_v2")
        objects: list[dict[str, Any]] = []
        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    objects.append(
                        {
                            "key": obj["Key"],
                            "size_bytes": obj["Size"],
                            "last_modified": obj["LastModified"].isoformat(),
                            "etag": obj.get("ETag", "").strip('"'),
                        }
                    )
        except (BotoCoreError, ClientError) as exc:
            self.logger.exception("s3_list_failed", extra={"bucket": bucket, "prefix": prefix})
            raise RuntimeError(f"S3 list failed: {exc}") from exc

        self.logger.info("s3_list_ok", extra={"prefix": prefix, "count": len(objects)})
        return S3ListResponse(prefix=prefix, objects=objects, count=len(objects))

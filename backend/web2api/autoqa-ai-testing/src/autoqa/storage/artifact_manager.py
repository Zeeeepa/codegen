"""
Artifact management for test results storage.

Supports local filesystem and S3-compatible storage backends.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO
from urllib.parse import urlparse

import aiofiles
import structlog

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = structlog.get_logger(__name__)


class ArtifactType(StrEnum):
    """Types of test artifacts."""

    SCREENSHOT = "screenshot"
    VIDEO = "video"
    LOG = "log"
    REPORT = "report"
    BASELINE = "baseline"
    DIFF = "diff"
    HAR = "har"
    TRACE = "trace"


class ArtifactManager:
    """
    Manages test artifacts storage and retrieval.

    Supports both local filesystem and S3-compatible storage.
    """

    def __init__(
        self,
        storage_path: str | Path | None = None,
        s3_bucket: str | None = None,
        s3_prefix: str = "autoqa",
        s3_client: S3Client | None = None,
    ) -> None:
        self._local_path = Path(storage_path) if storage_path else Path("./artifacts")
        self._s3_bucket = s3_bucket
        self._s3_prefix = s3_prefix
        self._s3_client = s3_client
        self._log = logger.bind(component="artifact_manager")

        self._local_path.mkdir(parents=True, exist_ok=True)

        if self._s3_bucket and self._s3_client is None:
            self._init_s3_client()

    def _init_s3_client(self) -> None:
        """Initialize S3 client from environment."""
        try:
            import boto3

            self._s3_client = boto3.client(
                "s3",
                endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
            )
            self._log.info("S3 client initialized", bucket=self._s3_bucket)
        except Exception as e:
            self._log.warning("Failed to initialize S3 client", error=str(e))

    def store(
        self,
        data: bytes | str | Path | BinaryIO,
        artifact_type: ArtifactType,
        test_run_id: str,
        filename: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """
        Store an artifact.

        Args:
            data: Artifact content
            artifact_type: Type of artifact
            test_run_id: Associated test run ID
            filename: Optional filename override
            metadata: Optional metadata to store with artifact

        Returns:
            Storage path or URL of the artifact
        """
        if filename is None:
            filename = self._generate_filename(artifact_type)

        content = self._read_content(data)
        content_hash = hashlib.sha256(content).hexdigest()[:16]

        relative_path = f"{test_run_id}/{artifact_type}/{filename}"

        local_path = self._store_locally(content, relative_path)

        if self._s3_bucket and self._s3_client:
            s3_path = self._store_to_s3(content, relative_path, metadata)
            self._log.info(
                "Artifact stored",
                type=artifact_type,
                local=str(local_path),
                s3=s3_path,
                size=len(content),
                hash=content_hash,
            )
            return s3_path

        self._log.info(
            "Artifact stored locally",
            type=artifact_type,
            path=str(local_path),
            size=len(content),
            hash=content_hash,
        )
        return str(local_path)

    def _read_content(self, data: bytes | str | Path | BinaryIO) -> bytes:
        """Read content from various sources."""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode("utf-8")
        elif isinstance(data, Path):
            return data.read_bytes()
        else:
            return data.read()

    def _generate_filename(self, artifact_type: ArtifactType) -> str:
        """Generate unique filename for artifact."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        extensions = {
            ArtifactType.SCREENSHOT: ".png",
            ArtifactType.VIDEO: ".webm",
            ArtifactType.LOG: ".log",
            ArtifactType.REPORT: ".html",
            ArtifactType.BASELINE: ".png",
            ArtifactType.DIFF: ".png",
            ArtifactType.HAR: ".har",
            ArtifactType.TRACE: ".json",
        }
        ext = extensions.get(artifact_type, ".bin")
        return f"{artifact_type}_{timestamp}{ext}"

    def _store_locally(self, content: bytes, relative_path: str) -> Path:
        """Store artifact to local filesystem."""
        full_path = self._local_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return full_path

    def _store_to_s3(
        self,
        content: bytes,
        relative_path: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Store artifact to S3."""
        if self._s3_client is None or self._s3_bucket is None:
            raise RuntimeError("S3 client not initialized")

        key = f"{self._s3_prefix}/{relative_path}"
        content_type = mimetypes.guess_type(relative_path)[0] or "application/octet-stream"

        extra_args: dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        self._s3_client.put_object(
            Bucket=self._s3_bucket,
            Key=key,
            Body=content,
            **extra_args,
        )

        return f"s3://{self._s3_bucket}/{key}"

    def retrieve(self, path: str) -> bytes:
        """
        Retrieve an artifact by path.

        Args:
            path: Local path or S3 URL

        Returns:
            Artifact content as bytes
        """
        if path.startswith("s3://"):
            return self._retrieve_from_s3(path)
        else:
            return Path(path).read_bytes()

    def _retrieve_from_s3(self, s3_url: str) -> bytes:
        """Retrieve artifact from S3."""
        if self._s3_client is None:
            raise RuntimeError("S3 client not initialized")

        parsed = urlparse(s3_url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        response = self._s3_client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    async def store_async(
        self,
        data: bytes | str | Path,
        artifact_type: ArtifactType,
        test_run_id: str,
        filename: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Async version of store."""
        if filename is None:
            filename = self._generate_filename(artifact_type)

        if isinstance(data, Path):
            async with aiofiles.open(data, "rb") as f:
                content = await f.read()
        elif isinstance(data, str):
            content = data.encode("utf-8")
        else:
            content = data

        relative_path = f"{test_run_id}/{artifact_type}/{filename}"

        full_path = self._local_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        if self._s3_bucket and self._s3_client:
            import asyncio

            loop = asyncio.get_event_loop()
            s3_path = await loop.run_in_executor(
                None,
                lambda: self._store_to_s3(content, relative_path, metadata),
            )
            return s3_path

        return str(full_path)

    def list_artifacts(
        self,
        test_run_id: str,
        artifact_type: ArtifactType | None = None,
    ) -> list[str]:
        """List artifacts for a test run."""
        artifacts: list[str] = []

        if artifact_type:
            search_path = self._local_path / test_run_id / artifact_type
        else:
            search_path = self._local_path / test_run_id

        if search_path.exists():
            for path in search_path.rglob("*"):
                if path.is_file():
                    artifacts.append(str(path))

        return sorted(artifacts)

    def delete_artifacts(
        self,
        test_run_id: str,
        artifact_type: ArtifactType | None = None,
    ) -> int:
        """Delete artifacts for a test run."""
        deleted = 0

        if artifact_type:
            search_path = self._local_path / test_run_id / artifact_type
        else:
            search_path = self._local_path / test_run_id

        if search_path.exists():
            for path in search_path.rglob("*"):
                if path.is_file():
                    path.unlink()
                    deleted += 1

            for path in sorted(search_path.rglob("*"), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()

        self._log.info(
            "Artifacts deleted",
            test_run_id=test_run_id,
            type=artifact_type,
            count=deleted,
        )
        return deleted

    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Get a presigned URL for S3 artifact.

        Args:
            path: S3 URL of the artifact
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        if not path.startswith("s3://"):
            raise ValueError("Path must be an S3 URL")

        if self._s3_client is None:
            raise RuntimeError("S3 client not initialized")

        parsed = urlparse(path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        url = self._s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    def get_artifact_stats(self, test_run_id: str) -> dict[str, Any]:
        """Get statistics about artifacts for a test run."""
        stats: dict[str, Any] = {
            "total_count": 0,
            "total_size": 0,
            "by_type": {},
        }

        artifacts = self.list_artifacts(test_run_id)

        for artifact_path in artifacts:
            path = Path(artifact_path)
            size = path.stat().st_size
            stats["total_count"] += 1
            stats["total_size"] += size

            artifact_type = path.parent.name
            if artifact_type not in stats["by_type"]:
                stats["by_type"][artifact_type] = {"count": 0, "size": 0}
            stats["by_type"][artifact_type]["count"] += 1
            stats["by_type"][artifact_type]["size"] += size

        return stats

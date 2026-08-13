"""Pluggable file storage backend.

Defaults to local disk so the project runs with zero external
dependencies. Set STORAGE_BACKEND=s3 (with the S3_* env vars) to switch
to an S3-compatible bucket without touching any calling code.
"""
import abc
import uuid
from pathlib import Path

from app.core.config import settings


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    def save(self, content: bytes, filename: str) -> str:
        """Persist content, return an opaque storage path/key."""

    @abc.abstractmethod
    def read(self, storage_path: str) -> bytes:
        """Read back previously saved content."""

    @abc.abstractmethod
    def delete(self, storage_path: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, storage_path: str) -> Path:
        resolved = (self.base_dir / storage_path).resolve()
        if self.base_dir.resolve() not in resolved.parents and resolved != self.base_dir.resolve():
            raise ValueError("Invalid storage path")
        return resolved

    def save(self, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix
        key = f"{uuid.uuid4().hex}{suffix}"
        path = self.base_dir / key
        path.write_bytes(content)
        return key

    def read(self, storage_path: str) -> bytes:
        return self._safe_path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        path = self._safe_path(storage_path)
        if path.exists():
            path.unlink()


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        import boto3  # imported lazily so boto3 isn't a hard dependency in local mode

        self.bucket = settings.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION or None,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
        )

    def save(self, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix
        key = f"{uuid.uuid4().hex}{suffix}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return key

    def read(self, storage_path: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=storage_path)
        return obj["Body"].read()

    def delete(self, storage_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_path)


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _backend
    if _backend is None:
        if settings.STORAGE_BACKEND == "s3":
            _backend = S3StorageBackend()
        else:
            _backend = LocalStorageBackend(settings.LOCAL_STORAGE_DIR)
    return _backend

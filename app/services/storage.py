"""File storage adapter abstraction.

Default: local filesystem (uploads/ and outputs/ dirs).
Designed for future swap to S3/MinIO without changing business logic.
"""

import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import UPLOAD_DIR, OUTPUT_DIR

logger = logging.getLogger("subtitle-generator")


class StorageAdapter(ABC):
    """Abstract file storage interface."""

    @abstractmethod
    def save_upload(self, filename: str, data: bytes) -> str:
        """Save an uploaded file. Returns the storage path/key."""

    @abstractmethod
    def get_upload_path(self, filename: str) -> Path | None:
        """Get the local path for an uploaded file."""

    @abstractmethod
    def save_output(self, filename: str, data: bytes) -> str:
        """Save an output file. Returns the storage path/key."""

    @abstractmethod
    def get_output_path(self, filename: str) -> Path | None:
        """Get the local path for an output file."""

    @abstractmethod
    def delete_upload(self, filename: str) -> bool:
        """Delete an uploaded file."""

    @abstractmethod
    def delete_output(self, filename: str) -> bool:
        """Delete an output file."""

    @abstractmethod
    def list_outputs(self) -> list[str]:
        """List output files."""

    @abstractmethod
    def get_storage_info(self) -> dict:
        """Get storage backend info."""


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter."""

    def __init__(self):
        UPLOAD_DIR.mkdir(exist_ok=True)
        OUTPUT_DIR.mkdir(exist_ok=True)

    def save_upload(self, filename: str, data: bytes) -> str:
        path = UPLOAD_DIR / filename
        path.write_bytes(data)
        return str(path)

    def get_upload_path(self, filename: str) -> Path | None:
        path = UPLOAD_DIR / filename
        return path if path.exists() else None

    def save_output(self, filename: str, data: bytes) -> str:
        path = OUTPUT_DIR / filename
        path.write_bytes(data)
        return str(path)

    def get_output_path(self, filename: str) -> Path | None:
        path = OUTPUT_DIR / filename
        return path if path.exists() else None

    def delete_upload(self, filename: str) -> bool:
        path = UPLOAD_DIR / filename
        if path.exists():
            path.unlink()
            return True
        return False

    def delete_output(self, filename: str) -> bool:
        path = OUTPUT_DIR / filename
        if path.exists():
            path.unlink()
            return True
        return False

    def list_outputs(self) -> list[str]:
        return [f.name for f in OUTPUT_DIR.iterdir() if f.is_file()]

    def get_storage_info(self) -> dict:
        try:
            usage = shutil.disk_usage(str(OUTPUT_DIR))
            free_gb = round(usage.free / 1024**3, 1)
            total_gb = round(usage.total / 1024**3, 1)
        except Exception:
            free_gb = -1
            total_gb = -1

        upload_count = sum(1 for _ in UPLOAD_DIR.iterdir() if _.is_file()) if UPLOAD_DIR.exists() else 0
        output_count = sum(1 for _ in OUTPUT_DIR.iterdir() if _.is_file()) if OUTPUT_DIR.exists() else 0

        return {
            "type": "local",
            "upload_dir": str(UPLOAD_DIR),
            "output_dir": str(OUTPUT_DIR),
            "upload_files": upload_count,
            "output_files": output_count,
            "disk_free_gb": free_gb,
            "disk_total_gb": total_gb,
        }


# Singleton
_storage: StorageAdapter | None = None


def get_storage() -> StorageAdapter:
    """Get the configured storage adapter.

    Uses S3 if STORAGE_BACKEND=s3, otherwise local filesystem.
    """
    global _storage
    if _storage is None:
        from app.config import STORAGE_BACKEND
        if STORAGE_BACKEND == "s3":
            try:
                from app.services.storage_s3 import S3StorageAdapter
                _storage = S3StorageAdapter()
                return _storage
            except Exception as e:
                logger.warning(f"STORAGE S3 backend unavailable ({e}), falling back to local")
        _storage = LocalStorageAdapter()
        logger.info("STORAGE Using local filesystem storage")
    return _storage

"""S3/MinIO storage adapter for multi-server deployments."""

import io
import logging
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import (
    OUTPUT_DIR,
    S3_ACCESS_KEY,
    S3_BUCKET_NAME,
    S3_ENDPOINT_URL,
    S3_REGION,
    S3_SECRET_KEY,
    UPLOAD_DIR,
)
from app.services.storage import StorageAdapter

logger = logging.getLogger("subtitle-generator")


class S3StorageAdapter(StorageAdapter):
    """S3/MinIO storage adapter. Files are stored in S3 and cached locally for processing."""

    def __init__(self):
        UPLOAD_DIR.mkdir(exist_ok=True)
        OUTPUT_DIR.mkdir(exist_ok=True)

        kwargs = {
            "service_name": "s3",
            "region_name": S3_REGION,
            "aws_access_key_id": S3_ACCESS_KEY,
            "aws_secret_access_key": S3_SECRET_KEY,
            "config": BotoConfig(signature_version="s3v4"),
        }
        if S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = S3_ENDPOINT_URL

        self._s3 = boto3.client(**kwargs)
        self._bucket = S3_BUCKET_NAME

        # Ensure bucket exists
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._s3.create_bucket(Bucket=self._bucket)
            logger.info(f"S3 Created bucket '{self._bucket}'")

        logger.info(f"S3 Storage initialized: bucket={self._bucket}")

    def _upload_key(self, filename: str) -> str:
        return f"uploads/{filename}"

    def _output_key(self, filename: str) -> str:
        return f"outputs/{filename}"

    def save_upload(self, filename: str, data: bytes) -> str:
        key = self._upload_key(filename)
        self._s3.upload_fileobj(io.BytesIO(data), self._bucket, key)
        # Also save locally for pipeline processing
        local_path = UPLOAD_DIR / filename
        local_path.write_bytes(data)
        return key

    def save_upload_from_path(self, filename: str, local_path: Path) -> str:
        """Upload a file from local path to S3."""
        key = self._upload_key(filename)
        self._s3.upload_file(str(local_path), self._bucket, key)
        return key

    def get_upload_path(self, filename: str) -> Path | None:
        """Get local path, downloading from S3 if needed."""
        local_path = UPLOAD_DIR / filename
        if local_path.exists():
            return local_path
        # Download from S3
        key = self._upload_key(filename)
        try:
            self._s3.download_file(self._bucket, key, str(local_path))
            return local_path
        except ClientError:
            return None

    def save_output(self, filename: str, data: bytes) -> str:
        key = self._output_key(filename)
        self._s3.upload_fileobj(io.BytesIO(data), self._bucket, key)
        # Also save locally for immediate serving
        local_path = OUTPUT_DIR / filename
        local_path.write_bytes(data)
        return key

    def save_output_from_path(self, filename: str, local_path: Path) -> str:
        """Upload an output file from local path to S3."""
        key = self._output_key(filename)
        self._s3.upload_file(str(local_path), self._bucket, key)
        return key

    def get_output_path(self, filename: str) -> Path | None:
        """Get local path, downloading from S3 if needed."""
        local_path = OUTPUT_DIR / filename
        if local_path.exists():
            return local_path
        key = self._output_key(filename)
        try:
            self._s3.download_file(self._bucket, key, str(local_path))
            return local_path
        except ClientError:
            return None

    def get_download_url(self, filename: str, expires_in: int = 3600) -> str | None:
        """Generate a pre-signed download URL for an output file."""
        key = self._output_key(filename)
        try:
            url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            return None

    def delete_upload(self, filename: str) -> bool:
        key = self._upload_key(filename)
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
        except ClientError:
            pass
        # Also delete local cache
        local_path = UPLOAD_DIR / filename
        if local_path.exists():
            local_path.unlink()
        return True

    def delete_output(self, filename: str) -> bool:
        key = self._output_key(filename)
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
        except ClientError:
            pass
        local_path = OUTPUT_DIR / filename
        if local_path.exists():
            local_path.unlink()
        return True

    def list_outputs(self) -> list[str]:
        result = []
        try:
            paginator = self._s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self._bucket, Prefix="outputs/"):
                for obj in page.get("Contents", []):
                    name = obj["Key"].removeprefix("outputs/")
                    if name:
                        result.append(name)
        except ClientError:
            pass
        return result

    def get_storage_info(self) -> dict:
        output_count = len(self.list_outputs())
        return {
            "type": "s3",
            "bucket": self._bucket,
            "endpoint": S3_ENDPOINT_URL or "AWS S3",
            "output_files": output_count,
        }

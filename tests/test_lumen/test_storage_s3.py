"""Phase Lumen L63 — S3 storage adapter tests.

Tests S3StorageAdapter: init bucket creation, upload/download,
output management, presigned URLs, delete, list, and storage info.
— Scout (QA Lead)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


# Mock boto3 and botocore before any app imports that reference them
if "botocore" not in sys.modules:
    _botocore_mock = MagicMock()

    class _MockClientError(Exception):
        """Mock botocore ClientError."""

        def __init__(self, error_response, operation_name):
            self.response = error_response
            self.operation_name = operation_name
            super().__init__(str(error_response))

    _botocore_mock.exceptions.ClientError = _MockClientError
    sys.modules["botocore"] = _botocore_mock
    sys.modules["botocore.exceptions"] = _botocore_mock.exceptions
    sys.modules["botocore.exceptions"].ClientError = _MockClientError
    sys.modules["botocore.config"] = MagicMock()

if "boto3" not in sys.modules:
    sys.modules["boto3"] = MagicMock()

from botocore.exceptions import ClientError


def _client_error(code="404", message="Not Found"):
    """Helper to build a botocore ClientError."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "HeadBucket",
    )


# ══════════════════════════════════════════════════════════════════════════════
# INIT
# ══════════════════════════════════════════════════════════════════════════════


class TestS3StorageAdapterInit:
    """Test S3StorageAdapter.__init__ bucket handling."""

    @patch("app.services.storage_s3.boto3")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    def test_head_bucket_succeeds_no_create(self, mock_output, mock_upload, mock_boto3):
        """When head_bucket succeeds, create_bucket is NOT called."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}

        from app.services.storage_s3 import S3StorageAdapter

        S3StorageAdapter()

        mock_client.head_bucket.assert_called_once()
        mock_client.create_bucket.assert_not_called()

    @patch("app.services.storage_s3.boto3")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    def test_head_bucket_fails_creates_bucket(self, mock_output, mock_upload, mock_boto3):
        """When head_bucket raises ClientError, create_bucket is called."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.side_effect = _client_error()

        from app.services.storage_s3 import S3StorageAdapter

        S3StorageAdapter()

        mock_client.create_bucket.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# SAVE & RETRIEVE UPLOADS
# ══════════════════════════════════════════════════════════════════════════════


class TestS3SaveAndRetrieve:
    """Test upload save/retrieve operations."""

    def _make_adapter(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}
        from app.services.storage_s3 import S3StorageAdapter

        adapter = S3StorageAdapter()
        return adapter, mock_client

    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_save_upload_calls_upload_fileobj(self, mock_boto3, mock_output, mock_upload):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_upload.__truediv__ = MagicMock(return_value=mock_local)

        key = adapter.save_upload("test.wav", b"audio data")

        assert key == "uploads/test.wav"
        mock_client.upload_fileobj.assert_called_once()
        args = mock_client.upload_fileobj.call_args
        assert args[0][2] == "uploads/test.wav"

    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_save_upload_from_path_calls_upload_file(self, mock_boto3, mock_output, mock_upload):
        adapter, mock_client = self._make_adapter(mock_boto3)

        key = adapter.save_upload_from_path("test.mp4", Path("/tmp/test.mp4"))

        assert key == "uploads/test.mp4"
        mock_client.upload_file.assert_called_once_with("/tmp/test.mp4", adapter._bucket, "uploads/test.mp4")

    @patch("app.services.storage_s3.UPLOAD_DIR")
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_upload_path_returns_local_when_exists(self, mock_boto3, mock_output, mock_upload_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = True
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_local)

        result = adapter.get_upload_path("test.wav")

        assert result == mock_local
        mock_client.download_file.assert_not_called()

    @patch("app.services.storage_s3.UPLOAD_DIR")
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_upload_path_downloads_from_s3_when_local_missing(self, mock_boto3, mock_output, mock_upload_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = False
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_local)

        result = adapter.get_upload_path("test.wav")

        mock_client.download_file.assert_called_once()
        assert result == mock_local

    @patch("app.services.storage_s3.UPLOAD_DIR")
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_upload_path_returns_none_on_client_error(self, mock_boto3, mock_output, mock_upload_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = False
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_local)
        mock_client.download_file.side_effect = _client_error()

        result = adapter.get_upload_path("test.wav")

        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestS3Output:
    """Test output save/retrieve and presigned URL generation."""

    def _make_adapter(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}
        from app.services.storage_s3 import S3StorageAdapter

        adapter = S3StorageAdapter()
        return adapter, mock_client

    @patch("app.services.storage_s3.OUTPUT_DIR")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_save_output_uploads_to_outputs_prefix(self, mock_boto3, mock_upload, mock_output_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_output_dir.__truediv__ = MagicMock(return_value=mock_local)

        key = adapter.save_output("result.srt", b"subtitle data")

        assert key == "outputs/result.srt"
        mock_client.upload_fileobj.assert_called_once()

    @patch("app.services.storage_s3.OUTPUT_DIR")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_output_path_returns_local_when_exists(self, mock_boto3, mock_upload, mock_output_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = True
        mock_output_dir.__truediv__ = MagicMock(return_value=mock_local)

        result = adapter.get_output_path("result.srt")

        assert result == mock_local
        mock_client.download_file.assert_not_called()

    @patch("app.services.storage_s3.OUTPUT_DIR")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_output_path_downloads_on_miss(self, mock_boto3, mock_upload, mock_output_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = False
        mock_output_dir.__truediv__ = MagicMock(return_value=mock_local)

        adapter.get_output_path("result.srt")

        mock_client.download_file.assert_called_once()

    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_download_url_generates_presigned_url(self, mock_boto3, mock_upload, mock_output):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_client.generate_presigned_url.return_value = "https://s3.example.com/signed"

        url = adapter.get_download_url("result.srt", expires_in=7200)

        assert url == "https://s3.example.com/signed"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": adapter._bucket, "Key": "outputs/result.srt"},
            ExpiresIn=7200,
        )

    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_download_url_returns_none_on_error(self, mock_boto3, mock_upload, mock_output):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_client.generate_presigned_url.side_effect = _client_error()

        url = adapter.get_download_url("result.srt")

        assert url is None


# ══════════════════════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════════════════════


class TestS3Delete:
    """Test delete operations."""

    def _make_adapter(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}
        from app.services.storage_s3 import S3StorageAdapter

        adapter = S3StorageAdapter()
        return adapter, mock_client

    @patch("app.services.storage_s3.UPLOAD_DIR")
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_delete_upload_calls_delete_object_and_local_unlink(self, mock_boto3, mock_output, mock_upload_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = True
        mock_upload_dir.__truediv__ = MagicMock(return_value=mock_local)

        result = adapter.delete_upload("test.wav")

        assert result is True
        mock_client.delete_object.assert_called_once_with(Bucket=adapter._bucket, Key="uploads/test.wav")
        mock_local.unlink.assert_called_once()

    @patch("app.services.storage_s3.OUTPUT_DIR")
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_delete_output_calls_delete_object_and_local_unlink(self, mock_boto3, mock_upload, mock_output_dir):
        adapter, mock_client = self._make_adapter(mock_boto3)
        mock_local = MagicMock()
        mock_local.exists.return_value = True
        mock_output_dir.__truediv__ = MagicMock(return_value=mock_local)

        result = adapter.delete_output("result.srt")

        assert result is True
        mock_client.delete_object.assert_called_once_with(Bucket=adapter._bucket, Key="outputs/result.srt")
        mock_local.unlink.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# LIST OUTPUTS & STORAGE INFO
# ══════════════════════════════════════════════════════════════════════════════


class TestS3ListOutputs:
    """Test list_outputs pagination and get_storage_info."""

    def _make_adapter(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}
        from app.services.storage_s3 import S3StorageAdapter

        adapter = S3StorageAdapter()
        return adapter, mock_client

    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_list_outputs_paginates_and_strips_prefix(self, mock_boto3, mock_upload, mock_output):
        adapter, mock_client = self._make_adapter(mock_boto3)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "outputs/file1.srt"}, {"Key": "outputs/file2.vtt"}]},
            {"Contents": [{"Key": "outputs/file3.json"}]},
        ]

        result = adapter.list_outputs()

        assert result == ["file1.srt", "file2.vtt", "file3.json"]

    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_list_outputs_returns_empty_on_client_error(self, mock_boto3, mock_upload, mock_output):
        adapter, mock_client = self._make_adapter(mock_boto3)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = _client_error()

        result = adapter.list_outputs()

        assert result == []

    @patch("app.services.storage_s3.S3_ENDPOINT_URL", "http://minio:9000")
    @patch("app.services.storage_s3.OUTPUT_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.UPLOAD_DIR", new_callable=lambda: MagicMock(spec=Path))
    @patch("app.services.storage_s3.boto3")
    def test_get_storage_info_returns_correct_dict(self, mock_boto3, mock_upload, mock_output):
        adapter, mock_client = self._make_adapter(mock_boto3)

        # Mock list_outputs to return 2 files
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "outputs/a.srt"}, {"Key": "outputs/b.srt"}]},
        ]

        info = adapter.get_storage_info()

        assert info["type"] == "s3"
        assert info["bucket"] == adapter._bucket
        assert info["output_files"] == 2
        assert info["endpoint"] == "http://minio:9000"

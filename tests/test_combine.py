"""Tests for the Combine feature — merge video + subtitle files."""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app import state

client = TestClient(app, base_url="https://testserver")


def _make_video_bytes():
    """Create minimal bytes that pass magic-bytes check as a video file."""
    # ftyp box header for MP4: 8 bytes size + 'ftyp' + brand
    return b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 1024


def _make_srt_content():
    return b"1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n2\n00:00:04,000 --> 00:00:06,000\nThis is a test\n"


def _make_vtt_content():
    return b"WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello world\n\n00:00:04.000 --> 00:00:06.000\nThis is a test\n"


class TestCombineValidation:
    """Test input validation for /combine endpoint."""

    def test_combine_rejects_non_video_extension(self):
        response = client.post(
            "/combine",
            files={
                "video": ("audio.mp3", BytesIO(b"\x00" * 2048), "audio/mpeg"),
                "subtitle": ("sub.srt", BytesIO(_make_srt_content()), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 400
        assert "video" in response.json()["detail"].lower()

    def test_combine_rejects_invalid_subtitle_extension(self):
        response = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                "subtitle": ("sub.txt", BytesIO(b"some text"), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 400
        assert "subtitle" in response.json()["detail"].lower()

    def test_combine_rejects_empty_subtitle(self):
        with patch("app.routes.combine.validate_magic_bytes", return_value=True):
            response = client.post(
                "/combine",
                files={
                    "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                    "subtitle": ("sub.srt", BytesIO(b""), "text/plain"),
                },
                data={"mode": "soft"},
            )
        assert response.status_code == 400

    def test_combine_rejects_invalid_srt_content(self):
        with patch("app.routes.combine.validate_magic_bytes", return_value=True):
            response = client.post(
                "/combine",
                files={
                    "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                    "subtitle": ("sub.srt", BytesIO(b"this is not a subtitle file"), "text/plain"),
                },
                data={"mode": "soft"},
            )
        assert response.status_code == 400
        assert "invalid subtitle" in response.json()["detail"].lower()

    def test_combine_rejects_invalid_vtt_content(self):
        with patch("app.routes.combine.validate_magic_bytes", return_value=True):
            response = client.post(
                "/combine",
                files={
                    "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                    "subtitle": ("sub.vtt", BytesIO(b"not a vtt file"), "text/plain"),
                },
                data={"mode": "soft"},
            )
        assert response.status_code == 400

    def test_combine_rejects_video_too_small(self):
        response = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4"),
                "subtitle": ("sub.srt", BytesIO(_make_srt_content()), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 400


class TestCombineEndpoint:
    """Test the /combine endpoint with valid inputs."""

    @patch("app.routes.combine.asyncio")
    @patch("app.routes.combine.validate_magic_bytes", return_value=True)
    @patch("app.routes.combine.create_event_queue")
    def test_combine_soft_returns_task_id(self, mock_queue, mock_magic, mock_asyncio):
        mock_asyncio.create_task = MagicMock()
        mock_asyncio.to_thread = MagicMock()

        response = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                "subtitle": ("sub.srt", BytesIO(_make_srt_content()), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["mode"] == "soft"
        assert "output" in data

        # Clean up task state
        task_id = data["task_id"]
        state.tasks.pop(task_id, None)

    @patch("app.routes.combine.asyncio")
    @patch("app.routes.combine.validate_magic_bytes", return_value=True)
    @patch("app.routes.combine.create_event_queue")
    def test_combine_hard_with_preset(self, mock_queue, mock_magic, mock_asyncio):
        mock_asyncio.create_task = MagicMock()
        mock_asyncio.to_thread = MagicMock()

        response = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                "subtitle": ("sub.srt", BytesIO(_make_srt_content()), "text/plain"),
            },
            data={"mode": "hard", "preset": "youtube_white"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "hard"

        state.tasks.pop(data["task_id"], None)

    @patch("app.routes.combine.asyncio")
    @patch("app.routes.combine.validate_magic_bytes", return_value=True)
    @patch("app.routes.combine.create_event_queue")
    def test_combine_vtt_accepted(self, mock_queue, mock_magic, mock_asyncio):
        mock_asyncio.create_task = MagicMock()
        mock_asyncio.to_thread = MagicMock()

        response = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(_make_video_bytes()), "video/mp4"),
                "subtitle": ("sub.vtt", BytesIO(_make_vtt_content()), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

        state.tasks.pop(data["task_id"], None)

    @patch("app.routes.combine.asyncio")
    @patch("app.routes.combine.validate_magic_bytes", return_value=True)
    @patch("app.routes.combine.create_event_queue")
    def test_combine_mkv_output_for_mkv_soft(self, mock_queue, mock_magic, mock_asyncio):
        mock_asyncio.create_task = MagicMock()
        mock_asyncio.to_thread = MagicMock()

        response = client.post(
            "/combine",
            files={
                "video": ("test.mkv", BytesIO(_make_video_bytes()), "video/x-matroska"),
                "subtitle": ("sub.srt", BytesIO(_make_srt_content()), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"].endswith(".mkv")

        state.tasks.pop(data["task_id"], None)


class TestCombineDownload:
    """Test the /combine/download endpoint."""

    def test_download_not_found_unknown_task(self):
        response = client.get("/combine/download/nonexistent-id")
        assert response.status_code == 404

    def test_download_no_combined_video(self):
        task_id = "test-combine-dl"
        state.tasks[task_id] = {"status": "done", "filename": "test.mp4"}
        try:
            response = client.get(f"/combine/download/{task_id}")
            assert response.status_code == 404
            assert "No combined video" in response.json()["detail"]
        finally:
            state.tasks.pop(task_id, None)

    def test_download_file_not_on_disk(self):
        task_id = "test-combine-dl2"
        state.tasks[task_id] = {
            "status": "done",
            "filename": "test.mp4",
            "combined_video": "nonexistent_file.mp4",
        }
        try:
            response = client.get(f"/combine/download/{task_id}")
            assert response.status_code == 404
        finally:
            state.tasks.pop(task_id, None)


class TestCombineStatus:
    """Test the /combine/status endpoint."""

    def test_status_not_found(self):
        response = client.get("/combine/status/nonexistent-id")
        assert response.status_code == 404

    def test_status_returns_task_info(self):
        task_id = "test-combine-status"
        state.tasks[task_id] = {
            "status": "combining",
            "percent": 50,
            "message": "Combining...",
            "mode": "soft",
        }
        try:
            response = client.get(f"/combine/status/{task_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "combining"
            assert data["percent"] == 50
            assert data["mode"] == "soft"
        finally:
            state.tasks.pop(task_id, None)


class TestSubtitleValidation:
    """Test subtitle file content validation."""

    def test_valid_srt_detection(self):
        from app.routes.combine import _validate_subtitle_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".srt", mode="w", delete=False) as f:
            f.write("1\n00:00:01,000 --> 00:00:03,000\nHello\n")
            f.flush()
            assert _validate_subtitle_file(Path(f.name)) is True
        Path(f.name).unlink(missing_ok=True)

    def test_valid_vtt_detection(self):
        from app.routes.combine import _validate_subtitle_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".vtt", mode="w", delete=False) as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nHello\n")
            f.flush()
            assert _validate_subtitle_file(Path(f.name)) is True
        Path(f.name).unlink(missing_ok=True)

    def test_invalid_srt_detection(self):
        from app.routes.combine import _validate_subtitle_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".srt", mode="w", delete=False) as f:
            f.write("This is just random text with no timestamps\n")
            f.flush()
            assert _validate_subtitle_file(Path(f.name)) is False
        Path(f.name).unlink(missing_ok=True)

    def test_invalid_vtt_detection(self):
        from app.routes.combine import _validate_subtitle_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".vtt", mode="w", delete=False) as f:
            f.write("Not a VTT file\n")
            f.flush()
            assert _validate_subtitle_file(Path(f.name)) is False
        Path(f.name).unlink(missing_ok=True)

    def test_empty_file_detection(self):
        from app.routes.combine import _validate_subtitle_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".srt", mode="w", delete=False) as f:
            f.write("")
            f.flush()
            assert _validate_subtitle_file(Path(f.name)) is False
        Path(f.name).unlink(missing_ok=True)

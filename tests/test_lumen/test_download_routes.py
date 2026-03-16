"""Phase Lumen L9 — Download route tests.

Tests GET /download/{task_id} for SRT, VTT, JSON formats:
content types, content-disposition headers, error handling,
format validation, and task status checks.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app

client = TestClient(app, base_url="https://testserver")


def _add_task(task_id=None, status="done", **kwargs):
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test_audio.wav",
        "session_id": "",
        "language_requested": "auto",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    task.update(kwargs)
    state.tasks[tid] = task
    return tid


def _cleanup(*task_ids):
    for tid in task_ids:
        state.tasks.pop(tid, None)
        # Clean up any files
        for ext in ("srt", "vtt", "json"):
            f = OUTPUT_DIR / f"{tid}.{ext}"
            if f.exists():
                f.unlink()


def _create_output_file(task_id: str, fmt: str, content: str):
    """Create an output file in the OUTPUT_DIR."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{task_id}.{fmt}"
    path.write_text(content, encoding="utf-8")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# SRT DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════


class TestSRTDownload:
    """Test SRT format downloads."""

    def test_download_srt_returns_200(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_download_srt_content_type(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "text/plain" in res.headers["content-type"]
        finally:
            _cleanup(tid)

    def test_download_srt_content_disposition(self):
        tid = _add_task(status="done", filename="my_video.mp4")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "my_video.srt" in res.headers.get("content-disposition", "")
        finally:
            _cleanup(tid)

    def test_download_srt_content(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "Hello" in res.text
        finally:
            _cleanup(tid)

    def test_download_srt_default_format(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nDefault\n")
        try:
            res = client.get(f"/download/{tid}")
            assert res.status_code == 200
            assert "Default" in res.text
        finally:
            _cleanup(tid)

    def test_download_srt_preserves_unicode(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\n\u65e5\u672c\u8a9e\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "\u65e5\u672c\u8a9e" in res.text
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# VTT DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════


class TestVTTDownload:
    """Test VTT format downloads."""

    def test_download_vtt_returns_200(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "vtt", "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_download_vtt_content_type(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "vtt", "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert "text/vtt" in res.headers["content-type"]
        finally:
            _cleanup(tid)

    def test_download_vtt_content_disposition(self):
        tid = _add_task(status="done", filename="lecture.mp4")
        _create_output_file(tid, "vtt", "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nHello\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert "lecture.vtt" in res.headers.get("content-disposition", "")
        finally:
            _cleanup(tid)

    def test_download_vtt_content(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "vtt", "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nVTT Test\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert "VTT Test" in res.text
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# JSON DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════


class TestJSONDownload:
    """Test JSON format downloads."""

    def test_download_json_returns_200(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", '[{"start": 0, "end": 1, "text": "Hello"}]')
        try:
            res = client.get(f"/download/{tid}?format=json")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_download_json_content_type(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", '[{"start": 0, "end": 1, "text": "Hello"}]')
        try:
            res = client.get(f"/download/{tid}?format=json")
            assert "application/json" in res.headers["content-type"]
        finally:
            _cleanup(tid)

    def test_download_json_content_disposition(self):
        tid = _add_task(status="done", filename="podcast.mp3")
        _create_output_file(tid, "json", '[{"start": 0, "end": 1, "text": "Hello"}]')
        try:
            res = client.get(f"/download/{tid}?format=json")
            assert "podcast.json" in res.headers.get("content-disposition", "")
        finally:
            _cleanup(tid)

    def test_download_json_valid(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", '[{"start": 0, "end": 1, "text": "Hello"}]')
        try:
            import json

            res = client.get(f"/download/{tid}?format=json")
            data = json.loads(res.text)
            assert isinstance(data, list)
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════


class TestDownloadErrors:
    """Test download error handling."""

    def test_download_nonexistent_task_returns_404(self):
        res = client.get("/download/nonexistent-task-id?format=srt")
        assert res.status_code == 404

    def test_download_active_task_returns_400(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_download_queued_task_returns_400(self):
        tid = _add_task(status="queued")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_download_error_task_returns_400(self):
        tid = _add_task(status="error")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_download_file_missing_returns_404(self):
        tid = _add_task(status="done")
        try:
            # Task exists but no file on disk
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_download_invalid_format_returns_422(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/download/{tid}?format=pdf")
            assert res.status_code == 422
        finally:
            _cleanup(tid)

    def test_download_error_detail_message(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "not ready" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_download_nonexistent_detail_message(self):
        res = client.get("/download/nonexistent?format=srt")
        assert "not found" in res.json()["detail"].lower()

    def test_download_missing_file_detail_message(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "not found" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# FILENAME DERIVATION
# ══════════════════════════════════════════════════════════════════════════════


class TestFilenameDerivation:
    """Test download filename is derived from original upload filename."""

    def test_srt_filename_from_original(self):
        tid = _add_task(status="done", filename="interview.mp4")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHi\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            cd = res.headers.get("content-disposition", "")
            assert "interview.srt" in cd
        finally:
            _cleanup(tid)

    def test_vtt_filename_from_original(self):
        tid = _add_task(status="done", filename="meeting.wav")
        _create_output_file(tid, "vtt", "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nHi\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            cd = res.headers.get("content-disposition", "")
            assert "meeting.vtt" in cd
        finally:
            _cleanup(tid)

    def test_json_filename_from_original(self):
        tid = _add_task(status="done", filename="webinar.mkv")
        _create_output_file(tid, "json", "[]")
        try:
            res = client.get(f"/download/{tid}?format=json")
            cd = res.headers.get("content-disposition", "")
            assert "webinar.json" in cd
        finally:
            _cleanup(tid)

    def test_filename_strips_extension(self):
        tid = _add_task(status="done", filename="complex.name.mp4")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHi\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            cd = res.headers.get("content-disposition", "")
            assert "complex.name.srt" in cd
        finally:
            _cleanup(tid)

    def test_attachment_header(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "srt", "1\n00:00:00,000 --> 00:00:01,000\nHi\n")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            cd = res.headers.get("content-disposition", "")
            assert "attachment" in cd
        finally:
            _cleanup(tid)

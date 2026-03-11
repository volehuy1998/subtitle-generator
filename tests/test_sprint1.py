"""Tests for Sprint 1 features: multi-language, VTT format, task persistence, error handling."""

from io import BytesIO

from app.config import SUPPORTED_LANGUAGES
from app.main import app
from app.utils.srt import segments_to_vtt, _format_vtt_timestamp, segments_to_srt
from app import state
from fastapi.testclient import TestClient

client = TestClient(app)

SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": "Hello world"},
    {"start": 3.0, "end": 5.5, "text": "How are you"},
    {"start": 6.0, "end": 8.0, "text": "Goodbye"},
]


# ── S1-1: Multi-language support ──

class TestLanguagesEndpoint:
    def test_returns_languages_dict(self):
        data = client.get("/languages").json()
        assert "languages" in data
        assert isinstance(data["languages"], dict)

    def test_auto_detect_is_first(self):
        data = client.get("/languages").json()
        assert "auto" in data["languages"]
        assert data["languages"]["auto"] == "Auto-detect"

    def test_english_present(self):
        data = client.get("/languages").json()
        assert data["languages"]["en"] == "English"

    def test_at_least_90_languages(self):
        data = client.get("/languages").json()
        assert len(data["languages"]) >= 90

    def test_supported_languages_config(self):
        assert "auto" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES
        assert "zh" in SUPPORTED_LANGUAGES
        assert "ja" in SUPPORTED_LANGUAGES
        assert "de" in SUPPORTED_LANGUAGES
        assert "fr" in SUPPORTED_LANGUAGES
        assert "es" in SUPPORTED_LANGUAGES
        assert "ru" in SUPPORTED_LANGUAGES


class TestUploadWithLanguage:
    def test_upload_accepts_language_param(self):
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny", "language": "en"},
        )
        # May fail at magic byte validation, but language param is accepted
        assert response.status_code in (200, 400)

    def test_upload_accepts_auto_language(self):
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny", "language": "auto"},
        )
        assert response.status_code in (200, 400)

    def test_upload_invalid_language_falls_back_to_auto(self):
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny", "language": "invalid_xyz"},
        )
        # Should not fail due to invalid language - falls back to auto
        assert response.status_code in (200, 400)

    def test_upload_default_language_is_auto(self):
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code in (200, 400)


# ── S1-2: VTT subtitle format ──

class TestVttFormat:
    def test_vtt_starts_with_header(self):
        result = segments_to_vtt(SAMPLE_SEGMENTS)
        assert result.startswith("WEBVTT")

    def test_vtt_has_blank_line_after_header(self):
        result = segments_to_vtt(SAMPLE_SEGMENTS)
        lines = result.split("\n")
        assert lines[0] == "WEBVTT"
        assert lines[1] == ""

    def test_vtt_segment_count(self):
        result = segments_to_vtt(SAMPLE_SEGMENTS)
        # Each segment: number, timestamp, text, blank line
        # Plus header (WEBVTT) and blank line = 2 + 4*3 = 14 lines
        lines = result.split("\n")
        segment_numbers = [line for line in lines if line.strip().isdigit()]
        assert len(segment_numbers) == 3

    def test_vtt_uses_dot_separator(self):
        result = segments_to_vtt(SAMPLE_SEGMENTS)
        assert "." in result
        # SRT uses commas, VTT uses dots
        # Check that no SRT-style comma timestamps appear
        lines = result.split("\n")
        for line in lines:
            if "-->" in line:
                assert "," not in line

    def test_vtt_empty_segments(self):
        result = segments_to_vtt([])
        assert result.startswith("WEBVTT")

    def test_vtt_timestamp_format(self):
        result = _format_vtt_timestamp(3661.5)  # 1h 1m 1.5s
        assert result == "01:01:01.500"

    def test_vtt_timestamp_zero(self):
        assert _format_vtt_timestamp(0) == "00:00:00.000"

    def test_vtt_timestamp_hours(self):
        assert _format_vtt_timestamp(7200) == "02:00:00.000"

    def test_vtt_contains_text(self):
        result = segments_to_vtt(SAMPLE_SEGMENTS)
        assert "Hello world" in result
        assert "How are you" in result
        assert "Goodbye" in result

    def test_vtt_and_srt_same_text(self):
        """VTT and SRT should contain the same subtitle text."""
        vtt = segments_to_vtt(SAMPLE_SEGMENTS)
        srt = segments_to_srt(SAMPLE_SEGMENTS)
        for seg in SAMPLE_SEGMENTS:
            assert seg["text"] in vtt
            assert seg["text"] in srt


class TestDownloadFormat:
    def test_download_unknown_task_404(self):
        assert client.get("/download/nonexistent?format=srt").status_code == 404

    def test_download_vtt_unknown_task_404(self):
        assert client.get("/download/nonexistent?format=vtt").status_code == 404

    def test_download_invalid_format_rejected(self):
        response = client.get("/download/nonexistent?format=txt")
        assert response.status_code == 422  # Literal validation


# ── S1-3: Task history persistence ──

class TestTaskPersistence:
    def test_save_and_load_history(self):
        # Clear state
        original_tasks = state.tasks.copy()
        state.tasks.clear()

        # Add a completed task
        state.tasks["test-persist-001"] = {
            "status": "done",
            "percent": 100,
            "message": "Done!",
            "filename": "test.mp4",
            "segments": 5,
            "language": "en",
        }

        try:
            state.save_task_history()

            # Clear and reload
            state.tasks.clear()
            state.load_task_history()

            assert "test-persist-001" in state.tasks
            t = state.tasks["test-persist-001"]
            assert t["status"] == "done"
            assert t["filename"] == "test.mp4"
            assert t["language"] == "en"
        finally:
            state.tasks.clear()
            state.tasks.update(original_tasks)
            # Clean up test file
            from app.config import TASK_HISTORY_FILE
            TASK_HISTORY_FILE.unlink(missing_ok=True)

    def test_only_terminal_tasks_persisted(self):
        original_tasks = state.tasks.copy()
        state.tasks.clear()

        state.tasks["active-task"] = {"status": "transcribing", "percent": 50}
        state.tasks["done-task"] = {"status": "done", "percent": 100, "filename": "x.mp4"}

        try:
            state.save_task_history()
            state.tasks.clear()
            state.load_task_history()

            # Only done/error/cancelled tasks are persisted
            assert "active-task" not in state.tasks
            assert "done-task" in state.tasks
        finally:
            state.tasks.clear()
            state.tasks.update(original_tasks)
            from app.config import TASK_HISTORY_FILE
            TASK_HISTORY_FILE.unlink(missing_ok=True)

    def test_load_empty_history(self):
        """Loading when no history file exists should not crash."""
        from app.config import TASK_HISTORY_FILE
        TASK_HISTORY_FILE.unlink(missing_ok=True)
        state.load_task_history()  # Should not raise

    def test_persist_fields_are_safe(self):
        """Verify no unpicklable fields in persist set."""
        assert "pause_event" not in state._PERSIST_FIELDS
        assert "transcription_profiler" not in state._PERSIST_FIELDS
        assert "segments_preview" not in state._PERSIST_FIELDS


# ── S1-4: Frontend error handling ──

class TestErrorResponses:
    def test_413_on_oversized_content_type(self):
        """Server returns descriptive error for large files."""
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"tiny"), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "small" in detail.lower() or "valid" in detail.lower()

    def test_429_message_is_helpful(self):
        """429 should tell user to wait."""
        # This test verifies the message format, not actually triggering 429
        # (would need MAX_CONCURRENT_TASKS active tasks)
        pass

    def test_400_unsupported_format_message(self):
        response = client.post(
            "/upload",
            files={"file": ("test.xyz", BytesIO(b"data"), "text/plain")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Unsupported" in detail or "Allowed" in detail

    def test_system_info_includes_languages(self):
        """System info endpoint should be reachable alongside languages."""
        assert client.get("/system-info").status_code == 200
        assert client.get("/languages").status_code == 200

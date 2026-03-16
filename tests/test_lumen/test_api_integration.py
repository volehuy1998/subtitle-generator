"""Phase Lumen L8 — API integration and utility tests.

Tests download endpoints, subtitle editing, formatting utilities,
model management, feedback, and miscellaneous API endpoints.
— Scout (QA Lead)
"""

import struct
import uuid
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app
from app.utils.formatting import format_bytes, format_time_display, format_time_short, format_timestamp

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT_BYTES UTILITY
# ══════════════════════════════════════════════════════════════════════════════


class TestFormatBytes:
    """Test format_bytes utility function."""

    def test_bytes(self):
        assert format_bytes(500) == "500 B"

    def test_zero_bytes(self):
        assert format_bytes(0) == "0 B"

    def test_one_byte(self):
        assert format_bytes(1) == "1 B"

    def test_kilobytes(self):
        result = format_bytes(2048)
        assert "KB" in result

    def test_megabytes(self):
        result = format_bytes(5 * 1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = format_bytes(2 * 1024 * 1024 * 1024)
        assert "GB" in result

    def test_boundary_kb(self):
        assert "B" in format_bytes(1023)
        assert "KB" in format_bytes(1024)

    def test_boundary_mb(self):
        assert "KB" in format_bytes(1024 * 1024 - 1)
        assert "MB" in format_bytes(1024 * 1024)

    def test_boundary_gb(self):
        assert "MB" in format_bytes(1024 * 1024 * 1024 - 1)
        assert "GB" in format_bytes(1024 * 1024 * 1024)


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT_TIME_DISPLAY UTILITY
# ══════════════════════════════════════════════════════════════════════════════


class TestFormatTimeDisplay:
    """Test format_time_display utility."""

    def test_negative_time(self):
        assert format_time_display(-1) == "calculating..."

    def test_sub_second(self):
        assert format_time_display(0.5) == "<1s"

    def test_one_second(self):
        assert format_time_display(1) == "1s"

    def test_seconds(self):
        assert format_time_display(30) == "30s"

    def test_one_minute(self):
        result = format_time_display(60)
        assert "m" in result

    def test_minutes_seconds(self):
        result = format_time_display(90)
        assert "1m" in result
        assert "30s" in result

    def test_one_hour(self):
        result = format_time_display(3600)
        assert "1h" in result

    def test_hours_minutes(self):
        result = format_time_display(3660)
        assert "h" in result
        assert "m" in result

    def test_zero(self):
        assert format_time_display(0) == "<1s"


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT_TIME_SHORT UTILITY
# ══════════════════════════════════════════════════════════════════════════════


class TestFormatTimeShort:
    """Test format_time_short utility."""

    def test_zero(self):
        result = format_time_short(0)
        assert "0:" in result

    def test_seconds(self):
        result = format_time_short(30.5)
        assert "0:" in result
        assert "30" in result

    def test_minutes(self):
        result = format_time_short(125.0)
        assert "2:" in result


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT_TIMESTAMP UTILITY (extended)
# ══════════════════════════════════════════════════════════════════════════════


class TestFormatTimestampExtended:
    """Extended tests for format_timestamp."""

    def test_exactly_one_hour(self):
        assert format_timestamp(3600.0) == "01:00:00,000"

    def test_max_reasonable_time(self):
        ts = format_timestamp(359999.999)
        assert ts.startswith("99:")

    def test_fractional_seconds(self):
        ts = format_timestamp(0.123)
        assert "00:00:00,123" == ts

    def test_59_seconds(self):
        ts = format_timestamp(59.0)
        assert ts == "00:00:59,000"

    def test_59_minutes(self):
        ts = format_timestamp(3540.0)
        assert ts == "00:59:00,000"


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestDownloadEndpoint:
    """Test GET /download/{task_id}."""

    def test_download_unknown_task(self):
        res = client.get("/download/nonexistent-task?format=srt")
        assert res.status_code == 404

    def test_download_not_done_task(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "transcribing", "filename": "t.wav", "session_id": ""}
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 400
        finally:
            state.tasks.pop(tid, None)

    def test_download_done_but_no_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "filename": "t.wav", "session_id": ""}
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 404
        finally:
            state.tasks.pop(tid, None)

    def test_download_with_srt_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "filename": "test.wav", "session_id": ""}
        srt_path = OUTPUT_DIR / f"{tid}.srt"
        srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n", encoding="utf-8")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
            assert "Hello" in res.text
        finally:
            state.tasks.pop(tid, None)
            srt_path.unlink(missing_ok=True)

    def test_download_with_vtt_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "filename": "test.wav", "session_id": ""}
        vtt_path = OUTPUT_DIR / f"{tid}.vtt"
        vtt_path.write_text("WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nHello VTT\n\n", encoding="utf-8")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert res.status_code == 200
            assert "Hello VTT" in res.text
        finally:
            state.tasks.pop(tid, None)
            vtt_path.unlink(missing_ok=True)

    def test_download_with_json_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "filename": "test.wav", "session_id": ""}
        json_path = OUTPUT_DIR / f"{tid}.json"
        json_path.write_text('[{"start": 0, "end": 1, "text": "JSON test"}]', encoding="utf-8")
        try:
            res = client.get(f"/download/{tid}?format=json")
            assert res.status_code == 200
        finally:
            state.tasks.pop(tid, None)
            json_path.unlink(missing_ok=True)

    def test_download_content_disposition(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "filename": "myaudio.wav", "session_id": ""}
        srt_path = OUTPUT_DIR / f"{tid}.srt"
        srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nTest\n\n", encoding="utf-8")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "content-disposition" in {k.lower() for k in res.headers.keys()}
            assert "myaudio.srt" in res.headers.get("content-disposition", "")
        finally:
            state.tasks.pop(tid, None)
            srt_path.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# SUBTITLES ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestSubtitlesEndpoint:
    """Test GET/PUT /subtitles/{task_id}."""

    def test_get_subtitles_unknown_task(self):
        res = client.get("/subtitles/nonexistent-task")
        assert res.status_code == 404

    def test_get_subtitles_not_done(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "transcribing"}
        try:
            res = client.get(f"/subtitles/{tid}")
            assert res.status_code == 400
        finally:
            state.tasks.pop(tid, None)

    def test_get_subtitles_no_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done"}
        try:
            res = client.get(f"/subtitles/{tid}")
            assert res.status_code == 404
        finally:
            state.tasks.pop(tid, None)

    def test_get_subtitles_with_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done"}
        srt_path = OUTPUT_DIR / f"{tid}.srt"
        srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n\n", encoding="utf-8")
        try:
            res = client.get(f"/subtitles/{tid}")
            assert res.status_code == 200
            data = res.json()
            assert "segments" in data
            assert len(data["segments"]) == 1
        finally:
            state.tasks.pop(tid, None)
            srt_path.unlink(missing_ok=True)

    def test_put_subtitles_unknown_task(self):
        res = client.put("/subtitles/nonexistent", json={"segments": []})
        assert res.status_code == 404

    def test_put_subtitles_not_done(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "transcribing"}
        try:
            res = client.put(f"/subtitles/{tid}", json={"segments": []})
            assert res.status_code == 400
        finally:
            state.tasks.pop(tid, None)

    def test_put_subtitles_updates_file(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "done", "segments": 0}
        try:
            segments = [{"start": 0.0, "end": 1.0, "text": "Updated text"}]
            res = client.put(f"/subtitles/{tid}", json={"segments": segments})
            assert res.status_code == 200
            assert res.json()["segments"] == 1
            # Verify SRT file was created
            srt_path = OUTPUT_DIR / f"{tid}.srt"
            assert srt_path.exists()
            content = srt_path.read_text()
            assert "Updated text" in content
        finally:
            state.tasks.pop(tid, None)
            (OUTPUT_DIR / f"{tid}.srt").unlink(missing_ok=True)
            (OUTPUT_DIR / f"{tid}.vtt").unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# FEEDBACK ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestFeedbackEndpoint:
    """Test POST /feedback."""

    def test_feedback_submission(self):
        res = client.post("/feedback", json={"rating": 5, "comment": "Great!"})
        assert res.status_code == 200

    def test_feedback_with_rating_only(self):
        res = client.post("/feedback", json={"rating": 3})
        assert res.status_code == 200

    def test_feedback_response_message(self):
        res = client.post("/feedback", json={"rating": 4, "comment": "Good"})
        data = res.json()
        assert "message" in data


# ══════════════════════════════════════════════════════════════════════════════
# MODEL MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════


class TestModelManagement:
    """Test model management functions."""

    def test_get_compute_type_cpu(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cpu", "tiny") == "int8"
        assert get_compute_type("cpu", "large") == "int8"

    def test_get_compute_type_gpu_small(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "tiny") == "float16"
        assert get_compute_type("cuda", "base") == "float16"

    def test_get_compute_type_gpu_large(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "large") == "int8_float16"
        assert get_compute_type("cuda", "medium") == "int8_float16"

    def test_get_model_readiness(self):
        from app.services.model_manager import get_model_readiness

        readiness = get_model_readiness()
        assert isinstance(readiness, dict)
        for size in ["tiny", "base", "small", "medium", "large"]:
            assert size in readiness

    def test_model_readiness_status_values(self):
        from app.services.model_manager import get_model_readiness

        readiness = get_model_readiness()
        for size, info in readiness.items():
            assert info["status"] in ("ready", "loading", "not_loaded")


# ══════════════════════════════════════════════════════════════════════════════
# OPENAPI / DOCS
# ══════════════════════════════════════════════════════════════════════════════


class TestDocsEndpoints:
    """Test API documentation endpoints."""

    def test_openapi_json(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "paths" in data
        assert "info" in data

    def test_openapi_title(self):
        data = client.get("/openapi.json").json()
        assert data["info"]["title"] == "Subtitle Generator"

    def test_openapi_has_upload_path(self):
        data = client.get("/openapi.json").json()
        assert "/upload" in data["paths"]

    def test_openapi_has_health_path(self):
        data = client.get("/openapi.json").json()
        assert "/health" in data["paths"]

    def test_openapi_has_tasks_path(self):
        data = client.get("/openapi.json").json()
        assert "/tasks" in data["paths"]

    def test_swagger_ui(self):
        res = client.get("/docs")
        assert res.status_code == 200

    def test_redoc_ui(self):
        res = client.get("/redoc")
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# STATIC PAGES
# ══════════════════════════════════════════════════════════════════════════════


class TestStaticPages:
    """Test static page endpoints."""

    def test_home_page(self):
        res = client.get("/")
        assert res.status_code == 200

    def test_about_page(self):
        res = client.get("/about")
        assert res.status_code == 200

    def test_contact_page(self):
        res = client.get("/contact")
        assert res.status_code == 200

    def test_security_page(self):
        res = client.get("/security")
        assert res.status_code == 200

    def test_status_page(self):
        res = client.get("/status")
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# GPU INFO
# ══════════════════════════════════════════════════════════════════════════════


class TestGPUInfo:
    """Test GPU-related functions."""

    def test_get_system_info(self):
        from app.services.gpu import get_system_info

        info = get_system_info()
        assert "cuda_available" in info
        assert "auto_model" in info

    def test_auto_select_model(self):
        from app.services.gpu import auto_select_model

        model = auto_select_model()
        assert model in ["tiny", "base", "small", "medium", "large"]

    def test_check_vram_no_gpu(self):
        from app.services.gpu import check_vram_for_model

        result = check_vram_for_model("tiny")
        assert "fits" in result

    def test_get_gpu_memory_usage(self):
        from app.services.gpu import get_gpu_memory_usage

        result = get_gpu_memory_usage()
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════════════════════
# STATE MODULE
# ══════════════════════════════════════════════════════════════════════════════


class TestStateModule:
    """Test app state module."""

    def test_tasks_is_dict(self):
        assert isinstance(state.tasks, dict)

    def test_loaded_models_exists(self):
        assert hasattr(state, "loaded_models")

    def test_model_lock_exists(self):
        assert hasattr(state, "model_lock")

    def test_task_event_queues_exists(self):
        assert hasattr(state, "task_event_queues")

    def test_system_critical_exists(self):
        assert hasattr(state, "system_critical")

    def test_shutting_down_exists(self):
        assert hasattr(state, "shutting_down")

    def test_model_preload_exists(self):
        assert hasattr(state, "model_preload")

    def test_translation_models_exists(self):
        assert hasattr(state, "translation_models")

    def test_translation_model_lock_exists(self):
        assert hasattr(state, "translation_model_lock")


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG MODULE
# ══════════════════════════════════════════════════════════════════════════════


class TestConfigModule:
    """Test config module values."""

    def test_allowed_extensions(self):
        from app.config import ALLOWED_EXTENSIONS

        assert ".wav" in ALLOWED_EXTENSIONS
        assert ".mp3" in ALLOWED_EXTENSIONS
        assert ".mp4" in ALLOWED_EXTENSIONS

    def test_max_file_size(self):
        from app.config import MAX_FILE_SIZE

        assert MAX_FILE_SIZE == 2 * 1024 * 1024 * 1024

    def test_min_file_size(self):
        from app.config import MIN_FILE_SIZE

        assert MIN_FILE_SIZE == 1024

    def test_valid_models(self):
        from app.config import VALID_MODELS

        assert "tiny" in VALID_MODELS
        assert "base" in VALID_MODELS
        assert "small" in VALID_MODELS
        assert "medium" in VALID_MODELS
        assert "large" in VALID_MODELS

    def test_supported_languages_has_english(self):
        from app.config import SUPPORTED_LANGUAGES

        assert "en" in SUPPORTED_LANGUAGES

    def test_supported_languages_has_auto(self):
        from app.config import SUPPORTED_LANGUAGES

        assert "auto" in SUPPORTED_LANGUAGES

    def test_upload_dir_exists(self):
        from app.config import UPLOAD_DIR

        assert UPLOAD_DIR.exists()

    def test_output_dir_exists(self):
        from app.config import OUTPUT_DIR

        assert OUTPUT_DIR.exists()

    def test_video_extensions(self):
        from app.config import VIDEO_EXTENSIONS

        assert ".mp4" in VIDEO_EXTENSIONS
        assert ".mkv" in VIDEO_EXTENSIONS

    def test_audio_only_extensions(self):
        from app.config import AUDIO_ONLY_EXTENSIONS

        assert ".wav" in AUDIO_ONLY_EXTENSIONS
        assert ".mp3" in AUDIO_ONLY_EXTENSIONS

    def test_max_concurrent_tasks_positive(self):
        from app.config import MAX_CONCURRENT_TASKS

        assert MAX_CONCURRENT_TASKS > 0

    def test_translation_batch_size(self):
        from app.config import TRANSLATION_BATCH_SIZE

        assert TRANSLATION_BATCH_SIZE == 50

    def test_role_default(self):
        from app.config import ROLE

        assert ROLE in ("standalone", "web", "worker")

    def test_environment_default(self):
        from app.config import ENVIRONMENT

        assert ENVIRONMENT in ("dev", "prod")

    def test_subtitle_extensions(self):
        from app.config import ALLOWED_SUBTITLE_EXTENSIONS

        assert ".srt" in ALLOWED_SUBTITLE_EXTENSIONS
        assert ".vtt" in ALLOWED_SUBTITLE_EXTENSIONS

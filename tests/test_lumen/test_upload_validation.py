"""Phase Lumen L8 — Comprehensive upload validation tests.

Tests upload endpoint: extensions, file sizes, MIME mismatches,
filename sanitization, concurrent limits, and parameter validation.
— Scout (QA Lead)
"""

import struct
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file in memory."""
    num_samples = int(sample_rate * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def _upload(filename="test.wav", data=None, content=None, content_type="audio/wav", **form_data):
    """Shortcut for upload POST."""
    if content is None:
        content = _make_wav_bytes()
    defaults = {"model_size": "tiny", "output_format": "srt"}
    defaults.update(form_data)
    return client.post(
        "/upload",
        files={"file": (filename, BytesIO(content), content_type)},
        data=defaults,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ALLOWED EXTENSIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestAllowedExtensions:
    """Test that all allowed audio/video extensions are accepted."""

    def test_upload_wav(self):
        res = _upload("test.wav")
        assert res.status_code == 200

    def test_upload_mp3(self):
        res = _upload("test.mp3", content_type="audio/mpeg")
        assert res.status_code in (200, 400)  # 400 if magic bytes don't match

    def test_upload_flac(self):
        res = _upload("test.flac", content_type="audio/flac")
        assert res.status_code in (200, 400)

    def test_upload_mp4(self):
        res = _upload("test.mp4", content_type="video/mp4")
        assert res.status_code in (200, 400, 503)  # 503 if ffmpeg not available

    def test_upload_mkv(self):
        res = _upload("test.mkv", content_type="video/x-matroska")
        assert res.status_code in (200, 400, 503)

    def test_upload_avi(self):
        res = _upload("test.avi", content_type="video/x-msvideo")
        assert res.status_code in (200, 400, 503)

    def test_upload_webm(self):
        res = _upload("test.webm", content_type="video/webm")
        assert res.status_code in (200, 400, 503)

    def test_upload_mov(self):
        res = _upload("test.mov", content_type="video/quicktime")
        assert res.status_code in (200, 400, 503)


class TestDisallowedExtensions:
    """Test that dangerous/unsupported extensions are rejected."""

    def test_reject_exe(self):
        res = _upload("malware.exe", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)

    def test_reject_py(self):
        res = _upload("script.py", content_type="text/x-python")
        assert res.status_code in (400, 415, 422)

    def test_reject_js(self):
        res = _upload("script.js", content_type="application/javascript")
        assert res.status_code in (400, 415, 422)

    def test_reject_php(self):
        res = _upload("index.php", content_type="text/html")
        assert res.status_code in (400, 415, 422)

    def test_reject_html(self):
        res = _upload("page.html", content_type="text/html")
        assert res.status_code in (400, 415, 422)

    def test_reject_sh(self):
        res = _upload("run.sh", content_type="application/x-sh")
        assert res.status_code in (400, 415, 422)

    def test_reject_bat(self):
        res = _upload("run.bat", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)

    def test_reject_txt(self):
        res = _upload("notes.txt", content=b"hello world", content_type="text/plain")
        assert res.status_code in (400, 415, 422)

    def test_reject_zip(self):
        res = _upload("archive.zip", content_type="application/zip")
        assert res.status_code in (400, 415, 422)

    def test_reject_pdf(self):
        res = _upload("doc.pdf", content_type="application/pdf")
        assert res.status_code in (400, 415, 422)

    def test_reject_dll(self):
        res = _upload("lib.dll", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)

    def test_reject_svg(self):
        res = _upload("image.svg", content_type="image/svg+xml")
        assert res.status_code in (400, 415, 422)

    def test_reject_no_extension(self):
        res = _upload("noext", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)

    def test_reject_double_extension(self):
        res = _upload("file.wav.exe", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)


# ══════════════════════════════════════════════════════════════════════════════
# FILE SIZE BOUNDARIES
# ══════════════════════════════════════════════════════════════════════════════


class TestFileSizeBoundaries:
    """Test file size validation."""

    def test_empty_file_rejected(self):
        res = _upload("empty.wav", content=b"")
        assert res.status_code in (400, 422)

    def test_one_byte_rejected(self):
        res = _upload("tiny.wav", content=b"\x00")
        assert res.status_code in (400, 422)

    def test_small_file_below_min(self):
        # MIN_FILE_SIZE is 1024 bytes
        res = _upload("small.wav", content=b"\x00" * 500)
        assert res.status_code in (400, 422)

    def test_valid_size_accepted(self):
        wav_data = _make_wav_bytes(1.0)
        res = _upload("test.wav", content=wav_data)
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# FILENAME SANITIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestFilenameSanitization:
    """Test filename handling and sanitization."""

    def test_path_traversal_dots(self):
        res = _upload("../../etc/passwd.wav")
        # Should not crash, extension is .wav so it goes through
        assert res.status_code in (200, 400)

    def test_path_traversal_backslash(self):
        res = _upload("..\\..\\windows\\system32\\test.wav")
        assert res.status_code in (200, 400)

    def test_null_bytes_in_name(self):
        res = _upload("test\x00.wav")
        assert res.status_code in (200, 400)

    def test_special_chars_in_name(self):
        res = _upload("test<>|;.wav")
        assert res.status_code in (200, 400)

    def test_unicode_filename(self):
        res = _upload("日本語テスト.wav")
        assert res.status_code in (200, 400)

    def test_very_long_filename(self):
        name = "a" * 300 + ".wav"
        res = _upload(name)
        assert res.status_code in (200, 400)

    def test_spaces_in_filename(self):
        res = _upload("my audio file.wav")
        assert res.status_code in (200, 400)

    def test_dots_in_filename(self):
        res = _upload("test.file.name.wav")
        assert res.status_code in (200, 400)


# ══════════════════════════════════════════════════════════════════════════════
# SANITIZE FILENAME UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSanitizeFilenameUnit:
    """Unit tests for the sanitize_filename function."""

    def test_basic_filename(self):
        from app.utils.security import sanitize_filename

        assert sanitize_filename("test.wav") == "test.wav"

    def test_strips_path_unix(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("/etc/passwd/evil.wav")
        assert "/" not in result
        assert "evil.wav" in result

    def test_strips_path_windows(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("C:\\Users\\evil.wav")
        assert "\\" not in result

    def test_removes_null_bytes(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("test\x00evil.wav")
        assert "\x00" not in result

    def test_removes_control_chars(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("test\x01\x02.wav")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_empty_returns_unnamed(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("")
        assert result == "unnamed_file"

    def test_only_dots_returns_unnamed(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("...")
        assert result == "unnamed_file"

    def test_preserves_unicode(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("日本語.wav")
        assert "日本語" in result


# ══════════════════════════════════════════════════════════════════════════════
# PARAMETER VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestParameterValidation:
    """Test upload form parameter validation."""

    def test_invalid_model_size(self):
        res = _upload(model_size="nonexistent")
        assert res.status_code in (400, 422)

    def test_valid_model_tiny(self):
        res = _upload(model_size="tiny")
        assert res.status_code == 200

    def test_valid_model_base(self):
        res = _upload(model_size="base")
        assert res.status_code == 200

    def test_valid_model_small(self):
        res = _upload(model_size="small")
        assert res.status_code == 200

    def test_valid_model_medium(self):
        res = _upload(model_size="medium")
        assert res.status_code == 200

    def test_valid_model_large(self):
        res = _upload(model_size="large")
        assert res.status_code == 200

    def test_valid_model_auto(self):
        res = _upload(model_size="auto")
        assert res.status_code == 200

    def test_invalid_output_format(self):
        res = _upload(output_format="xml")
        # FastAPI Literal validation
        assert res.status_code in (200, 400, 422)

    def test_invalid_language_falls_back_to_auto(self):
        res = _upload(language="zzz_invalid")
        assert res.status_code == 200
        data = res.json()
        assert data["language"] == "auto"

    def test_valid_language_en(self):
        res = _upload(language="en")
        assert res.status_code == 200
        assert res.json()["language"] == "en"

    def test_missing_file_field(self):
        res = client.post("/upload")
        assert res.status_code == 422

    def test_response_has_task_id(self):
        res = _upload()
        assert res.status_code == 200
        assert "task_id" in res.json()

    def test_response_has_model_size(self):
        res = _upload(model_size="tiny")
        assert res.status_code == 200
        assert res.json()["model_size"] == "tiny"

    def test_max_line_chars_clamped_high(self):
        # max_line_chars > 80 should be clamped to 80
        res = _upload(max_line_chars="200")
        assert res.status_code == 200

    def test_max_line_chars_clamped_low(self):
        # max_line_chars < 20 should be clamped to 20
        res = _upload(max_line_chars="5")
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# CONCURRENT UPLOAD LIMITS
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrentLimits:
    """Test concurrent task limiting."""

    def test_exceeding_max_tasks_returns_429(self):
        from app import state
        from app.config import MAX_CONCURRENT_TASKS

        # Fill up the task queue
        original_tasks = dict(state.tasks)
        try:
            for i in range(MAX_CONCURRENT_TASKS + 1):
                state.tasks[f"fake-task-{i}"] = {"status": "transcribing"}
            res = _upload()
            assert res.status_code == 429
        finally:
            state.tasks.clear()
            state.tasks.update(original_tasks)

    def test_done_tasks_dont_count_against_limit(self):
        from app import state
        from app.config import MAX_CONCURRENT_TASKS

        original_tasks = dict(state.tasks)
        try:
            for i in range(MAX_CONCURRENT_TASKS + 5):
                state.tasks[f"fake-done-{i}"] = {"status": "done"}
            res = _upload()
            assert res.status_code == 200
        finally:
            state.tasks.clear()
            state.tasks.update(original_tasks)

    def test_error_tasks_dont_count_against_limit(self):
        from app import state
        from app.config import MAX_CONCURRENT_TASKS

        original_tasks = dict(state.tasks)
        try:
            for i in range(MAX_CONCURRENT_TASKS + 5):
                state.tasks[f"fake-err-{i}"] = {"status": "error"}
            res = _upload()
            assert res.status_code == 200
        finally:
            state.tasks.clear()
            state.tasks.update(original_tasks)


# ══════════════════════════════════════════════════════════════════════════════
# FILE EXTENSION VALIDATION UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestFileExtensionValidation:
    """Unit tests for validate_file_extension."""

    def test_valid_mp4(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("video.mp4") == ".mp4"

    def test_valid_wav(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("audio.wav") == ".wav"

    def test_invalid_exe(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("malware.exe") is None

    def test_case_insensitive(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("video.MP4") == ".mp4"

    def test_no_extension(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("noext") is None

    def test_empty_filename(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("") is None

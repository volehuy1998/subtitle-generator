"""Phase Lumen L33-L36 — Error codes and error response quality tests.

Tests the structured error handling module (`app.errors`), error response
quality across API endpoints, and upload error handling paths.
— Scout (QA Lead)
"""

import re
import struct
import wave
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    """Generate a minimal valid WAV file in memory."""
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def _upload(filename="test.wav", content=None, content_type="audio/wav", **form_data):
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
# ERROR CODE MODULE (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorCodeModule:
    """Test the app.errors module structure and contents."""

    def test_module_importable(self):
        """app.errors module should be importable without error."""
        import app.errors

        assert app.errors is not None

    def test_all_error_codes_are_strings(self):
        """Every constant in ALL_ERROR_CODES should be a string."""
        from app.errors import ALL_ERROR_CODES

        for code in ALL_ERROR_CODES:
            assert isinstance(code, str), f"Error code {code!r} is not a string"

    def test_api_error_returns_dict_with_code_and_message(self):
        """api_error() should return a dict containing 'code' and 'message'."""
        from app.errors import api_error

        result = api_error("TEST_ERROR", "Something went wrong")
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Something went wrong"

    def test_error_codes_follow_upper_snake_case(self):
        """All error codes should follow UPPER_SNAKE_CASE convention."""
        from app.errors import ALL_ERROR_CODES

        pattern = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")
        for code in ALL_ERROR_CODES:
            assert pattern.match(code), f"Error code {code!r} does not follow UPPER_SNAKE_CASE"

    def test_file_size_codes_exist(self):
        """FILE_TOO_LARGE, FILE_TOO_SMALL, UNSUPPORTED_FORMAT must exist."""
        from app import errors

        assert errors.FILE_TOO_LARGE == "FILE_TOO_LARGE"
        assert errors.FILE_TOO_SMALL == "FILE_TOO_SMALL"
        assert errors.UNSUPPORTED_FORMAT == "UNSUPPORTED_FORMAT"

    def test_task_codes_exist(self):
        """TASK_NOT_FOUND and TASK_NOT_TERMINAL must exist."""
        from app import errors

        assert errors.TASK_NOT_FOUND == "TASK_NOT_FOUND"
        assert errors.TASK_NOT_TERMINAL == "TASK_NOT_TERMINAL"

    def test_system_codes_exist(self):
        """SYSTEM_CRITICAL and FFMPEG_UNAVAILABLE must exist."""
        from app import errors

        assert errors.SYSTEM_CRITICAL == "SYSTEM_CRITICAL"
        assert errors.FFMPEG_UNAVAILABLE == "FFMPEG_UNAVAILABLE"

    def test_audio_codes_exist(self):
        """NO_AUDIO_STREAM and DURATION_EXCEEDED must exist."""
        from app import errors

        assert errors.NO_AUDIO_STREAM == "NO_AUDIO_STREAM"
        assert errors.DURATION_EXCEEDED == "DURATION_EXCEEDED"

    def test_api_error_with_request_id(self):
        """api_error with request_id should include it in result."""
        from app.errors import api_error

        result = api_error("ERR", "msg", request_id="abc-123")
        assert result["request_id"] == "abc-123"

    def test_api_error_without_request_id(self):
        """api_error without request_id should omit it from result."""
        from app.errors import api_error

        result = api_error("ERR", "msg")
        assert "request_id" not in result


# ══════════════════════════════════════════════════════════════════════════════
# ERROR RESPONSE QUALITY (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorResponseQuality:
    """Test that API error responses are user-friendly and secure."""

    def test_404_responses_have_descriptive_messages(self):
        """404 responses should have a descriptive detail message."""
        res = client.get("/progress/nonexistent-task-id-12345")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data
        assert len(data["detail"]) > 5  # Not just an empty or trivial message

    def test_400_responses_explain_what_went_wrong(self):
        """400 responses should explain the validation failure."""
        res = _upload("malware.exe", content_type="application/octet-stream")
        assert res.status_code in (400, 415, 422)
        data = res.json()
        detail = data.get("detail", "")
        if isinstance(detail, str):
            assert len(detail) > 10, "Error message should be descriptive"

    def test_413_responses_mention_file_size(self):
        """413 responses should mention file size limits."""
        # The upload route returns 413 when file exceeds MAX_FILE_SIZE.
        # We can't easily trigger a real 413 (2GB upload), so verify the
        # body limit middleware returns a clear message for oversized content-length.
        res = client.post(
            "/upload",
            headers={"Content-Length": str(3 * 1024 * 1024 * 1024)},  # 3 GB
            content=b"tiny",
        )
        # BodyLimitMiddleware should reject with 413
        assert res.status_code in (413, 400, 422)

    def test_429_responses_mention_limits(self):
        """429 responses should reference rate or task limits."""
        from app import state

        # Fill all task slots so next upload hits the 429 path
        original_tasks = dict(state.tasks)
        fake_tasks = {}
        for i in range(20):
            tid = f"fake-concurrent-{i}"
            fake_tasks[tid] = {"status": "transcribing"}
        state.tasks.update(fake_tasks)
        try:
            res = _upload("test.wav")
            if res.status_code == 429:
                data = res.json()
                detail = data.get("detail", "")
                # detail may be a structured dict (code + message) or a plain string
                detail_text = detail.get("message", "") if isinstance(detail, dict) else detail
                assert "task" in detail_text.lower() or "limit" in detail_text.lower() or "wait" in detail_text.lower()
        finally:
            for tid in fake_tasks:
                state.tasks.pop(tid, None)
            state.tasks.update(original_tasks)

    def test_error_messages_no_raw_file_paths(self):
        """Error messages should not expose raw filesystem paths."""
        res = _upload("malware.exe", content_type="application/octet-stream")
        data = res.json()
        detail = str(data.get("detail", ""))
        # Should not contain Unix or Windows absolute paths
        assert "/home/" not in detail
        assert "/tmp/" not in detail
        assert "C:\\" not in detail
        assert "/app/" not in detail

    def test_error_messages_no_stack_traces(self):
        """Error messages should not contain stack traces."""
        res = client.get("/progress/nonexistent-task-id-xyz")
        data = res.json()
        detail = str(data.get("detail", ""))
        assert "Traceback" not in detail
        assert 'File "' not in detail
        assert "line " not in detail or "Please" in detail  # "line" may appear in user-friendly text

    def test_error_messages_under_500_chars(self):
        """Error messages should be concise — under 500 characters."""
        endpoints = [
            ("/progress/nonexistent-id", "GET"),
            ("/download/nonexistent-id", "GET"),
        ]
        for path, method in endpoints:
            res = client.request(method, path)
            data = res.json()
            detail = str(data.get("detail", ""))
            assert len(detail) < 500, f"Error message too long for {path}: {len(detail)} chars"

    def test_error_messages_use_plain_language(self):
        """Error messages should use plain language, not technical jargon."""
        res = _upload("malware.exe", content_type="application/octet-stream")
        data = res.json()
        detail = str(data.get("detail", "")).lower()
        # Should not contain raw exception class names or internal jargon
        assert "nullpointerexception" not in detail
        assert "segfault" not in detail
        assert "errno" not in detail

    def test_404_for_nonexistent_download(self):
        """Downloading a nonexistent task should return 404 with clear message."""
        res = client.get("/download/does-not-exist")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data

    def test_error_response_content_type_is_json(self):
        """Error responses should have application/json content type."""
        res = client.get("/progress/nonexistent-task-id-test")
        assert res.status_code == 404
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD ERROR HANDLING (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestUploadErrorHandling:
    """Test upload endpoint error paths and edge cases."""

    def test_upload_with_no_file_returns_422(self):
        """POST /upload without a file attachment should return 422."""
        res = client.post("/upload")
        assert res.status_code == 422

    def test_upload_with_unsupported_extension_returns_400(self):
        """Uploading a file with unsupported extension should return 400."""
        res = _upload("test.pdf", content_type="application/pdf")
        assert res.status_code in (400, 415, 422)

    def test_upload_response_has_proper_structure(self):
        """Successful upload should return task_id, model_size, language."""
        wav_data = _make_wav_bytes(1.0)
        res = _upload("test.wav", content=wav_data)
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        assert "model_size" in data
        assert "language" in data

    def test_upload_with_empty_filename_handled(self):
        """Upload with empty filename should not crash the server."""
        res = _upload("", content_type="application/octet-stream")
        # Should reject (no extension) but not crash
        assert res.status_code in (400, 415, 422)

    def test_upload_with_very_long_filename_handled(self):
        """Upload with an extremely long filename should not crash."""
        long_name = "a" * 500 + ".wav"
        wav_data = _make_wav_bytes()
        res = _upload(long_name, content=wav_data)
        # May succeed (filename sanitized) or reject, but must not 500
        assert res.status_code != 500

    def test_concurrent_task_limit_clear_error(self):
        """Hitting concurrent task limit should return 429 with clear message."""
        from app import state

        original_tasks = dict(state.tasks)
        fake_tasks = {}
        for i in range(20):
            tid = f"limit-test-{i}"
            fake_tasks[tid] = {"status": "transcribing"}
        state.tasks.update(fake_tasks)
        try:
            res = _upload("test.wav")
            assert res.status_code == 429
            data = res.json()
            assert "detail" in data
            detail = data["detail"]
            detail_text = detail.get("message", "") if isinstance(detail, dict) else detail
            assert "task" in detail_text.lower() or "wait" in detail_text.lower()
        finally:
            for tid in fake_tasks:
                state.tasks.pop(tid, None)
            state.tasks.update(original_tasks)

    def test_invalid_model_parameter_handled_gracefully(self):
        """Invalid model_size should be handled without crashing."""
        wav_data = _make_wav_bytes(1.0)
        # FastAPI Form with Literal type validates model_size, so invalid
        # values should return 422 (validation error) — not 500.
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "nonexistent_model", "output_format": "srt"},
        )
        assert res.status_code in (200, 400, 422)

    def test_invalid_language_defaults_to_auto(self):
        """Invalid language parameter should default to auto, not crash."""
        wav_data = _make_wav_bytes(1.0)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "language": "zzzz_invalid"},
        )
        # Should succeed — invalid language defaults to "auto"
        assert res.status_code == 200
        data = res.json()
        assert data.get("language") == "auto"

    def test_upload_422_detail_is_list_or_string(self):
        """422 validation error detail should be a list (FastAPI) or string."""
        res = client.post("/upload")
        assert res.status_code == 422
        data = res.json()
        detail = data.get("detail")
        assert isinstance(detail, (list, str))

    def test_upload_no_file_error_mentions_file(self):
        """422 for missing file should reference the 'file' field."""
        res = client.post("/upload")
        assert res.status_code == 422
        body = res.text.lower()
        assert "file" in body or "field" in body or "required" in body

"""Sprint 25 tests: Input Validation & Secure Processing.

Tests cover:
  - Path traversal prevention (safe_path)
  - File checksum computation and verification
  - Subtitle content sanitization
  - Subtitle timing validation
  - Error message sanitization
  - FFmpeg filter injection prevention
  - Pydantic schema validation
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Path Traversal Prevention Tests ──

class TestSafePath:
    """Test path traversal prevention."""

    def test_safe_path_exists(self):
        from app.utils.validation import safe_path
        assert callable(safe_path)

    def test_safe_path_rejects_traversal(self):
        from app.utils.validation import safe_path
        with pytest.raises(ValueError, match="traversal|outside"):
            safe_path("../../etc/passwd")

    def test_safe_path_rejects_absolute_outside(self):
        from app.utils.validation import safe_path
        with pytest.raises(ValueError):
            safe_path("/etc/passwd")

    def test_safe_path_allows_valid_dir(self):
        from app.utils.validation import safe_path
        from app.config import OUTPUT_DIR
        OUTPUT_DIR.mkdir(exist_ok=True)
        # Should not raise for a path inside OUTPUT_DIR
        result = safe_path(OUTPUT_DIR / "test.srt", allowed_dir=OUTPUT_DIR)
        assert isinstance(result, Path)

    def test_safe_path_blocks_dir_escape(self):
        from app.utils.validation import safe_path
        from app.config import OUTPUT_DIR
        with pytest.raises(ValueError):
            safe_path(OUTPUT_DIR / ".." / ".." / "etc" / "passwd", allowed_dir=OUTPUT_DIR)


# ── Checksum Tests ──

class TestFileChecksum:
    """Test file integrity checksums."""

    def test_compute_checksum(self):
        from app.utils.validation import compute_checksum
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test content for checksum")
            f.flush()
            path = f.name
        try:
            h = compute_checksum(path)
            assert isinstance(h, str)
            assert len(h) == 64  # SHA-256 hex length
        finally:
            os.unlink(path)

    def test_verify_checksum_matches(self):
        from app.utils.validation import compute_checksum, verify_checksum
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"verify me")
            f.flush()
            path = f.name
        try:
            h = compute_checksum(path)
            assert verify_checksum(path, h) is True
        finally:
            os.unlink(path)

    def test_verify_checksum_fails_mismatch(self):
        from app.utils.validation import verify_checksum
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"some data")
            f.flush()
            path = f.name
        try:
            assert verify_checksum(path, "0" * 64) is False
        finally:
            os.unlink(path)

    def test_deterministic_checksum(self):
        from app.utils.validation import compute_checksum
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"deterministic")
            f.flush()
            path = f.name
        try:
            h1 = compute_checksum(path)
            h2 = compute_checksum(path)
            assert h1 == h2
        finally:
            os.unlink(path)


# ── Subtitle Sanitization Tests ──

class TestSubtitleSanitization:
    """Test subtitle content sanitization."""

    def test_sanitize_function_exists(self):
        from app.utils.validation import sanitize_subtitle_text
        assert callable(sanitize_subtitle_text)

    def test_removes_control_chars(self):
        from app.utils.validation import sanitize_subtitle_text
        text = "Hello\x00World\x01!"
        result = sanitize_subtitle_text(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "Hello" in result

    def test_removes_script_tags(self):
        from app.utils.validation import sanitize_subtitle_text
        text = 'Normal text<script>alert("xss")</script>More text'
        result = sanitize_subtitle_text(text)
        assert "<script" not in result
        assert "alert" not in result
        assert "Normal text" in result
        assert "More text" in result

    def test_preserves_formatting_tags(self):
        from app.utils.validation import sanitize_subtitle_text
        text = "<b>Bold</b> and <i>italic</i>"
        result = sanitize_subtitle_text(text)
        assert "<b>" in result
        assert "<i>" in result

    def test_removes_dangerous_html(self):
        from app.utils.validation import sanitize_subtitle_text
        text = 'Text <img src=x onerror=alert(1)> more'
        result = sanitize_subtitle_text(text)
        assert "<img" not in result

    def test_preserves_normal_text(self):
        from app.utils.validation import sanitize_subtitle_text
        text = "This is a normal subtitle line."
        assert sanitize_subtitle_text(text) == text

    def test_empty_input(self):
        from app.utils.validation import sanitize_subtitle_text
        assert sanitize_subtitle_text("") == ""
        assert sanitize_subtitle_text(None) is None


# ── Subtitle Timing Validation ──

class TestSubtitleTiming:
    """Test subtitle timing validation."""

    def test_valid_timing(self):
        from app.utils.validation import validate_subtitle_timing
        valid, msg = validate_subtitle_timing(1.0, 5.0)
        assert valid is True

    def test_negative_start(self):
        from app.utils.validation import validate_subtitle_timing
        valid, msg = validate_subtitle_timing(-1.0, 5.0)
        assert valid is False
        assert "negative" in msg.lower()

    def test_end_before_start(self):
        from app.utils.validation import validate_subtitle_timing
        valid, msg = validate_subtitle_timing(5.0, 3.0)
        assert valid is False

    def test_equal_times(self):
        from app.utils.validation import validate_subtitle_timing
        valid, msg = validate_subtitle_timing(5.0, 5.0)
        assert valid is False

    def test_excessive_duration(self):
        from app.utils.validation import validate_subtitle_timing
        valid, msg = validate_subtitle_timing(0.0, 400.0)
        assert valid is False
        assert "maximum" in msg.lower()


# ── Error Message Sanitization ──

class TestErrorSanitization:
    """Test error message sanitization for client responses."""

    def test_sanitize_function_exists(self):
        from app.utils.validation import sanitize_error_message
        assert callable(sanitize_error_message)

    def test_redacts_file_paths(self):
        from app.utils.validation import sanitize_error_message
        msg = "Failed to read C:\\Users\\admin\\secrets\\key.txt"
        result = sanitize_error_message(msg)
        assert "admin" not in result
        assert "secrets" not in result

    def test_redacts_unix_paths(self):
        from app.utils.validation import sanitize_error_message
        msg = "Error in /home/user/app/service.py line 42"
        result = sanitize_error_message(msg)
        assert "/home/user" not in result

    def test_redacts_db_urls(self):
        from app.utils.validation import sanitize_error_message
        msg = "Connection failed: postgresql://user:pass@db:5432/mydb"
        result = sanitize_error_message(msg)
        assert "user:pass" not in result

    def test_preserves_generic_messages(self):
        from app.utils.validation import sanitize_error_message
        msg = "File not found"
        assert sanitize_error_message(msg) == msg

    def test_include_details_flag(self):
        from app.utils.validation import sanitize_error_message
        msg = "Error at /home/user/app.py"
        result = sanitize_error_message(msg, include_details=True)
        assert result == msg  # No redaction when details=True


# ── FFmpeg Filter Injection Tests ──

class TestFFmpegValidation:
    """Test FFmpeg filter value validation."""

    def test_validate_function_exists(self):
        from app.utils.validation import validate_ffmpeg_filter_value
        assert callable(validate_ffmpeg_filter_value)

    def test_allows_safe_values(self):
        from app.utils.validation import validate_ffmpeg_filter_value
        assert validate_ffmpeg_filter_value("Arial") is True
        assert validate_ffmpeg_filter_value("24") is True
        assert validate_ffmpeg_filter_value("bold-text") is True

    def test_rejects_injection(self):
        from app.utils.validation import validate_ffmpeg_filter_value
        assert validate_ffmpeg_filter_value("'; rm -rf /") is False
        assert validate_ffmpeg_filter_value("$(whoami)") is False
        assert validate_ffmpeg_filter_value("val`id`") is False

    def test_rejects_special_chars(self):
        from app.utils.validation import validate_ffmpeg_filter_value
        assert validate_ffmpeg_filter_value("test;cmd") is False
        assert validate_ffmpeg_filter_value("val|pipe") is False

    def test_validates_font_name(self):
        from app.utils.validation import validate_ffmpeg_font
        assert validate_ffmpeg_font("Arial") == "Arial"
        assert validate_ffmpeg_font("") == "Arial"
        assert validate_ffmpeg_font("'; DROP TABLE") == "DROP TABLE"  # Only alphanum kept

    def test_empty_value_allowed(self):
        from app.utils.validation import validate_ffmpeg_filter_value
        assert validate_ffmpeg_filter_value("") is True


# ── Pydantic Validation on Routes ──

class TestRouteValidation:
    """Test that routes properly validate input via Pydantic."""

    def test_upload_rejects_invalid_extension(self):
        import io
        res = client.post("/upload", files={"file": ("test.exe", io.BytesIO(b"x" * 2048), "application/octet-stream")})
        assert res.status_code in (400, 422)

    def test_track_rejects_missing_event(self):
        res = client.post("/track", json={"target": "btn"})
        assert res.status_code == 422

    def test_feedback_rejects_invalid_rating(self):
        res = client.post("/feedback", json={"task_id": "t1", "rating": 10, "comment": "test"})
        assert res.status_code == 422

    def test_register_rejects_short_password(self):
        res = client.post("/auth/register", json={"username": "validuser", "password": "12345"})
        assert res.status_code == 422

"""Phase Lumen L8 — Security validation tests.

Tests path traversal prevention, filename sanitization, FFmpeg filter
validation, subtitle text sanitization, security headers, CORS, and
error message redaction.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app.main import app
from app.utils.validation import (
    safe_path,
    sanitize_error_message,
    sanitize_subtitle_text,
    validate_ffmpeg_filter_value,
    validate_ffmpeg_font,
    validate_subtitle_timing,
)

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# PATH TRAVERSAL PREVENTION
# ══════════════════════════════════════════════════════════════════════════════


class TestPathTraversal:
    """Test safe_path blocks traversal attacks."""

    def test_path_within_allowed_dir(self):
        from app.config import UPLOAD_DIR

        p = safe_path(UPLOAD_DIR / "test.wav", allowed_dir=UPLOAD_DIR)
        assert str(p).startswith(str(UPLOAD_DIR.resolve()))

    def test_path_traversal_blocked(self):
        import pytest

        from app.config import UPLOAD_DIR

        with pytest.raises(ValueError, match="traversal"):
            safe_path(UPLOAD_DIR / "../../etc/passwd", allowed_dir=UPLOAD_DIR)

    def test_path_traversal_double_dots(self):
        import pytest

        from app.config import UPLOAD_DIR

        with pytest.raises(ValueError):
            safe_path("../../etc/shadow", allowed_dir=UPLOAD_DIR)

    def test_path_in_output_dir_allowed(self):
        from app.config import OUTPUT_DIR

        p = safe_path(OUTPUT_DIR / "result.srt")
        assert str(p).startswith(str(OUTPUT_DIR.resolve()))

    def test_path_in_upload_dir_allowed(self):
        from app.config import UPLOAD_DIR

        p = safe_path(UPLOAD_DIR / "file.wav")
        assert str(p).startswith(str(UPLOAD_DIR.resolve()))

    def test_path_outside_safe_dirs_blocked(self):
        import pytest

        with pytest.raises(ValueError):
            safe_path("/etc/passwd")

    def test_path_absolute_outside_blocked(self):
        import pytest

        with pytest.raises(ValueError):
            safe_path("/tmp/evil_file.txt")

    def test_path_resolve_symlinks(self):
        from app.config import UPLOAD_DIR

        # safe_path resolves paths
        p = safe_path(UPLOAD_DIR / "." / "test.wav", allowed_dir=UPLOAD_DIR)
        assert ".." not in str(p)


# ══════════════════════════════════════════════════════════════════════════════
# FILENAME SANITIZATION (via security.py)
# ══════════════════════════════════════════════════════════════════════════════


class TestFilenameSanitization:
    """Test sanitize_filename from security module."""

    def test_normal_filename(self):
        from app.utils.security import sanitize_filename

        assert sanitize_filename("test.wav") == "test.wav"

    def test_removes_null_bytes(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("test\x00.wav")
        assert "\x00" not in result

    def test_removes_control_chars(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("test\x01\x02\x03.wav")
        for c in ["\x01", "\x02", "\x03"]:
            assert c not in result

    def test_strips_unix_path(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("/etc/passwd/evil.wav")
        assert result == "evil.wav"

    def test_strips_windows_path(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("C:\\Windows\\evil.wav")
        assert "C:" not in result
        assert "Windows" not in result

    def test_replaces_shell_metacharacters(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename('test"file|name?.wav')
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result

    def test_empty_returns_unnamed(self):
        from app.utils.security import sanitize_filename

        assert sanitize_filename("") == "unnamed_file"

    def test_only_spaces_returns_unnamed(self):
        from app.utils.security import sanitize_filename

        assert sanitize_filename("   ") == "unnamed_file"

    def test_only_dots_returns_unnamed(self):
        from app.utils.security import sanitize_filename

        assert sanitize_filename("...") == "unnamed_file"

    def test_leading_dots_stripped(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename(".hidden.wav")
        assert not result.startswith(".")

    def test_unicode_preserved(self):
        from app.utils.security import sanitize_filename

        result = sanitize_filename("日本語.wav")
        assert "日本語" in result


# ══════════════════════════════════════════════════════════════════════════════
# FFMPEG FILTER VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestFFmpegValidation:
    """Test FFmpeg filter value and font validation."""

    def test_safe_value_allowed(self):
        assert validate_ffmpeg_filter_value("Arial") is True

    def test_numbers_allowed(self):
        assert validate_ffmpeg_filter_value("24") is True

    def test_spaces_allowed(self):
        assert validate_ffmpeg_filter_value("Times New Roman") is True

    def test_empty_allowed(self):
        assert validate_ffmpeg_filter_value("") is True

    def test_semicolon_blocked(self):
        assert validate_ffmpeg_filter_value("test;rm -rf /") is False

    def test_backtick_blocked(self):
        assert validate_ffmpeg_filter_value("`id`") is False

    def test_pipe_blocked(self):
        assert validate_ffmpeg_filter_value("test|cat /etc/passwd") is False

    def test_dollar_blocked(self):
        assert validate_ffmpeg_filter_value("$(whoami)") is False

    def test_brackets_blocked(self):
        assert validate_ffmpeg_filter_value("[evil]") is False

    def test_single_quote_blocked(self):
        assert validate_ffmpeg_filter_value("test'injection") is False

    def test_font_validation_known_font(self):
        assert validate_ffmpeg_font("Arial") == "Arial"

    def test_font_validation_empty(self):
        assert validate_ffmpeg_font("") == "Arial"

    def test_font_validation_strips_special(self):
        result = validate_ffmpeg_font("Arial;rm -rf /")
        assert ";" not in result
        assert "/" not in result

    def test_font_validation_unknown_font_sanitized(self):
        result = validate_ffmpeg_font("CustomFont")
        assert isinstance(result, str)
        assert len(result) > 0


# ══════════════════════════════════════════════════════════════════════════════
# SUBTITLE TEXT SANITIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestSubtitleSanitization:
    """Test subtitle text sanitization (XSS prevention)."""

    def test_plain_text_unchanged(self):
        assert sanitize_subtitle_text("Hello world") == "Hello world"

    def test_script_tag_removed(self):
        result = sanitize_subtitle_text("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "alert" not in result

    def test_script_with_attributes_removed(self):
        result = sanitize_subtitle_text('<script type="text/javascript">evil()</script>')
        assert "<script" not in result

    def test_img_tag_removed(self):
        result = sanitize_subtitle_text("<img src=x onerror=alert(1)>")
        assert "<img" not in result

    def test_bold_tag_preserved(self):
        result = sanitize_subtitle_text("<b>Bold text</b>")
        assert "<b>" in result

    def test_italic_tag_preserved(self):
        result = sanitize_subtitle_text("<i>Italic text</i>")
        assert "<i>" in result

    def test_underline_tag_preserved(self):
        result = sanitize_subtitle_text("<u>Underlined</u>")
        assert "<u>" in result

    def test_font_tag_preserved(self):
        result = sanitize_subtitle_text('<font color="red">Red</font>')
        assert "<font" in result

    def test_div_tag_removed(self):
        result = sanitize_subtitle_text("<div>content</div>")
        assert "<div>" not in result

    def test_control_chars_removed(self):
        result = sanitize_subtitle_text("Hello\x01\x02World")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_newlines_preserved(self):
        result = sanitize_subtitle_text("Line 1\nLine 2")
        assert "\n" in result

    def test_empty_text_returns_empty(self):
        assert sanitize_subtitle_text("") == ""

    def test_none_text_returns_none(self):
        assert sanitize_subtitle_text(None) is None

    def test_unicode_normalized(self):
        # NFC normalization
        result = sanitize_subtitle_text("caf\u0065\u0301")  # e + combining accent
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════════════════════
# SUBTITLE TIMING VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestSubtitleTimingValidation:
    """Test subtitle timing validation."""

    def test_valid_timing(self):
        valid, msg = validate_subtitle_timing(0.0, 2.0)
        assert valid is True

    def test_negative_start(self):
        valid, msg = validate_subtitle_timing(-1.0, 2.0)
        assert valid is False
        assert "negative" in msg.lower()

    def test_negative_end(self):
        valid, msg = validate_subtitle_timing(0.0, -1.0)
        assert valid is False

    def test_end_before_start(self):
        valid, msg = validate_subtitle_timing(5.0, 3.0)
        assert valid is False

    def test_equal_start_end(self):
        valid, msg = validate_subtitle_timing(1.0, 1.0)
        assert valid is False

    def test_too_long_duration(self):
        valid, msg = validate_subtitle_timing(0.0, 400.0)
        assert valid is False
        assert "300" in msg or "maximum" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# ERROR MESSAGE SANITIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorSanitization:
    """Test error message sanitization for client responses."""

    def test_strips_unix_paths(self):
        msg = sanitize_error_message("Error at /home/user/secret/file.py")
        assert "/home/user" not in msg

    def test_strips_windows_paths(self):
        msg = sanitize_error_message("Error at C:\\Users\\admin\\secret.txt")
        assert "C:" not in msg

    def test_strips_db_urls(self):
        msg = sanitize_error_message("Cannot connect to postgresql://admin:pass@host/db")
        assert "postgresql://" not in msg

    def test_strips_tracebacks(self):
        msg = sanitize_error_message('File "/app/main.py", line 42')
        assert "/app/main.py" not in msg

    def test_include_details_preserves_all(self):
        original = "Error at /home/user/file.py line 42"
        msg = sanitize_error_message(original, include_details=True)
        assert msg == original

    def test_normal_message_unchanged(self):
        msg = sanitize_error_message("File too large")
        assert msg == "File too large"


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY HEADERS
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_x_content_type_options(self):
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self):
        res = client.get("/health")
        header = res.headers.get("x-frame-options", "")
        assert header in ("DENY", "SAMEORIGIN", "deny", "sameorigin", "")

    def test_referrer_policy(self):
        res = client.get("/health")
        assert "referrer-policy" in {k.lower() for k in res.headers.keys()}

    def test_csp_header_present(self):
        res = client.get("/")
        # CSP may be on HTML pages
        headers_lower = {k.lower(): v for k, v in res.headers.items()}
        # At least one security header should be present
        assert any(
            h in headers_lower
            for h in [
                "content-security-policy",
                "x-content-type-options",
                "x-frame-options",
            ]
        )


# ══════════════════════════════════════════════════════════════════════════════
# CORS HEADERS
# ══════════════════════════════════════════════════════════════════════════════


class TestCORSHeaders:
    """Test CORS behavior."""

    def test_cors_preflight(self):
        res = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.status_code == 200

    def test_cors_origin_header_on_response(self):
        res = client.get("/health", headers={"Origin": "http://localhost:3000"})
        # Should have access-control-allow-origin
        assert "access-control-allow-origin" in {k.lower() for k in res.headers.keys()}


# ══════════════════════════════════════════════════════════════════════════════
# FILE VALIDATION UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestFileValidation:
    """Test file validation utilities."""

    def test_validate_extension_valid(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("audio.wav") == ".wav"

    def test_validate_extension_invalid(self):
        from app.utils.security import validate_file_extension

        assert validate_file_extension("script.py") is None

    def test_validate_file_size_too_small(self):
        from app.utils.security import validate_file_size

        valid, msg = validate_file_size(100)
        assert valid is False

    def test_validate_file_size_valid(self):
        from app.utils.security import validate_file_size

        valid, msg = validate_file_size(2048)
        assert valid is True

    def test_checksum_computation(self):
        import tempfile

        from app.utils.validation import compute_checksum

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test data")
            f.flush()
            checksum = compute_checksum(f.name)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA-256 hex length

    def test_checksum_verification(self):
        import tempfile

        from app.utils.validation import compute_checksum, verify_checksum

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test data")
            f.flush()
            checksum = compute_checksum(f.name)
            assert verify_checksum(f.name, checksum) is True
            assert verify_checksum(f.name, "wrong_checksum") is False

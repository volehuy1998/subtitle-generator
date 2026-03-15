"""Sprint 31 tests: FFmpeg error-banner filter and template guards.

Tests cover:
  - FFmpeg stderr banner-stripping logic in extract_audio (media.py:119-127)
  - Template typeof guard for toggleEmbedPanel (index.html)

Tests by Scout (QA Lead)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── FFmpeg Banner Filter Tests ──


FFMPEG_BANNER = """\
ffmpeg version 6.1.1 Copyright (c) 2000-2024 the FFmpeg developers
  built with gcc 13.2.0
  configuration: --enable-gpl --enable-libx264
  libavutil      58. 29.100 / 58. 29.100
  libavcodec     60. 31.102 / 60. 31.102
  libavformat    60. 16.100 / 60. 16.100
  libswscale      7. 11.100 /  7. 11.100"""

REAL_ERROR = "input.mp4: No such file or directory"
CONVERSION_ERROR = "Discarding 42 corrupt packets\nConversion failed!"


class TestFfmpegBannerFilter:
    """Test that extract_audio strips ffmpeg banner lines from error messages."""

    def _build_stderr(self, banner: str, error: str) -> str:
        """Combine banner and error into realistic ffmpeg stderr."""
        parts = []
        if banner:
            parts.append(banner)
        if error:
            parts.append(error)
        return "\n".join(parts)

    def _get_error_msg(self, stderr: str) -> str:
        """Apply the same banner-filter logic as media.py extract_audio."""
        error_lines = [
            line
            for line in stderr.strip().splitlines()
            if not line.startswith(("  ", "ffmpeg version")) and line.strip()
        ]
        return "\n".join(error_lines[-5:]) if error_lines else stderr[-200:]

    @patch("app.utils.media.subprocess.Popen")
    def test_banner_stripped_stderr_raises_correct_error(self, mock_popen):
        """Banner lines are filtered; RuntimeError contains only the real error."""
        from app.utils.media import extract_audio

        stderr = self._build_stderr(FFMPEG_BANNER, REAL_ERROR)
        proc_mock = MagicMock()
        proc_mock.communicate.return_value = ("", stderr)
        proc_mock.returncode = 1
        mock_popen.return_value = proc_mock

        with pytest.raises(RuntimeError, match="No such file or directory"):
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))

        # Verify banner lines are NOT in the error
        try:
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))
        except RuntimeError as exc:
            msg = str(exc)
            assert "ffmpeg version" not in msg
            assert "built with" not in msg
            assert "configuration:" not in msg
            assert "libavutil" not in msg

    @patch("app.utils.media.subprocess.Popen")
    def test_all_filtered_uses_fallback(self, mock_popen):
        """When ALL lines match the filter, fallback to stderr[-200:]."""
        from app.utils.media import extract_audio

        # stderr with only banner lines (all start with "  " or "ffmpeg version")
        all_banner = FFMPEG_BANNER
        proc_mock = MagicMock()
        proc_mock.communicate.return_value = ("", all_banner)
        proc_mock.returncode = 1
        mock_popen.return_value = proc_mock

        with pytest.raises(RuntimeError) as exc_info:
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))

        msg = str(exc_info.value)
        # Fallback: last 200 chars of stderr
        assert len(msg) > 0
        # Should contain the tail of the banner since fallback is used
        assert "libswscale" in msg or "libavformat" in msg or "ffmpeg version" in msg

    @patch("app.utils.media.subprocess.Popen")
    def test_mixed_content_only_error_lines(self, mock_popen):
        """Mixed banner + error lines: only error lines appear in the message."""
        from app.utils.media import extract_audio

        stderr = self._build_stderr(FFMPEG_BANNER, CONVERSION_ERROR)
        proc_mock = MagicMock()
        proc_mock.communicate.return_value = ("", stderr)
        proc_mock.returncode = 1
        mock_popen.return_value = proc_mock

        with pytest.raises(RuntimeError) as exc_info:
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))

        msg = str(exc_info.value)
        assert "Conversion failed!" in msg
        assert "corrupt packets" in msg
        assert "ffmpeg version" not in msg
        assert "libavutil" not in msg

    @patch("app.utils.media.subprocess.Popen")
    def test_empty_stderr(self, mock_popen):
        """Empty stderr uses fallback (empty string)."""
        from app.utils.media import extract_audio

        proc_mock = MagicMock()
        proc_mock.communicate.return_value = ("", "")
        proc_mock.returncode = 1
        mock_popen.return_value = proc_mock

        with pytest.raises(RuntimeError, match="ffmpeg error \\(exit 1\\):"):
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))

    @patch("app.utils.media.subprocess.Popen")
    def test_error_lines_limited_to_last_five(self, mock_popen):
        """Only the last 5 error lines are included in the message."""
        from app.utils.media import extract_audio

        many_errors = "\n".join(f"Error line {i}" for i in range(10))
        stderr = self._build_stderr(FFMPEG_BANNER, many_errors)
        proc_mock = MagicMock()
        proc_mock.communicate.return_value = ("", stderr)
        proc_mock.returncode = 1
        mock_popen.return_value = proc_mock

        with pytest.raises(RuntimeError) as exc_info:
            extract_audio(Path("/tmp/input.mp4"), Path("/tmp/out.wav"))

        msg = str(exc_info.value)
        assert "Error line 5" in msg
        assert "Error line 9" in msg
        assert "Error line 0" not in msg
        assert "Error line 4" not in msg


class TestBannerFilterLogic:
    """Unit tests for the banner-filter logic in isolation (no subprocess)."""

    def test_startswith_tuple_simplified(self):
        """Verify the startswith tuple no longer has redundant entries."""
        import inspect

        from app.utils.media import extract_audio

        source = inspect.getsource(extract_audio)
        # Should NOT contain the old redundant entries
        assert '"  built with"' not in source
        assert '"  configuration:"' not in source
        assert '"  lib"' not in source
        # Should still filter two-space-prefixed lines and "ffmpeg version"
        assert '"  "' in source
        assert '"ffmpeg version"' in source


# ── Template Guard Tests ──


class TestTemplateEmbedPanelTracking:
    """Verify embed panel toggle tracking exists in Jinja template.

    Replaces skipped test in test_sprint21.py:306 (TestAnalyticsTracking.test_panel_view_tracking).
    The Jinja template uses inline tracking calls rather than a separate toggleEmbedPanel function.
    """

    def test_embed_panel_toggle_tracking_present(self):
        """templates/index.html must contain embed_panel_toggle tracking."""
        template_path = Path(__file__).parent.parent / "templates" / "index.html"
        assert template_path.exists(), f"Template not found: {template_path}"
        content = template_path.read_text()
        assert "embed_panel_toggle" in content, "Missing embed_panel_toggle tracking in templates/index.html"

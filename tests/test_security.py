"""Tests for app.utils.security - file validation and sanitization."""

from app.utils.security import validate_file_extension, sanitize_filename


class TestValidateFileExtension:
    def test_valid_mp4(self):
        assert validate_file_extension("video.mp4") == ".mp4"

    def test_valid_mkv(self):
        assert validate_file_extension("video.mkv") == ".mkv"

    def test_valid_wav(self):
        assert validate_file_extension("audio.wav") == ".wav"

    def test_valid_flac(self):
        assert validate_file_extension("audio.flac") == ".flac"

    def test_invalid_txt(self):
        assert validate_file_extension("file.txt") is None

    def test_invalid_exe(self):
        assert validate_file_extension("malware.exe") is None

    def test_invalid_pdf(self):
        assert validate_file_extension("doc.pdf") is None

    def test_case_insensitive(self):
        assert validate_file_extension("video.MP4") == ".mp4"

    def test_no_extension(self):
        assert validate_file_extension("noextension") is None


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_filename("video.mp4") == "video.mp4"

    def test_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_null_bytes(self):
        result = sanitize_filename("video\x00.mp4")
        assert "\x00" not in result

    def test_windows_path_separators(self):
        result = sanitize_filename("C:\\Users\\test\\video.mp4")
        assert "video.mp4" == result

    def test_special_characters(self):
        result = sanitize_filename('file<>:"|?*.mp4')
        assert "<" not in result
        assert ">" not in result

    def test_empty_filename(self):
        result = sanitize_filename("")
        assert result == "unnamed_file"

    def test_only_dots(self):
        result = sanitize_filename("...")
        assert result == "unnamed_file"

    def test_unicode_filename(self):
        result = sanitize_filename("video.mp4")
        assert result == "video.mp4"

    def test_leading_trailing_spaces(self):
        result = sanitize_filename("  video.mp4  ")
        assert result == "video.mp4"

"""Tests for app.utils.srt - pure functions, no mocks needed."""

from app.utils.srt import segments_to_srt


class TestSegmentsToSrt:
    def test_empty_segments(self):
        assert segments_to_srt([]) == ""

    def test_single_segment(self):
        segments = [{"start": 0.0, "end": 2.5, "text": "Hello world"}]
        result = segments_to_srt(segments)
        lines = result.split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:02,500"
        assert lines[2] == "Hello world"
        assert lines[3] == ""

    def test_multiple_segments(self):
        segments = [
            {"start": 0.0, "end": 2.0, "text": "First"},
            {"start": 2.5, "end": 5.0, "text": "Second"},
            {"start": 5.5, "end": 8.0, "text": "Third"},
        ]
        result = segments_to_srt(segments)
        lines = result.split("\n")
        assert lines[0] == "1"
        assert lines[4] == "2"
        assert lines[8] == "3"

    def test_text_is_stripped(self):
        segments = [{"start": 0.0, "end": 1.0, "text": "  padded text  "}]
        result = segments_to_srt(segments)
        assert "padded text" in result
        assert "  padded text  " not in result

    def test_srt_format_structure(self):
        segments = [
            {"start": 0.0, "end": 1.0, "text": "Line one"},
            {"start": 1.0, "end": 2.0, "text": "Line two"},
        ]
        result = segments_to_srt(segments)
        assert " --> " in result
        assert result.startswith("1\n")
        assert "\n2\n" in result

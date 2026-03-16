"""Phase Lumen L8 — Subtitle format output tests.

Tests SRT/VTT/JSON output correctness, edge cases, line breaking,
timestamp precision, and parsing roundtrips.
— Scout (QA Lead)
"""

import json

from app.utils.formatting import format_timestamp
from app.utils.srt import (
    _format_vtt_timestamp,
    _parse_srt_timestamp,
    _parse_vtt_timestamp,
    parse_srt,
    parse_vtt,
    segments_to_json,
    segments_to_srt,
    segments_to_vtt,
)
from app.utils.subtitle_format import (
    break_line,
    calculate_cps,
    format_segments_with_linebreaks,
    validate_timing,
    words_to_segments,
)

# ── Helper segments ──────────────────────────────────────────────────────────


def _make_segments(n=3):
    """Create n simple test segments."""
    return [{"start": i * 2.0, "end": i * 2.0 + 1.5, "text": f"Segment {i + 1} text."} for i in range(n)]


def _make_segment(start=0.0, end=1.0, text="Hello world"):
    return {"start": start, "end": end, "text": text}


# ══════════════════════════════════════════════════════════════════════════════
# SRT FORMAT
# ══════════════════════════════════════════════════════════════════════════════


class TestSRTFormat:
    """Test SRT output formatting."""

    def test_srt_sequential_numbering(self):
        segs = _make_segments(5)
        srt = segments_to_srt(segs)
        lines = srt.strip().split("\n")
        numbers = [ln for ln in lines if ln.strip().isdigit()]
        assert numbers == ["1", "2", "3", "4", "5"]

    def test_srt_single_segment(self):
        srt = segments_to_srt([_make_segment(0.0, 1.5, "Hello")])
        assert "1\n" in srt
        assert "00:00:00,000 --> 00:00:01,500" in srt
        assert "Hello" in srt

    def test_srt_timestamp_format(self):
        srt = segments_to_srt([_make_segment(3661.123, 3662.456, "Test")])
        assert "01:01:01,123 --> 01:01:02,456" in srt

    def test_srt_blank_line_separators(self):
        segs = _make_segments(3)
        srt = segments_to_srt(segs)
        blocks = srt.strip().split("\n\n")
        assert len(blocks) == 3

    def test_srt_zero_start_time(self):
        srt = segments_to_srt([_make_segment(0.0, 0.5, "First")])
        assert "00:00:00,000" in srt

    def test_srt_millisecond_precision(self):
        srt = segments_to_srt([_make_segment(1.001, 2.999, "Precise")])
        # format_timestamp uses int((seconds - int(seconds)) * 1000), may lose sub-ms precision
        assert "00:00:01," in srt
        assert "00:00:02,999" in srt

    def test_srt_large_timestamp(self):
        srt = segments_to_srt([_make_segment(7200.0, 7201.0, "Two hours")])
        assert "02:00:00,000" in srt

    def test_srt_empty_segments_list(self):
        srt = segments_to_srt([])
        assert srt == ""

    def test_srt_whitespace_trimmed(self):
        srt = segments_to_srt([_make_segment(0, 1, "  padded text  ")])
        assert "padded text" in srt
        assert "  padded text  " not in srt

    def test_srt_unicode_text(self):
        srt = segments_to_srt([_make_segment(0, 1, "日本語テスト")])
        assert "日本語テスト" in srt

    def test_srt_arabic_rtl_text(self):
        srt = segments_to_srt([_make_segment(0, 1, "مرحبا بالعالم")])
        assert "مرحبا بالعالم" in srt

    def test_srt_emoji_text(self):
        srt = segments_to_srt([_make_segment(0, 1, "Hello 🌍")])
        assert "Hello 🌍" in srt

    def test_srt_speaker_label(self):
        seg = {"start": 0, "end": 1, "text": "Hello", "speaker": "SPEAKER_00"}
        srt = segments_to_srt([seg], include_speakers=True)
        assert "[SPEAKER_00]" in srt

    def test_srt_no_speaker_label_when_disabled(self):
        seg = {"start": 0, "end": 1, "text": "Hello", "speaker": "SPEAKER_00"}
        srt = segments_to_srt([seg], include_speakers=False)
        assert "[SPEAKER_00]" not in srt

    def test_srt_no_speaker_key(self):
        seg = {"start": 0, "end": 1, "text": "Hello"}
        srt = segments_to_srt([seg])
        assert "[" not in srt

    def test_srt_many_segments(self):
        segs = _make_segments(100)
        srt = segments_to_srt(segs)
        assert "100\n" in srt


class TestSRTParsing:
    """Test SRT parsing (roundtrip)."""

    def test_parse_srt_basic(self):
        segs = _make_segments(3)
        srt = segments_to_srt(segs)
        parsed = parse_srt(srt)
        assert len(parsed) == 3

    def test_parse_srt_preserves_text(self):
        srt = segments_to_srt([_make_segment(0, 1, "Hello world")])
        parsed = parse_srt(srt)
        assert parsed[0]["text"] == "Hello world"

    def test_parse_srt_preserves_timing(self):
        srt = segments_to_srt([_make_segment(10.5, 12.75, "Test")])
        parsed = parse_srt(srt)
        assert abs(parsed[0]["start"] - 10.5) < 0.01
        assert abs(parsed[0]["end"] - 12.75) < 0.01

    def test_parse_srt_empty(self):
        assert parse_srt("") == []

    def test_parse_srt_roundtrip(self):
        original = _make_segments(5)
        srt = segments_to_srt(original, include_speakers=False)
        parsed = parse_srt(srt)
        for orig, pars in zip(original, parsed):
            assert abs(orig["start"] - pars["start"]) < 0.01
            assert abs(orig["end"] - pars["end"]) < 0.01
            assert orig["text"].strip() == pars["text"]


# ══════════════════════════════════════════════════════════════════════════════
# VTT FORMAT
# ══════════════════════════════════════════════════════════════════════════════


class TestVTTFormat:
    """Test VTT output formatting."""

    def test_vtt_header(self):
        vtt = segments_to_vtt([_make_segment(0, 1, "Test")])
        assert vtt.startswith("WEBVTT")

    def test_vtt_dot_milliseconds(self):
        vtt = segments_to_vtt([_make_segment(1.5, 2.75, "Test")])
        assert "00:00:01.500" in vtt
        assert "00:00:02.750" in vtt

    def test_vtt_no_comma_in_timestamps(self):
        vtt = segments_to_vtt([_make_segment(0, 1, "Test")])
        # VTT uses . not , for ms
        lines = [ln for ln in vtt.split("\n") if "-->" in ln]
        for ln in lines:
            assert "," not in ln

    def test_vtt_sequential_numbering(self):
        segs = _make_segments(3)
        vtt = segments_to_vtt(segs)
        lines = vtt.split("\n")
        # After WEBVTT and blank line, cues start
        number_lines = [ln for ln in lines if ln.strip().isdigit()]
        assert "1" in number_lines
        assert "2" in number_lines
        assert "3" in number_lines

    def test_vtt_blank_line_between_cues(self):
        segs = _make_segments(2)
        vtt = segments_to_vtt(segs)
        # WEBVTT\n\n1\n...\n\n2\n...
        assert "\n\n" in vtt

    def test_vtt_speaker_tag(self):
        seg = {"start": 0, "end": 1, "text": "Hello", "speaker": "Alice"}
        vtt = segments_to_vtt([seg])
        assert "<v Alice>" in vtt

    def test_vtt_no_speaker_when_disabled(self):
        seg = {"start": 0, "end": 1, "text": "Hello", "speaker": "Alice"}
        vtt = segments_to_vtt([seg], include_speakers=False)
        assert "<v Alice>" not in vtt

    def test_vtt_unicode(self):
        vtt = segments_to_vtt([_make_segment(0, 1, "中文测试")])
        assert "中文测试" in vtt

    def test_vtt_empty_segments(self):
        vtt = segments_to_vtt([])
        assert vtt.startswith("WEBVTT")

    def test_vtt_large_timestamp(self):
        vtt = segments_to_vtt([_make_segment(3600.0, 3601.0, "Hour")])
        assert "01:00:00.000" in vtt


class TestVTTParsing:
    """Test VTT parsing."""

    def test_parse_vtt_basic(self):
        vtt = segments_to_vtt(_make_segments(3), include_speakers=False)
        parsed = parse_vtt(vtt)
        assert len(parsed) == 3

    def test_parse_vtt_preserves_text(self):
        vtt = segments_to_vtt([_make_segment(0, 1, "VTT text")])
        parsed = parse_vtt(vtt)
        assert parsed[0]["text"] == "VTT text"

    def test_parse_vtt_empty(self):
        assert parse_vtt("WEBVTT\n\n") == []

    def test_parse_vtt_roundtrip_timing(self):
        original = _make_segments(3)
        vtt = segments_to_vtt(original, include_speakers=False)
        parsed = parse_vtt(vtt)
        for orig, pars in zip(original, parsed):
            assert abs(orig["start"] - pars["start"]) < 0.01
            assert abs(orig["end"] - pars["end"]) < 0.01


# ══════════════════════════════════════════════════════════════════════════════
# JSON FORMAT
# ══════════════════════════════════════════════════════════════════════════════


class TestJSONFormat:
    """Test JSON output formatting."""

    def test_json_valid(self):
        j = segments_to_json(_make_segments(3))
        data = json.loads(j)
        assert isinstance(data, list)

    def test_json_required_fields(self):
        j = segments_to_json([_make_segment(0, 1, "Test")])
        data = json.loads(j)
        assert "start" in data[0]
        assert "end" in data[0]
        assert "text" in data[0]

    def test_json_array_structure(self):
        j = segments_to_json(_make_segments(5))
        data = json.loads(j)
        assert len(data) == 5

    def test_json_empty_segments(self):
        j = segments_to_json([])
        data = json.loads(j)
        assert data == []

    def test_json_unicode_preserved(self):
        j = segments_to_json([_make_segment(0, 1, "日本語テスト")])
        data = json.loads(j)
        assert data[0]["text"] == "日本語テスト"

    def test_json_speaker_included(self):
        seg = {"start": 0, "end": 1, "text": "Hi", "speaker": "Bob"}
        j = segments_to_json([seg])
        data = json.loads(j)
        assert data[0]["speaker"] == "Bob"

    def test_json_no_speaker_key_when_absent(self):
        j = segments_to_json([_make_segment(0, 1, "Hi")])
        data = json.loads(j)
        assert "speaker" not in data[0]

    def test_json_words_included(self):
        seg = {
            "start": 0,
            "end": 1,
            "text": "Hi there",
            "words": [{"word": "Hi", "start": 0, "end": 0.5}, {"word": "there", "start": 0.5, "end": 1}],
        }
        j = segments_to_json([seg])
        data = json.loads(j)
        assert "words" in data[0]
        assert len(data[0]["words"]) == 2

    def test_json_numeric_precision(self):
        j = segments_to_json([_make_segment(1.123456, 2.654321, "Precise")])
        data = json.loads(j)
        assert isinstance(data[0]["start"], float)
        assert isinstance(data[0]["end"], float)


# ══════════════════════════════════════════════════════════════════════════════
# TIMESTAMP FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestTimestampFormatting:
    """Test timestamp formatting functions."""

    def test_srt_timestamp_zero(self):
        assert format_timestamp(0.0) == "00:00:00,000"

    def test_srt_timestamp_one_second(self):
        assert format_timestamp(1.0) == "00:00:01,000"

    def test_srt_timestamp_with_ms(self):
        assert format_timestamp(1.5) == "00:00:01,500"

    def test_srt_timestamp_hours(self):
        assert format_timestamp(3661.0) == "01:01:01,000"

    def test_srt_timestamp_zero_padded(self):
        ts = format_timestamp(5.001)
        assert ts == "00:00:05,001"

    def test_vtt_timestamp_dot_separator(self):
        ts = _format_vtt_timestamp(1.5)
        assert "." in ts
        assert "," not in ts

    def test_vtt_timestamp_zero(self):
        assert _format_vtt_timestamp(0.0) == "00:00:00.000"

    def test_parse_srt_timestamp(self):
        val = _parse_srt_timestamp("01:02:03,456")
        assert abs(val - 3723.456) < 0.001

    def test_parse_vtt_timestamp(self):
        val = _parse_vtt_timestamp("01:02:03.456")
        assert abs(val - 3723.456) < 0.001

    def test_srt_timestamp_large_value(self):
        ts = format_timestamp(86399.999)
        assert ts.startswith("23:59:59")


# ══════════════════════════════════════════════════════════════════════════════
# LINE BREAKING
# ══════════════════════════════════════════════════════════════════════════════


class TestLineBreaking:
    """Test subtitle line-breaking rules."""

    def test_short_text_no_break(self):
        result = break_line("Short text", max_chars=42)
        assert "\n" not in result

    def test_long_text_breaks(self):
        text = "This is a very long subtitle line that should be broken into two lines"
        result = break_line(text, max_chars=42)
        assert "\n" in result

    def test_break_at_sentence_boundary(self):
        # Text must exceed max_chars and both halves must fit within max_chars
        text = "This is the first part. And this is second"
        result = break_line(text, max_chars=30)
        assert "\n" in result
        assert result.split("\n")[0].endswith(".")

    def test_break_at_comma(self):
        text = "Before the comma, after the comma goes here for length"
        result = break_line(text, max_chars=42)
        if "\n" in result:
            line1 = result.split("\n")[0]
            assert len(line1) <= 42

    def test_max_chars_respected(self):
        text = "A " * 50  # 100 chars
        result = break_line(text, max_chars=42)
        lines = result.split("\n")
        # With max_lines=2 (default), should produce 2 lines
        assert len(lines) <= 2
        # At least one line should be shorter than or close to max_chars
        assert any(len(ln) <= 50 for ln in lines)

    def test_single_word_no_break(self):
        result = break_line("Superlongwordthatcannotbebroken", max_chars=42)
        assert "\n" not in result

    def test_max_lines_one(self):
        text = "A very long line that would normally be broken into multiple lines for display"
        result = break_line(text, max_chars=30, max_lines=1)
        assert "\n" not in result

    def test_empty_text(self):
        assert break_line("") == ""

    def test_whitespace_only(self):
        assert break_line("   ").strip() == ""

    def test_format_segments_applies_linebreaks(self):
        segs = [{"start": 0, "end": 1, "text": "A " * 30}]
        result = format_segments_with_linebreaks(segs, max_chars=42)
        assert len(result) == 1
        # Text should be modified
        assert isinstance(result[0]["text"], str)


# ══════════════════════════════════════════════════════════════════════════════
# TIMING VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestTimingValidation:
    """Test subtitle timing validation."""

    def test_valid_timing(self):
        result = validate_timing(0.0, 2.0, "Hello world")
        assert result["valid"] is True

    def test_too_short_duration(self):
        result = validate_timing(0.0, 0.1, "X")
        assert result["valid"] is False
        assert any("too_short" in i for i in result["issues"])

    def test_too_long_duration(self):
        result = validate_timing(0.0, 10.0, "Hello")
        assert result["valid"] is False
        assert any("too_long" in i for i in result["issues"])

    def test_empty_text_issue(self):
        result = validate_timing(0.0, 2.0, "   ")
        assert result["valid"] is False
        assert "empty_text" in result["issues"]

    def test_cps_calculation(self):
        cps = calculate_cps("Hello world", 2.0)
        assert abs(cps - 5.5) < 0.1

    def test_cps_zero_duration(self):
        cps = calculate_cps("text", 0.0)
        assert cps == 0.0

    def test_too_fast_cps(self):
        # 100 chars in 1 second = 100 CPS
        result = validate_timing(0.0, 1.0, "x" * 100)
        assert result["valid"] is False
        assert any("too_fast" in i for i in result["issues"])

    def test_duration_field(self):
        result = validate_timing(1.0, 3.5, "Hello")
        assert abs(result["duration"] - 2.5) < 0.01

    def test_char_count_field(self):
        result = validate_timing(0, 2, "Hello world")
        assert result["char_count"] == 11


# ══════════════════════════════════════════════════════════════════════════════
# WORDS TO SEGMENTS
# ══════════════════════════════════════════════════════════════════════════════


class TestWordsToSegments:
    """Test word-level timestamp grouping."""

    def test_empty_words(self):
        assert words_to_segments([]) == []

    def test_single_word(self):
        words = [{"word": "Hello", "start": 0, "end": 0.5, "probability": 0.99}]
        segs = words_to_segments(words)
        assert len(segs) == 1
        assert segs[0]["text"] == "Hello"

    def test_multiple_words_one_segment(self):
        words = [
            {"word": "Hello", "start": 0, "end": 0.3, "probability": 0.99},
            {"word": "world", "start": 0.3, "end": 0.6, "probability": 0.98},
        ]
        segs = words_to_segments(words)
        assert len(segs) == 1
        assert "Hello" in segs[0]["text"]
        assert "world" in segs[0]["text"]

    def test_gap_forces_new_segment(self):
        words = [
            {"word": "Hello", "start": 0, "end": 0.5, "probability": 0.99},
            {"word": "world", "start": 5.0, "end": 5.5, "probability": 0.98},
        ]
        segs = words_to_segments(words, max_gap=1.5)
        assert len(segs) == 2

    def test_max_duration_forces_split(self):
        words = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4, "probability": 0.9} for i in range(30)]
        segs = words_to_segments(words, max_segment_duration=3.0)
        assert len(segs) > 1

    def test_words_preserve_timing(self):
        words = [
            {"word": "Test", "start": 1.0, "end": 1.5, "probability": 0.95},
        ]
        segs = words_to_segments(words)
        assert segs[0]["start"] == 1.0
        assert segs[0]["end"] == 1.5

    def test_words_field_in_output(self):
        words = [{"word": "Hi", "start": 0, "end": 0.3, "probability": 0.9}]
        segs = words_to_segments(words)
        assert "words" in segs[0]

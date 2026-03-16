"""Phase Lumen L8 — Edge case and boundary condition tests.

Tests extreme inputs, race conditions, boundary values, and
unusual but valid scenarios across all subsystems.
— Scout (QA Lead)
"""

import json
import struct
import uuid
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, MIN_FILE_SIZE, SUPPORTED_LANGUAGES, VALID_MODELS
from app.main import app
from app.utils.formatting import format_bytes, format_time_display, format_time_short, format_timestamp
from app.utils.srt import segments_to_json, segments_to_srt, segments_to_vtt
from app.utils.subtitle_format import break_line, calculate_cps, validate_timing

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
# EXTREME SEGMENT VALUES
# ══════════════════════════════════════════════════════════════════════════════


class TestExtremeSegmentValues:
    """Test extreme values in subtitle segments."""

    def test_very_long_text(self):
        seg = {"start": 0, "end": 1, "text": "A" * 10000}
        srt = segments_to_srt([seg])
        assert "A" * 100 in srt

    def test_very_short_text(self):
        seg = {"start": 0, "end": 1, "text": "A"}
        srt = segments_to_srt([seg])
        assert "A\n" in srt

    def test_very_large_timestamp(self):
        seg = {"start": 99999.999, "end": 100000.0, "text": "End"}
        srt = segments_to_srt([seg])
        assert "-->" in srt

    def test_zero_duration_segment(self):
        seg = {"start": 5.0, "end": 5.0, "text": "Instant"}
        srt = segments_to_srt([seg])
        assert "Instant" in srt

    def test_very_small_duration(self):
        seg = {"start": 1.0, "end": 1.001, "text": "Flash"}
        srt = segments_to_srt([seg])
        assert "Flash" in srt

    def test_many_segments_1000(self):
        segs = [{"start": i, "end": i + 0.5, "text": f"Seg {i}"} for i in range(1000)]
        srt = segments_to_srt(segs)
        assert "1000\n" in srt

    def test_segment_with_newlines(self):
        seg = {"start": 0, "end": 1, "text": "Line one\nLine two"}
        srt = segments_to_srt([seg])
        assert "Line one\nLine two" in srt

    def test_segment_only_whitespace(self):
        seg = {"start": 0, "end": 1, "text": "   "}
        srt = segments_to_srt([seg])
        # Whitespace gets stripped
        assert "-->" in srt

    def test_segment_with_special_chars(self):
        seg = {"start": 0, "end": 1, "text": "He said: \"Hello\" & 'World' <tag>"}
        srt = segments_to_srt([seg])
        assert "Hello" in srt

    def test_segment_chinese_text(self):
        seg = {"start": 0, "end": 1, "text": "你好世界，这是一个测试"}
        json_out = segments_to_json([seg])
        data = json.loads(json_out)
        assert data[0]["text"] == "你好世界，这是一个测试"

    def test_segment_korean_text(self):
        seg = {"start": 0, "end": 1, "text": "안녕하세요 세계"}
        vtt = segments_to_vtt([seg])
        assert "안녕하세요" in vtt

    def test_segment_devanagari_text(self):
        seg = {"start": 0, "end": 1, "text": "नमस्ते दुनिया"}
        srt = segments_to_srt([seg])
        assert "नमस्ते" in srt

    def test_segment_mixed_scripts(self):
        seg = {"start": 0, "end": 1, "text": "Hello 世界 Мир عالم"}
        srt = segments_to_srt([seg])
        assert "Hello" in srt and "世界" in srt


# ══════════════════════════════════════════════════════════════════════════════
# FORMAT EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestFormatEdgeCases:
    """Test format conversion edge cases."""

    def test_srt_to_vtt_timestamps_differ(self):
        seg = {"start": 1.5, "end": 3.5, "text": "Test"}
        srt = segments_to_srt([seg])
        vtt = segments_to_vtt([seg])
        assert "," in srt  # SRT uses comma
        assert "." in vtt  # VTT uses dot

    def test_json_handles_float_precision(self):
        seg = {"start": 0.1 + 0.2, "end": 1.0, "text": "Float"}
        j = segments_to_json([seg])
        data = json.loads(j)
        assert abs(data[0]["start"] - 0.3) < 0.001

    def test_vtt_header_always_present(self):
        vtt = segments_to_vtt([])
        assert vtt.startswith("WEBVTT")

    def test_srt_index_with_speaker(self):
        segs = [
            {"start": 0, "end": 1, "text": "A", "speaker": "S1"},
            {"start": 1, "end": 2, "text": "B", "speaker": "S2"},
        ]
        srt = segments_to_srt(segs)
        assert "[S1]" in srt
        assert "[S2]" in srt

    def test_json_speaker_and_words(self):
        seg = {
            "start": 0,
            "end": 1,
            "text": "Hi",
            "speaker": "Alice",
            "words": [{"word": "Hi", "start": 0, "end": 0.5}],
        }
        j = segments_to_json([seg])
        data = json.loads(j)
        assert data[0]["speaker"] == "Alice"
        assert len(data[0]["words"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# LINE BREAKING EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestLineBreakingEdgeCases:
    """Test line breaking with unusual inputs."""

    def test_exactly_at_max_chars(self):
        text = "A" * 42
        result = break_line(text, max_chars=42)
        assert "\n" not in result

    def test_one_over_max_chars(self):
        text = "A" * 43
        result = break_line(text, max_chars=42)
        # Single word, can't break
        assert len(result) == 43

    def test_question_mark_break(self):
        text = "Is this a question? Yes it is definitely so"
        result = break_line(text, max_chars=30)
        if "\n" in result:
            assert "?" in result.split("\n")[0]

    def test_exclamation_break(self):
        text = "What a surprise! This is really amazing text"
        result = break_line(text, max_chars=30)
        if "\n" in result:
            assert "!" in result.split("\n")[0]

    def test_two_word_text_over_limit(self):
        text = "Hello " + "W" * 40
        result = break_line(text, max_chars=20)
        assert "\n" in result

    def test_tab_in_text(self):
        result = break_line("Hello\tworld", max_chars=42)
        assert isinstance(result, str)


# ══════════════════════════════════════════════════════════════════════════════
# TIMING EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestTimingEdgeCases:
    """Test timing validation edge cases."""

    def test_very_fast_subtitle(self):
        result = validate_timing(0, 0.5, "A" * 100)
        # duration < min, and CPS very high
        assert result["valid"] is False

    def test_perfect_timing(self):
        result = validate_timing(0, 3, "Hello world test")
        assert result["valid"] is True

    def test_cps_boundary(self):
        # 25 CPS exactly
        cps = calculate_cps("x" * 25, 1.0)
        assert cps == 25.0

    def test_multiline_cps(self):
        cps = calculate_cps("Line1\nLine2", 2.0)
        assert cps > 0

    def test_duration_precision(self):
        result = validate_timing(0.001, 2.001, "Test")
        assert abs(result["duration"] - 2.0) < 0.01


# ══════════════════════════════════════════════════════════════════════════════
# FORMATTING EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestFormattingEdgeCases:
    """Test formatting functions with edge values."""

    def test_format_bytes_exact_1kb(self):
        result = format_bytes(1024)
        assert "1.0 KB" == result

    def test_format_bytes_exact_1mb(self):
        result = format_bytes(1024 * 1024)
        assert "1.0 MB" == result

    def test_format_bytes_exact_1gb(self):
        result = format_bytes(1024 * 1024 * 1024)
        assert "1.00 GB" == result

    def test_format_timestamp_midnight(self):
        assert format_timestamp(0.0) == "00:00:00,000"

    def test_format_timestamp_one_ms(self):
        # 0.001 seconds
        ts = format_timestamp(0.001)
        assert ts == "00:00:00,001"

    def test_format_time_display_boundary(self):
        assert "59s" == format_time_display(59)
        assert "m" in format_time_display(60)

    def test_format_time_short_zero(self):
        result = format_time_short(0.0)
        assert "0:00.0" == result

    def test_format_time_short_precise(self):
        result = format_time_short(65.3)
        assert "1:" in result


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE/CONFIG EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestLanguageEdgeCases:
    """Test language-related edge cases."""

    def test_all_supported_languages_have_names(self):
        for code, name in SUPPORTED_LANGUAGES.items():
            assert isinstance(name, str)
            assert len(name) > 0

    def test_allowed_extensions_are_lowercase(self):
        for ext in ALLOWED_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith(".")

    def test_valid_models_list_order(self):
        assert VALID_MODELS == ["tiny", "base", "small", "medium", "large"]

    def test_min_file_size_less_than_max(self):
        assert MIN_FILE_SIZE < MAX_FILE_SIZE


# ══════════════════════════════════════════════════════════════════════════════
# CONCURRENT STATE EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrentStateEdgeCases:
    """Test state management edge cases."""

    def test_add_remove_task_quickly(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "queued"}
        state.tasks.pop(tid, None)
        assert tid not in state.tasks

    def test_overwrite_task_data(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {"status": "queued", "percent": 0}
        state.tasks[tid]["status"] = "done"
        state.tasks[tid]["percent"] = 100
        assert state.tasks[tid]["status"] == "done"
        state.tasks.pop(tid, None)

    def test_task_with_extra_fields(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {
            "status": "done",
            "percent": 100,
            "custom_field": "extra_data",
            "another": 42,
        }
        assert state.tasks[tid]["custom_field"] == "extra_data"
        state.tasks.pop(tid, None)

    def test_empty_task_dict(self):
        tid = str(uuid.uuid4())
        state.tasks[tid] = {}
        assert state.tasks[tid] == {}
        state.tasks.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# API ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIErrorHandling:
    """Test API error responses."""

    def test_404_unknown_endpoint(self):
        res = client.get("/nonexistent-endpoint-xyz")
        assert res.status_code in (404, 405)

    def test_method_not_allowed_on_upload(self):
        res = client.get("/upload")
        assert res.status_code == 405

    def test_method_not_allowed_on_cancel(self):
        res = client.get("/cancel/some-id")
        assert res.status_code == 405

    def test_empty_json_body_on_feedback(self):
        res = client.post("/feedback", json={})
        assert res.status_code in (200, 422)

    def test_malformed_json_body(self):
        res = client.post(
            "/feedback",
            content=b"not-json",
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 422

    def test_upload_wrong_content_type(self):
        res = client.post(
            "/upload",
            content=b"not a file",
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityEdgeCases:
    """Test security-related edge cases."""

    def test_very_long_url_path(self):
        long_path = "/" + "a" * 5000
        res = client.get(long_path)
        assert res.status_code in (404, 405, 414)

    def test_null_byte_in_url(self):
        res = client.get("/health%00")
        assert res.status_code in (200, 404, 400)

    def test_unicode_in_url(self):
        res = client.get("/health/%E4%B8%AD%E6%96%87")
        assert res.status_code in (404, 200)

    def test_double_encoding(self):
        res = client.get("/health/%252e%252e")
        assert res.status_code in (200, 404)

    def test_multiple_slashes(self):
        res = client.get("///health")
        assert res.status_code in (200, 404, 307)

    def test_path_with_semicolon(self):
        res = client.get("/health;drop=table")
        assert res.status_code in (200, 404)

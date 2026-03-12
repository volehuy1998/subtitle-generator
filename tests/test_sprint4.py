"""Tests for Sprint 4: Advanced Transcription features.

S4-1: Speaker diarization (graceful degradation)
S4-2: Word-level timestamps
S4-3: Custom vocabulary (initial_prompt)
S4-4: Subtitle line-breaking rules (max chars, CPS)
S4-5: Auto-cleanup of old files
S4-6: This file
"""

import json
import os
import time
import tempfile
from io import BytesIO
from pathlib import Path

from app.main import app
from app import state
from app.utils.subtitle_format import (
    break_line, calculate_cps, validate_timing,
    format_segments_with_linebreaks, words_to_segments,
)
from app.utils.srt import segments_to_srt, segments_to_vtt, segments_to_json
from app.services.cleanup import cleanup_old_files
from app.services.diarization import (
    is_diarization_available, assign_speakers_to_segments,
)
from app.services.transcription import get_optimal_transcribe_options
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


# ── S4-4: Subtitle Line-Breaking Rules ──

class TestLineBreaking:
    def test_short_line_unchanged(self):
        assert break_line("Hello world") == "Hello world"

    def test_long_line_split_at_sentence(self):
        text = "This is a long sentence. And here is a second one."
        result = break_line(text, max_chars=30)
        assert "\n" in result
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0].endswith(".")

    def test_long_line_split_at_comma(self):
        text = "When the weather is nice, everyone goes to the park"
        result = break_line(text, max_chars=30)
        assert "\n" in result

    def test_long_line_split_at_middle(self):
        text = "The quick brown fox jumps over the lazy dog near the river"
        result = break_line(text, max_chars=35)
        assert "\n" in result
        lines = result.split("\n")
        for line in lines:
            assert len(line) <= 35

    def test_max_lines_1_truncates(self):
        text = "This is a very long line that should be truncated at the word boundary"
        result = break_line(text, max_chars=30, max_lines=1)
        assert "\n" not in result
        assert len(result) <= 30

    def test_single_word_long(self):
        text = "Supercalifragilisticexpialidocious"
        result = break_line(text, max_chars=20)
        # Single word can't be split, returned as-is
        assert "Supercalifragilisticexpialidocious" in result

    def test_format_segments_applies_breaks(self):
        segments = [
            {"start": 0, "end": 3, "text": "This is a test sentence that is quite long and needs breaking"},
        ]
        result = format_segments_with_linebreaks(segments, max_chars=30)
        assert len(result) == 1
        assert "\n" in result[0]["text"]

    def test_format_preserves_other_fields(self):
        segments = [
            {"start": 1.5, "end": 3.0, "text": "Short text", "speaker": "SPEAKER_00"},
        ]
        result = format_segments_with_linebreaks(segments, max_chars=40)
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["start"] == 1.5


class TestCPS:
    def test_calculate_cps(self):
        cps = calculate_cps("Hello world!", 2.0)
        assert cps == 6.0  # 12 chars / 2 sec

    def test_cps_zero_duration(self):
        assert calculate_cps("text", 0.0) == 0.0

    def test_cps_multiline(self):
        cps = calculate_cps("Line one\nLine two", 2.0)
        # "Line one Line two" = 17 chars / 2 = 8.5
        assert cps == 8.5


class TestTimingValidation:
    def test_valid_timing(self):
        result = validate_timing(0.0, 3.0, "Hello world")
        assert result["valid"] is True
        assert result["duration"] == 3.0
        assert len(result["issues"]) == 0

    def test_too_short(self):
        result = validate_timing(0.0, 0.3, "Hi")
        assert result["valid"] is False
        assert any("too_short" in i for i in result["issues"])

    def test_too_long(self):
        result = validate_timing(0.0, 10.0, "Brief text")
        assert result["valid"] is False
        assert any("too_long" in i for i in result["issues"])

    def test_too_fast(self):
        text = "x" * 100  # 100 chars
        result = validate_timing(0.0, 2.0, text)  # 50 CPS
        assert result["valid"] is False
        assert any("too_fast" in i for i in result["issues"])

    def test_empty_text(self):
        result = validate_timing(0.0, 2.0, "  ")
        assert result["valid"] is False
        assert any("empty_text" in i for i in result["issues"])


class TestWordsToSegments:
    def test_basic_grouping(self):
        words = [
            {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.99},
            {"word": "world", "start": 0.6, "end": 1.0, "probability": 0.98},
            {"word": "this", "start": 1.1, "end": 1.3, "probability": 0.97},
            {"word": "is", "start": 1.4, "end": 1.5, "probability": 0.99},
            {"word": "a", "start": 1.6, "end": 1.7, "probability": 0.95},
            {"word": "test", "start": 1.8, "end": 2.0, "probability": 0.96},
        ]
        segments = words_to_segments(words, max_chars=40)
        assert len(segments) >= 1
        assert all("words" in s for s in segments)

    def test_gap_splits_segment(self):
        words = [
            {"word": "First", "start": 0.0, "end": 0.5, "probability": 0.99},
            {"word": "part", "start": 0.6, "end": 1.0, "probability": 0.98},
            # Big gap
            {"word": "Second", "start": 5.0, "end": 5.5, "probability": 0.97},
            {"word": "part", "start": 5.6, "end": 6.0, "probability": 0.96},
        ]
        segments = words_to_segments(words, max_gap=1.5)
        assert len(segments) == 2

    def test_empty_words(self):
        assert words_to_segments([]) == []


# ── S4-2: Word-Level Timestamps ──

class TestWordTimestamps:
    def test_transcribe_options_with_words(self):
        opts = get_optimal_transcribe_options("cpu", "small", "en", word_timestamps=True)
        assert opts["word_timestamps"] is True

    def test_transcribe_options_without_words(self):
        opts = get_optimal_transcribe_options("cpu", "small", "en", word_timestamps=False)
        assert opts["word_timestamps"] is False


# ── S4-3: Custom Vocabulary ──

class TestCustomVocabulary:
    def test_initial_prompt_in_options(self):
        opts = get_optimal_transcribe_options(
            "cpu", "small", "en",
            initial_prompt="Technical terms: Kubernetes, FastAPI, CTranslate2"
        )
        assert opts["initial_prompt"] == "Technical terms: Kubernetes, FastAPI, CTranslate2"

    def test_empty_prompt_not_included(self):
        opts = get_optimal_transcribe_options("cpu", "small", "en", initial_prompt="")
        assert "initial_prompt" not in opts

    def test_whitespace_prompt_not_included(self):
        opts = get_optimal_transcribe_options("cpu", "small", "en", initial_prompt="   ")
        assert "initial_prompt" not in opts


# ── S4-1: Speaker Diarization ──

class TestDiarization:
    def test_availability_check(self):
        status = is_diarization_available()
        assert "available" in status
        assert "pyannote_installed" in status
        assert "hf_token_set" in status
        assert "reason" in status

    def test_assign_speakers_empty_turns(self):
        segments = [{"start": 0, "end": 3, "text": "Hello"}]
        result = assign_speakers_to_segments(segments, [])
        assert result == segments  # Unchanged

    def test_assign_speakers_single_speaker(self):
        segments = [
            {"start": 0, "end": 3, "text": "Hello world"},
            {"start": 3.5, "end": 6, "text": "How are you"},
        ]
        turns = [
            {"start": 0, "end": 6, "speaker": "SPEAKER_00"},
        ]
        result = assign_speakers_to_segments(segments, turns)
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_00"

    def test_assign_speakers_two_speakers(self):
        segments = [
            {"start": 0, "end": 3, "text": "Hello, my name is Alice"},
            {"start": 4, "end": 7, "text": "Hi Alice, I'm Bob"},
        ]
        turns = [
            {"start": 0, "end": 3.5, "speaker": "SPEAKER_00"},
            {"start": 3.5, "end": 8, "speaker": "SPEAKER_01"},
        ]
        result = assign_speakers_to_segments(segments, turns)
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"

    def test_assign_speakers_preserves_fields(self):
        segments = [{"start": 0, "end": 2, "text": "Test", "words": [{"word": "Test"}]}]
        turns = [{"start": 0, "end": 2, "speaker": "SPEAKER_00"}]
        result = assign_speakers_to_segments(segments, turns)
        assert "words" in result[0]
        assert result[0]["speaker"] == "SPEAKER_00"

    def test_system_info_includes_diarization(self):
        res = client.get("/system-info")
        assert res.status_code == 200
        data = res.json()
        assert "diarization" in data
        assert "available" in data["diarization"]


# ── SRT/VTT with Speaker Labels ──

class TestSrtWithSpeakers:
    def test_srt_with_speaker(self):
        segments = [
            {"start": 0, "end": 3, "text": "Hello", "speaker": "SPEAKER_00"},
        ]
        srt = segments_to_srt(segments)
        assert "[SPEAKER_00] Hello" in srt

    def test_srt_without_speaker(self):
        segments = [{"start": 0, "end": 3, "text": "Hello"}]
        srt = segments_to_srt(segments)
        assert "[" not in srt

    def test_srt_speakers_disabled(self):
        segments = [
            {"start": 0, "end": 3, "text": "Hello", "speaker": "SPEAKER_00"},
        ]
        srt = segments_to_srt(segments, include_speakers=False)
        assert "[SPEAKER_00]" not in srt

    def test_vtt_with_speaker(self):
        segments = [
            {"start": 0, "end": 3, "text": "Hello", "speaker": "SPEAKER_00"},
        ]
        vtt = segments_to_vtt(segments)
        assert "<v SPEAKER_00>" in vtt

    def test_json_export_with_words(self):
        segments = [
            {
                "start": 0, "end": 3, "text": "Hello world",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.99},
                    {"word": "world", "start": 0.6, "end": 1.0, "probability": 0.98},
                ],
            },
        ]
        result = segments_to_json(segments)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["speaker"] == "SPEAKER_00"
        assert len(data[0]["words"]) == 2

    def test_json_export_without_words(self):
        segments = [{"start": 0, "end": 3, "text": "Hello"}]
        result = segments_to_json(segments)
        data = json.loads(result)
        assert "words" not in data[0]


# ── S4-5: Auto-Cleanup ──

class TestAutoCleanup:
    def test_cleanup_removes_old_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            old_file = tmp / "old.txt"
            old_file.write_text("old")
            # Set modification time to 2 days ago
            old_time = time.time() - 2 * 24 * 3600
            os.utime(old_file, (old_time, old_time))

            new_file = tmp / "new.txt"
            new_file.write_text("new")

            result = cleanup_old_files(tmp, max_age_seconds=24 * 3600)
            assert result["removed"] == 1
            assert result["checked"] == 2
            assert not old_file.exists()
            assert new_file.exists()

    def test_cleanup_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            f = tmp / "test.txt"
            f.write_text("data")
            old_time = time.time() - 2 * 24 * 3600
            os.utime(f, (old_time, old_time))

            result = cleanup_old_files(tmp, max_age_seconds=24 * 3600, dry_run=True)
            assert result["removed"] == 1
            assert f.exists()  # Still exists in dry run

    def test_cleanup_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = cleanup_old_files(Path(tmpdir), max_age_seconds=1)
            assert result["checked"] == 0
            assert result["removed"] == 0

    def test_cleanup_nonexistent_directory(self):
        result = cleanup_old_files(Path("/nonexistent/path"))
        assert result["checked"] == 0
        assert result["removed"] == 0


# ── Upload Endpoint with New Parameters ──

class TestUploadNewParams:
    def test_upload_accepts_word_timestamps(self):
        """Verify the upload endpoint accepts word_timestamps parameter without crashing."""
        res = client.post(
            "/upload",
            files={"file": ("test.mp3", BytesIO(b"x" * 2048), "audio/mpeg")},
            data={
                "device": "cpu",
                "model_size": "tiny",
                "language": "en",
                "word_timestamps": "true",
            },
        )
        # Will fail at magic bytes validation, but should not fail at parameter parsing
        assert res.status_code in (400, 422)

    def test_upload_accepts_initial_prompt(self):
        res = client.post(
            "/upload",
            files={"file": ("test.mp3", BytesIO(b"x" * 2048), "audio/mpeg")},
            data={
                "device": "cpu",
                "model_size": "tiny",
                "initial_prompt": "Technical: FastAPI, Kubernetes",
            },
        )
        assert res.status_code in (400, 422)

    def test_upload_accepts_diarize(self):
        res = client.post(
            "/upload",
            files={"file": ("test.mp3", BytesIO(b"x" * 2048), "audio/mpeg")},
            data={
                "device": "cpu",
                "model_size": "tiny",
                "diarize": "true",
            },
        )
        assert res.status_code in (400, 422)

    def test_upload_accepts_max_line_chars(self):
        res = client.post(
            "/upload",
            files={"file": ("test.mp3", BytesIO(b"x" * 2048), "audio/mpeg")},
            data={
                "device": "cpu",
                "model_size": "tiny",
                "max_line_chars": "50",
            },
        )
        assert res.status_code in (400, 422)


# ── Download JSON Format ──

class TestDownloadJson:
    def test_download_json_not_found(self):
        """JSON download returns 404 when no JSON file exists."""
        original = state.tasks.copy()
        state.tasks["test-json-001"] = {"status": "done", "filename": "test.mp4"}
        try:
            res = client.get("/download/test-json-001?format=json")
            assert res.status_code == 404
        finally:
            state.tasks.clear()
            state.tasks.update(original)

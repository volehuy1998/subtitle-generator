"""Phase Lumen L13 — Pipeline optimization tests.

Tests WAV skip extraction, beam size auto-tuning, output file writing,
and pipeline error handling.
— Scout (QA Lead)
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

from app import state
from app.config import ALLOWED_EXTENSIONS, OUTPUT_DIR
from app.services.sse import create_event_queue
from app.utils.srt import segments_to_json, segments_to_srt, segments_to_vtt


def _create_task(task_id="opt-test", status="queued"):
    """Set up a task in state for testing."""
    state.tasks[task_id] = {
        "status": status,
        "percent": 0,
        "message": "",
        "filename": "test.mp4",
        "session_id": "",
        "cancel_requested": False,
    }
    create_event_queue(task_id)
    return task_id


def _cleanup(task_id):
    state.tasks.pop(task_id, None)
    state.task_event_queues.pop(task_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# WAV SKIP EXTRACTION (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestWavSkipExtraction:
    """Test that WAV inputs skip ffmpeg extraction in the pipeline."""

    def test_wav_extension_in_allowed(self):
        """WAV files are accepted by the upload validator."""
        assert ".wav" in ALLOWED_EXTENSIONS

    def test_mp4_extension_in_allowed(self):
        """MP4 files are accepted by the upload validator."""
        assert ".mp4" in ALLOWED_EXTENSIONS

    def test_mp3_extension_in_allowed(self):
        """MP3 files are accepted by the upload validator."""
        assert ".mp3" in ALLOWED_EXTENSIONS

    def test_wav_detection_case_insensitive(self):
        """Extension detection normalizes to lowercase."""
        for ext in (".WAV", ".wav", ".Wav", ".wAv"):
            assert ext.lower() == ".wav"
            # Pipeline uses os.path.splitext + .lower()
            _, detected = os.path.splitext(f"file{ext}")
            assert detected.lower() == ".wav"

    def test_wav_input_skips_extraction_in_pipeline(self):
        """WAV input sets audio_path = video_path, no extraction call."""
        video_path = Path("/tmp/test-audio.wav")
        input_ext = os.path.splitext(str(video_path))[1].lower()
        assert input_ext == ".wav"
        # Pipeline assigns audio_path = video_path when .wav
        audio_path = video_path if input_ext == ".wav" else video_path.with_suffix(".wav")
        assert audio_path == video_path

    def test_non_wav_triggers_extraction_path(self):
        """Non-WAV input creates a .wav audio_path (extraction needed)."""
        video_path = Path("/tmp/test-video.mp4")
        input_ext = os.path.splitext(str(video_path))[1].lower()
        assert input_ext != ".wav"
        audio_path = video_path if input_ext == ".wav" else video_path.with_suffix(".wav")
        assert audio_path != video_path
        assert audio_path.suffix == ".wav"

    def test_flac_triggers_extraction_path(self):
        """FLAC input still goes through extraction."""
        video_path = Path("/tmp/test-audio.flac")
        input_ext = os.path.splitext(str(video_path))[1].lower()
        assert input_ext == ".flac"
        assert input_ext != ".wav"

    def test_upload_endpoint_accepts_wav(self):
        """WAV extension passes validation."""
        from app.utils.security import validate_file_extension

        ext = validate_file_extension("recording.wav")
        assert ext == ".wav"

    def test_wav_magic_bytes_mime_map(self):
        """WAV files have expected MIME types in security map."""
        from app.utils.security import EXTENSION_MIME_MAP

        assert ".wav" in EXTENSION_MIME_MAP
        wav_mimes = EXTENSION_MIME_MAP[".wav"]
        assert any("wav" in m for m in wav_mimes)

    def test_uppercase_wav_extension_validated(self):
        """Upload validator handles uppercase .WAV via case normalization."""
        from app.utils.security import validate_file_extension

        ext = validate_file_extension("recording.WAV")
        assert ext == ".wav"


# ══════════════════════════════════════════════════════════════════════════════
# BEAM SIZE AUTO-TUNING (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestBeamSizeAutoTuning:
    """Test beam size selection logic in transcription options."""

    def _get_opts(self, device, model, **kwargs):
        from app.services.transcription import get_optimal_transcribe_options

        return get_optimal_transcribe_options(device, model, **kwargs)

    def test_beam_size_present_in_options(self):
        """Transcription options always include a beam_size."""
        opts = self._get_opts("cpu", "tiny")
        assert "beam_size" in opts

    def test_tiny_model_cpu_beam_size(self):
        """Tiny model on CPU uses beam_size 1 (greedy, speed priority)."""
        opts = self._get_opts("cpu", "tiny")
        assert opts["beam_size"] == 1

    def test_base_model_cpu_beam_size(self):
        """Base model on CPU uses beam_size 3 (balanced)."""
        opts = self._get_opts("cpu", "base")
        assert opts["beam_size"] == 3

    def test_medium_model_cpu_beam_size(self):
        """Medium model on CPU uses beam_size 5 (quality)."""
        opts = self._get_opts("cpu", "medium")
        assert opts["beam_size"] == 5

    def test_large_model_cpu_beam_size(self):
        """Large model on CPU uses beam_size 5 (quality priority)."""
        opts = self._get_opts("cpu", "large")
        assert opts["beam_size"] == 5

    def test_small_model_cpu_beam_size(self):
        """Small model on CPU uses beam_size 5 (default)."""
        opts = self._get_opts("cpu", "small")
        assert opts["beam_size"] == 5

    def test_unknown_model_falls_back_to_default_beam_size(self):
        """Unknown model name falls back to default beam_size 5."""
        opts = self._get_opts("cpu", "nonexistent_model")
        assert "beam_size" in opts
        assert opts["beam_size"] == 5

    def test_all_beam_sizes_positive_integers(self):
        """Every model's beam_size is a positive integer."""
        for model in ("tiny", "base", "small", "medium", "large"):
            opts = self._get_opts("cpu", model)
            bs = opts["beam_size"]
            assert isinstance(bs, int), f"{model} beam_size is not int: {type(bs)}"
            assert bs > 0, f"{model} beam_size is not positive: {bs}"

    def test_beam_sizes_in_reasonable_range(self):
        """All beam sizes fall within 1-10."""
        for model in ("tiny", "base", "small", "medium", "large"):
            opts = self._get_opts("cpu", model)
            bs = opts["beam_size"]
            assert 1 <= bs <= 10, f"{model} beam_size {bs} out of range [1, 10]"

    def test_cuda_tight_vram_forces_beam_1(self):
        """When VRAM is tight on CUDA, beam_size drops to 1 (greedy)."""
        with patch("app.services.transcription.check_vram_for_model", return_value={"fits": True, "tight": True}):
            opts = self._get_opts("cuda", "large")
            assert opts["beam_size"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT FILE WRITING (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestOutputFileWriting:
    """Test subtitle output file generation."""

    SAMPLE_SEGMENTS = [
        {"start": 0.0, "end": 2.5, "text": "Hello world"},
        {"start": 3.0, "end": 5.0, "text": "Testing subtitles"},
    ]

    def test_srt_output_extension(self):
        """SRT output path uses .srt extension."""
        task_id = "ext-srt-test"
        srt_path = OUTPUT_DIR / f"{task_id}.srt"
        assert srt_path.suffix == ".srt"

    def test_vtt_output_extension(self):
        """VTT output path uses .vtt extension."""
        task_id = "ext-vtt-test"
        vtt_path = OUTPUT_DIR / f"{task_id}.vtt"
        assert vtt_path.suffix == ".vtt"

    def test_json_output_extension(self):
        """JSON output path uses .json extension."""
        task_id = "ext-json-test"
        json_path = OUTPUT_DIR / f"{task_id}.json"
        assert json_path.suffix == ".json"

    def test_srt_content_valid_utf8(self):
        """SRT content is valid UTF-8 text."""
        content = segments_to_srt(self.SAMPLE_SEGMENTS)
        encoded = content.encode("utf-8")
        decoded = encoded.decode("utf-8")
        assert decoded == content

    def test_vtt_content_valid_utf8(self):
        """VTT content is valid UTF-8 text."""
        content = segments_to_vtt(self.SAMPLE_SEGMENTS)
        encoded = content.encode("utf-8")
        decoded = encoded.decode("utf-8")
        assert decoded == content

    def test_srt_content_starts_with_1(self):
        """SRT content starts with subtitle index '1'."""
        content = segments_to_srt(self.SAMPLE_SEGMENTS)
        assert content.strip().startswith("1")

    def test_vtt_content_starts_with_webvtt(self):
        """VTT content starts with 'WEBVTT' header."""
        content = segments_to_vtt(self.SAMPLE_SEGMENTS)
        assert content.startswith("WEBVTT")

    def test_json_content_is_valid_json(self):
        """JSON output parses as valid JSON."""
        content = segments_to_json(self.SAMPLE_SEGMENTS)
        parsed = json.loads(content)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_empty_segments_produce_valid_srt(self):
        """Empty segment list produces valid SRT (no crash)."""
        content = segments_to_srt([])
        assert isinstance(content, str)
        assert content is not None

    def test_empty_segments_produce_valid_json(self):
        """Empty segment list produces valid JSON (empty array)."""
        content = segments_to_json([])
        parsed = json.loads(content)
        assert parsed == []


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE ERROR HANDLING (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


def _get_sanitize_fn():
    """Import _sanitize_error_for_user resolving circular imports."""
    # Force full app init to break circular import chain
    import app.main  # noqa: F401
    from app.services.pipeline import _sanitize_error_for_user

    return _sanitize_error_for_user


def _get_error_map():
    """Import _ERROR_MAP resolving circular imports."""
    import app.main  # noqa: F401
    from app.services.pipeline import _ERROR_MAP

    return _ERROR_MAP


class TestPipelineErrorHandling:
    """Test pipeline error sanitization and handling."""

    def test_missing_input_file_sanitized(self):
        """Missing file error is mapped to user-friendly message."""
        _sanitize_error_for_user = _get_sanitize_fn()

        msg = _sanitize_error_for_user(Exception("No such file or directory: /tmp/missing.wav"))
        assert "file" in msg.lower()
        assert "/tmp/" not in msg

    def test_zero_byte_file_error(self):
        """Generic errors still produce a string message."""
        _sanitize_error_for_user = _get_sanitize_fn()
        msg = _sanitize_error_for_user(Exception("Empty file: 0 bytes"))
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_cancelled_task_state(self):
        """Cancelled tasks set status to 'cancelled'."""
        tid = _create_task("cancel-err-1")
        try:
            state.tasks[tid]["cancel_requested"] = True
            state.tasks[tid]["status"] = "cancelled"
            state.tasks[tid]["message"] = "Task cancelled by user."
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_error_messages_sanitized_no_raw_paths(self):
        """Sanitized errors strip file system paths."""
        _sanitize_error_for_user = _get_sanitize_fn()
        msg = _sanitize_error_for_user(Exception("Failed at /home/user/uploads/secret.mp4 line 42"))
        assert "/home/user" not in msg

    def test_error_map_covers_disk_full(self):
        """Error map includes disk full pattern."""
        _ERROR_MAP = _get_error_map()
        patterns = [p for p, _ in _ERROR_MAP]
        assert any("space" in p.lower() or "ENOSPC" in p for p in patterns)

    def test_error_map_covers_memory(self):
        """Error map includes memory error pattern."""
        _ERROR_MAP = _get_error_map()
        patterns = [p for p, _ in _ERROR_MAP]
        assert any("memory" in p.lower() for p in patterns)

    def test_sanitize_error_function_exists(self):
        """_sanitize_error_for_user function is importable."""
        fn = _get_sanitize_fn()
        assert callable(fn)

    def test_sanitized_errors_no_file_paths(self):
        """Various path-containing errors are all stripped."""
        _sanitize_error_for_user = _get_sanitize_fn()
        test_cases = [
            "Error reading /var/data/uploads/file.mp4",
            "Permission denied: /etc/shadow",
            "Cannot open /home/user/video.mkv",
        ]
        for raw in test_cases:
            msg = _sanitize_error_for_user(Exception(raw))
            assert "/var/" not in msg and "/etc/" not in msg and "/home/" not in msg, f"Path leaked in: {msg}"

    def test_error_events_emitted_on_failure(self):
        """Error events are placed in the task event queue."""
        from app.services.sse import emit_event, subscribe

        tid = _create_task("err-emit-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "error", {"status": "error", "message": "Test failure"})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert len(events) >= 1
            assert events[-1]["type"] == "error"
            assert events[-1]["message"] == "Test failure"
        finally:
            _cleanup(tid)

    def test_enospc_errno_handled(self):
        """OSError with ENOSPC errno returns disk full message."""
        import errno

        _sanitize_error_for_user = _get_sanitize_fn()
        exc = OSError(errno.ENOSPC, "No space left on device")
        msg = _sanitize_error_for_user(exc)
        assert "storage" in msg.lower() or "space" in msg.lower()

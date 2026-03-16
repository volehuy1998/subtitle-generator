"""Sprint L14: Transcription configuration, VAD, compute type, and API config tests.

Tests validate that transcription options, VAD parameters, compute type selection,
and API configuration constants are correct and consistent.

— Scout (QA Lead)
"""

from pathlib import Path

from app.config import (
    FFMPEG_AVAILABLE,
    FFPROBE_AVAILABLE,
    MAX_CONCURRENT_TASKS,
    MAX_FILE_SIZE,
    MIN_FILE_SIZE,
    OUTPUT_DIR,
    SUPPORTED_LANGUAGES,
    UPLOAD_DIR,
    VALID_MODELS,
)
from app.services.model_manager import get_compute_type
from app.services.transcription import get_optimal_transcribe_options


# ─────────────────────────────────────────────────────────────
# VAD Configuration (10 tests)
# ─────────────────────────────────────────────────────────────


class TestVADConfiguration:
    """Validate Voice Activity Detection configuration in transcription options."""

    def test_vad_filter_enabled_by_default(self):
        """Transcription options enable VAD filter by default."""
        opts = get_optimal_transcribe_options("cpu", "base")
        assert opts["vad_filter"] is True

    def test_vad_parameters_present(self):
        """Transcription options include vad_parameters dict."""
        opts = get_optimal_transcribe_options("cpu", "base")
        assert "vad_parameters" in opts
        assert isinstance(opts["vad_parameters"], dict)

    def test_vad_min_silence_duration_ms(self):
        """VAD parameters include min_silence_duration_ms."""
        opts = get_optimal_transcribe_options("cpu", "base")
        vad = opts["vad_parameters"]
        assert "min_silence_duration_ms" in vad
        assert isinstance(vad["min_silence_duration_ms"], int)
        assert vad["min_silence_duration_ms"] > 0

    def test_vad_speech_pad_ms(self):
        """VAD parameters include speech_pad_ms."""
        opts = get_optimal_transcribe_options("cpu", "base")
        vad = opts["vad_parameters"]
        assert "speech_pad_ms" in vad
        assert isinstance(vad["speech_pad_ms"], int)
        assert vad["speech_pad_ms"] > 0

    def test_vad_threshold_between_0_and_1(self):
        """VAD threshold is a float between 0 and 1."""
        opts = get_optimal_transcribe_options("cpu", "base")
        vad = opts["vad_parameters"]
        assert "threshold" in vad
        assert 0.0 < vad["threshold"] < 1.0

    def test_vad_threshold_is_numeric(self):
        """VAD threshold is a numeric type."""
        opts = get_optimal_transcribe_options("cpu", "base")
        threshold = opts["vad_parameters"]["threshold"]
        assert isinstance(threshold, (int, float))

    def test_vad_enabled_for_all_models(self):
        """VAD filter is enabled for every valid model size."""
        for model in VALID_MODELS:
            opts = get_optimal_transcribe_options("cpu", model)
            assert opts["vad_filter"] is True, f"VAD not enabled for model={model}"

    def test_vad_parameters_consistent_across_models(self):
        """VAD parameters are the same regardless of model size."""
        reference = get_optimal_transcribe_options("cpu", "tiny")["vad_parameters"]
        for model in VALID_MODELS[1:]:
            vad = get_optimal_transcribe_options("cpu", model)["vad_parameters"]
            assert vad == reference, f"VAD params differ for model={model}"

    def test_vad_min_silence_reasonable_range(self):
        """min_silence_duration_ms is within a reasonable range (100-2000ms)."""
        opts = get_optimal_transcribe_options("cpu", "base")
        ms = opts["vad_parameters"]["min_silence_duration_ms"]
        assert 100 <= ms <= 2000

    def test_vad_speech_pad_reasonable_range(self):
        """speech_pad_ms is within a reasonable range (50-500ms)."""
        opts = get_optimal_transcribe_options("cpu", "base")
        pad = opts["vad_parameters"]["speech_pad_ms"]
        assert 50 <= pad <= 500


# ─────────────────────────────────────────────────────────────
# Compute Type Selection (10 tests)
# ─────────────────────────────────────────────────────────────


class TestComputeTypeSelection:
    """Validate compute type selection logic for CPU and GPU."""

    def test_cpu_always_returns_int8(self):
        """CPU device always uses int8 compute type regardless of model."""
        for model in VALID_MODELS:
            assert get_compute_type("cpu", model) == "int8", f"CPU should use int8 for {model}"

    def test_gpu_small_models_use_float16(self):
        """GPU uses float16 for small models (tiny, base, small)."""
        for model in ("tiny", "base", "small"):
            assert get_compute_type("cuda", model) == "float16", f"GPU should use float16 for {model}"

    def test_gpu_large_model_uses_int8_float16(self):
        """GPU uses int8_float16 for the large model."""
        assert get_compute_type("cuda", "large") == "int8_float16"

    def test_gpu_medium_model_uses_int8_float16(self):
        """GPU uses int8_float16 for the medium model."""
        assert get_compute_type("cuda", "medium") == "int8_float16"

    def test_compute_type_returns_string(self):
        """Compute type is always a string."""
        for device in ("cpu", "cuda"):
            for model in VALID_MODELS:
                result = get_compute_type(device, model)
                assert isinstance(result, str), f"Expected string for {device}/{model}"

    def test_valid_compute_types_only(self):
        """All returned compute types are from the valid set."""
        valid_types = {"int8", "float16", "int8_float16", "auto"}
        for device in ("cpu", "cuda"):
            for model in VALID_MODELS:
                result = get_compute_type(device, model)
                assert result in valid_types, f"Invalid compute type '{result}' for {device}/{model}"

    def test_get_compute_type_function_exists(self):
        """get_compute_type is callable."""
        assert callable(get_compute_type)

    def test_cpu_int8_for_tiny(self):
        """CPU uses int8 even for the smallest model."""
        assert get_compute_type("cpu", "tiny") == "int8"

    def test_cpu_int8_for_large(self):
        """CPU uses int8 even for the largest model."""
        assert get_compute_type("cpu", "large") == "int8"

    def test_gpu_compute_types_differ_by_model_size(self):
        """GPU compute type differs between small and large models."""
        small_type = get_compute_type("cuda", "tiny")
        large_type = get_compute_type("cuda", "large")
        assert small_type != large_type


# ─────────────────────────────────────────────────────────────
# Transcription Options (10 tests)
# ─────────────────────────────────────────────────────────────


class TestTranscriptionOptions:
    """Validate transcription option generation and parameter handling."""

    def test_language_auto_omits_language_key(self):
        """When language='auto', the language key is not set in options."""
        opts = get_optimal_transcribe_options("cpu", "base", language="auto")
        assert "language" not in opts

    def test_language_explicit_sets_key(self):
        """When language is explicit (e.g. 'en'), it appears in options."""
        opts = get_optimal_transcribe_options("cpu", "base", language="en")
        assert opts["language"] == "en"

    def test_language_french_accepted(self):
        """French language code is accepted."""
        opts = get_optimal_transcribe_options("cpu", "base", language="fr")
        assert opts["language"] == "fr"

    def test_word_timestamps_parameter(self):
        """word_timestamps parameter is passed through to options."""
        opts = get_optimal_transcribe_options("cpu", "base", word_timestamps=True)
        assert opts["word_timestamps"] is True

    def test_word_timestamps_default_false(self):
        """word_timestamps defaults to False."""
        opts = get_optimal_transcribe_options("cpu", "base")
        assert opts["word_timestamps"] is False

    def test_initial_prompt_parameter(self):
        """initial_prompt is included when provided."""
        opts = get_optimal_transcribe_options("cpu", "base", initial_prompt="Technical vocabulary")
        assert opts["initial_prompt"] == "Technical vocabulary"

    def test_initial_prompt_stripped(self):
        """initial_prompt is stripped of whitespace."""
        opts = get_optimal_transcribe_options("cpu", "base", initial_prompt="  hello  ")
        assert opts["initial_prompt"] == "hello"

    def test_initial_prompt_empty_not_included(self):
        """Empty initial_prompt is not included in options."""
        opts = get_optimal_transcribe_options("cpu", "base", initial_prompt="")
        assert "initial_prompt" not in opts

    def test_beam_size_set_for_all_models(self):
        """beam_size is present in options for every valid model."""
        for model in VALID_MODELS:
            opts = get_optimal_transcribe_options("cpu", model)
            assert "beam_size" in opts, f"beam_size missing for {model}"
            assert isinstance(opts["beam_size"], int)
            assert opts["beam_size"] >= 1

    def test_all_valid_models_supported(self):
        """get_optimal_transcribe_options works for all VALID_MODELS."""
        assert len(VALID_MODELS) == 5
        expected = {"tiny", "base", "small", "medium", "large"}
        assert set(VALID_MODELS) == expected
        for model in VALID_MODELS:
            opts = get_optimal_transcribe_options("cpu", model)
            assert isinstance(opts, dict)


# ─────────────────────────────────────────────────────────────
# API Configuration (10 tests)
# ─────────────────────────────────────────────────────────────


class TestAPIConfiguration:
    """Validate API configuration constants from app.config."""

    def test_max_file_size_defined_and_positive(self):
        """MAX_FILE_SIZE is defined and greater than zero."""
        assert MAX_FILE_SIZE > 0

    def test_min_file_size_defined_and_positive(self):
        """MIN_FILE_SIZE is defined and greater than zero."""
        assert MIN_FILE_SIZE > 0

    def test_max_concurrent_tasks_defined_and_positive(self):
        """MAX_CONCURRENT_TASKS is defined and greater than zero."""
        assert MAX_CONCURRENT_TASKS > 0

    def test_upload_dir_is_path(self):
        """UPLOAD_DIR is a Path instance."""
        assert isinstance(UPLOAD_DIR, Path)

    def test_output_dir_is_path(self):
        """OUTPUT_DIR is a Path instance."""
        assert isinstance(OUTPUT_DIR, Path)

    def test_supported_languages_has_entries(self):
        """SUPPORTED_LANGUAGES is a dict with entries."""
        assert isinstance(SUPPORTED_LANGUAGES, dict)
        assert len(SUPPORTED_LANGUAGES) > 10

    def test_valid_models_contains_five_sizes(self):
        """VALID_MODELS contains all 5 model sizes."""
        assert len(VALID_MODELS) == 5
        for size in ("tiny", "base", "small", "medium", "large"):
            assert size in VALID_MODELS

    def test_max_file_size_at_least_1mb(self):
        """MAX_FILE_SIZE is at least 1 MB."""
        assert MAX_FILE_SIZE >= 1 * 1024 * 1024

    def test_ffmpeg_available_is_boolean(self):
        """FFMPEG_AVAILABLE is a boolean."""
        assert isinstance(FFMPEG_AVAILABLE, bool)

    def test_ffprobe_available_is_boolean(self):
        """FFPROBE_AVAILABLE is a boolean."""
        assert isinstance(FFPROBE_AVAILABLE, bool)

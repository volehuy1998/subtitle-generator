"""Phase Lumen L20 — Configuration validation tests.

Tests all configuration values are valid, consistent, and have sane defaults.
Validates types, ranges, and relationships between config constants.
— Scout (QA Lead)
"""

from pathlib import Path

from app import config


# ══════════════════════════════════════════════════════════════════════════════
# IMPORTABILITY & TYPES
# ══════════════════════════════════════════════════════════════════════════════


class TestConfigImportability:
    """All config constants are importable and have correct types."""

    def test_upload_dir_is_path(self):
        assert isinstance(config.UPLOAD_DIR, Path)

    def test_output_dir_is_path(self):
        assert isinstance(config.OUTPUT_DIR, Path)

    def test_log_dir_is_path(self):
        assert isinstance(config.LOG_DIR, Path)

    def test_base_dir_is_path(self):
        assert isinstance(config.BASE_DIR, Path)

    def test_template_dir_is_path(self):
        assert isinstance(config.TEMPLATE_DIR, Path)

    def test_upload_dir_exists(self):
        config.UPLOAD_DIR.mkdir(exist_ok=True)
        assert config.UPLOAD_DIR.exists()

    def test_output_dir_exists(self):
        config.OUTPUT_DIR.mkdir(exist_ok=True)
        assert config.OUTPUT_DIR.exists()


# ══════════════════════════════════════════════════════════════════════════════
# FILE SIZE CONSTRAINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestFileSizeConstraints:
    """File size limits are valid and consistent."""

    def test_max_file_size_greater_than_min(self):
        assert config.MAX_FILE_SIZE > config.MIN_FILE_SIZE

    def test_max_file_size_is_positive(self):
        assert config.MAX_FILE_SIZE > 0

    def test_min_file_size_is_positive(self):
        assert config.MIN_FILE_SIZE > 0

    def test_max_file_size_is_2gb(self):
        assert config.MAX_FILE_SIZE == 2 * 1024 * 1024 * 1024

    def test_min_file_size_is_1kb(self):
        assert config.MIN_FILE_SIZE == 1024


# ══════════════════════════════════════════════════════════════════════════════
# CONCURRENCY CONSTRAINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrencyConfig:
    """Concurrency settings have valid values."""

    def test_max_concurrent_tasks_at_least_1(self):
        assert config.MAX_CONCURRENT_TASKS >= 1

    def test_max_concurrent_tasks_is_int(self):
        assert isinstance(config.MAX_CONCURRENT_TASKS, int)


# ══════════════════════════════════════════════════════════════════════════════
# MODEL VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestModelConfig:
    """Whisper model configuration is valid."""

    def test_valid_models_has_5_entries(self):
        assert len(config.VALID_MODELS) == 5

    def test_valid_models_are_strings(self):
        for model in config.VALID_MODELS:
            assert isinstance(model, str), f"Model '{model}' is not a string"

    def test_valid_models_contains_expected(self):
        expected = {"tiny", "base", "small", "medium", "large"}
        assert set(config.VALID_MODELS) == expected

    def test_model_vram_gb_matches_valid_models(self):
        assert set(config.MODEL_VRAM_GB.keys()) == set(config.VALID_MODELS)

    def test_model_vram_gb_values_positive(self):
        for model, vram in config.MODEL_VRAM_GB.items():
            assert vram > 0, f"VRAM for '{model}' should be positive, got {vram}"


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SUPPORT
# ══════════════════════════════════════════════════════════════════════════════


class TestLanguageConfig:
    """Language support configuration is valid."""

    def test_supported_languages_has_at_least_10(self):
        assert len(config.SUPPORTED_LANGUAGES) >= 10

    def test_supported_languages_includes_auto(self):
        assert "auto" in config.SUPPORTED_LANGUAGES

    def test_supported_languages_includes_english(self):
        assert "en" in config.SUPPORTED_LANGUAGES

    def test_supported_languages_is_dict(self):
        assert isinstance(config.SUPPORTED_LANGUAGES, dict)

    def test_all_language_values_are_strings(self):
        for code, name in config.SUPPORTED_LANGUAGES.items():
            assert isinstance(code, str), f"Language code '{code}' is not a string"
            assert isinstance(name, str), f"Language name for '{code}' is not a string"
            assert len(name) > 0, f"Language name for '{code}' is empty"


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO/VIDEO EXTENSIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestExtensionConfig:
    """File extension sets are valid and consistent."""

    def test_video_extensions_is_set(self):
        assert isinstance(config.VIDEO_EXTENSIONS, (set, frozenset))

    def test_audio_only_extensions_is_set(self):
        assert isinstance(config.AUDIO_ONLY_EXTENSIONS, (set, frozenset))

    def test_allowed_extensions_is_set(self):
        assert isinstance(config.ALLOWED_EXTENSIONS, (set, frozenset))

    def test_video_extensions_not_empty(self):
        assert len(config.VIDEO_EXTENSIONS) > 0

    def test_audio_extensions_not_empty(self):
        assert len(config.AUDIO_ONLY_EXTENSIONS) > 0

    def test_allowed_extensions_superset_of_video(self):
        assert config.VIDEO_EXTENSIONS.issubset(config.ALLOWED_EXTENSIONS)

    def test_allowed_extensions_superset_of_audio(self):
        assert config.AUDIO_ONLY_EXTENSIONS.issubset(config.ALLOWED_EXTENSIONS)

    def test_all_extensions_start_with_dot(self):
        for ext in config.ALLOWED_EXTENSIONS:
            assert ext.startswith("."), f"Extension '{ext}' does not start with '.'"


# ══════════════════════════════════════════════════════════════════════════════
# FFMPEG AVAILABILITY FLAGS
# ══════════════════════════════════════════════════════════════════════════════


class TestFFmpegConfig:
    """FFmpeg availability flags are boolean."""

    def test_ffmpeg_available_is_bool(self):
        assert isinstance(config.FFMPEG_AVAILABLE, bool)

    def test_ffprobe_available_is_bool(self):
        assert isinstance(config.FFPROBE_AVAILABLE, bool)


# ══════════════════════════════════════════════════════════════════════════════
# AUDIO DURATION LIMIT
# ══════════════════════════════════════════════════════════════════════════════


class TestAudioDurationConfig:
    """Audio duration limit is valid."""

    def test_max_audio_duration_positive(self):
        assert config.MAX_AUDIO_DURATION > 0

    def test_max_audio_duration_is_numeric(self):
        assert isinstance(config.MAX_AUDIO_DURATION, (int, float))


# ══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════


class TestEnvironmentDefaults:
    """Default environment configuration is sane."""

    def test_default_environment_is_dev(self):
        # Unless overridden by env var, default is "dev"
        assert config.ENVIRONMENT in ("dev", "prod")

    def test_role_is_valid(self):
        assert config.ROLE in ("standalone", "web", "worker")

    def test_storage_backend_is_valid(self):
        assert config.STORAGE_BACKEND in ("local", "s3")

    def test_log_output_is_valid(self):
        assert config.LOG_OUTPUT in ("stdout", "file", "both", "json")

    def test_log_level_is_valid(self):
        assert config.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL")

    def test_db_pool_size_positive(self):
        assert config.DB_POOL_SIZE > 0

    def test_db_max_overflow_non_negative(self):
        assert config.DB_MAX_OVERFLOW >= 0

    def test_database_url_is_string(self):
        assert isinstance(config.DATABASE_URL, str)
        assert len(config.DATABASE_URL) > 0

    def test_translation_batch_size_positive(self):
        assert config.TRANSLATION_BATCH_SIZE > 0

    def test_static_cache_max_age_positive(self):
        assert config.STATIC_CACHE_MAX_AGE > 0

    def test_max_task_history_positive(self):
        assert config.MAX_TASK_HISTORY > 0

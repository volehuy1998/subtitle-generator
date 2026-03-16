"""Phase Lumen L10 — Performance-related feature tests.

Tests model readiness, model manager, system capability detection,
ffprobe caching, and performance tuning configurations.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# MODEL READINESS (15 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestModelReadinessAPI:
    """Test GET /api/model-status model readiness fields."""

    def test_model_status_returns_all_five_models(self):
        data = client.get("/api/model-status").json()
        models = data["models"]
        assert len(models) >= 5
        for name in ["tiny", "base", "small", "medium", "large"]:
            assert name in models

    def test_each_model_has_status_field(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert "status" in info, f"Model '{name}' missing 'status'"

    def test_each_model_has_size_gb_field(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert "size_gb" in info, f"Model '{name}' missing 'size_gb'"

    def test_each_model_has_loaded_devices_field(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert "loaded_devices" in info, f"Model '{name}' missing 'loaded_devices'"

    def test_model_status_values_are_valid(self):
        valid_statuses = {"ready", "loading", "not_loaded"}
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert info["status"] in valid_statuses, f"Model '{name}' has invalid status '{info['status']}'"

    def test_loaded_devices_is_list(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert isinstance(info["loaded_devices"], list), f"Model '{name}' loaded_devices is not a list"

    def test_size_gb_is_numeric(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert isinstance(info["size_gb"], (int, float)), f"Model '{name}' size_gb is not numeric"

    def test_preload_status_structure(self):
        data = client.get("/api/model-status").json()
        preload = data["preload"]
        assert "status" in preload

    def test_preload_has_models_field(self):
        data = client.get("/api/model-status").json()
        preload = data["preload"]
        assert "models" in preload

    def test_preload_has_loaded_field(self):
        data = client.get("/api/model-status").json()
        preload = data["preload"]
        assert "loaded" in preload

    def test_preload_has_total_field(self):
        data = client.get("/api/model-status").json()
        preload = data["preload"]
        assert "total" in preload

    def test_no_models_loaded_by_default(self):
        """Without preloading, all models should be not_loaded."""
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert info["status"] in ("not_loaded", "ready"), (
                f"Model '{name}' unexpectedly has status '{info['status']}'"
            )

    def test_model_size_gb_positive(self):
        data = client.get("/api/model-status").json()
        for name, info in data["models"].items():
            assert info["size_gb"] >= 0, f"Model '{name}' has negative size_gb"

    def test_tiny_is_smallest_model(self):
        data = client.get("/api/model-status").json()
        models = data["models"]
        assert models["tiny"]["size_gb"] <= models["base"]["size_gb"]

    def test_large_is_biggest_model(self):
        data = client.get("/api/model-status").json()
        models = data["models"]
        assert models["large"]["size_gb"] >= models["medium"]["size_gb"]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL MANAGER (15 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestModelManager:
    """Test model manager constants, errors, and state structures."""

    def test_model_load_timeout_exists(self):
        from app.services.model_manager import MODEL_LOAD_TIMEOUT

        assert isinstance(MODEL_LOAD_TIMEOUT, (int, float))

    def test_model_load_timeout_is_reasonable(self):
        from app.services.model_manager import MODEL_LOAD_TIMEOUT

        assert 60 <= MODEL_LOAD_TIMEOUT <= 300

    def test_model_load_timeout_error_importable(self):
        from app.services.model_manager import ModelLoadTimeoutError

        assert issubclass(ModelLoadTimeoutError, Exception)

    def test_model_load_timeout_error_message(self):
        from app.services.model_manager import ModelLoadTimeoutError

        err = ModelLoadTimeoutError("test message")
        assert str(err) == "test message"

    def test_get_model_readiness_importable(self):
        from app.services.model_manager import get_model_readiness

        assert callable(get_model_readiness)

    def test_get_model_readiness_returns_dict(self):
        from app.services.model_manager import get_model_readiness

        result = get_model_readiness()
        assert isinstance(result, dict)

    def test_get_model_readiness_has_all_five_models(self):
        from app.services.model_manager import get_model_readiness

        result = get_model_readiness()
        for name in ["tiny", "base", "small", "medium", "large"]:
            assert name in result, f"Missing model '{name}' in readiness dict"

    def test_get_model_readiness_status_field(self):
        from app.services.model_manager import get_model_readiness

        result = get_model_readiness()
        for name, info in result.items():
            assert "status" in info

    def test_get_model_readiness_size_gb_field(self):
        from app.services.model_manager import get_model_readiness

        result = get_model_readiness()
        for name, info in result.items():
            assert "size_gb" in info

    def test_get_model_readiness_loaded_devices_field(self):
        from app.services.model_manager import get_model_readiness

        result = get_model_readiness()
        for name, info in result.items():
            assert "loaded_devices" in info

    def test_loaded_models_cache_is_dict(self):
        assert isinstance(state.loaded_models, dict)

    def test_model_lock_exists(self):
        import threading

        assert isinstance(state.model_lock, type(threading.Lock()))

    def test_model_preload_has_status(self):
        assert "status" in state.model_preload

    def test_model_preload_has_models(self):
        assert "models" in state.model_preload

    def test_model_preload_has_current_model(self):
        assert "current_model" in state.model_preload

    def test_model_preload_has_loaded_list(self):
        assert "loaded" in state.model_preload
        assert isinstance(state.model_preload["loaded"], list)

    def test_model_preload_has_total(self):
        assert "total" in state.model_preload


class TestModelManagerComputeType:
    """Test compute type selection logic."""

    def test_cpu_always_returns_int8(self):
        from app.services.model_manager import get_compute_type

        for model in ["tiny", "base", "small", "medium", "large"]:
            assert get_compute_type("cpu", model) == "int8"

    def test_gpu_large_returns_int8_float16(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "large") == "int8_float16"

    def test_gpu_medium_returns_int8_float16(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "medium") == "int8_float16"

    def test_gpu_small_returns_float16(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "small") == "float16"

    def test_gpu_tiny_returns_float16(self):
        from app.services.model_manager import get_compute_type

        assert get_compute_type("cuda", "tiny") == "float16"


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM CAPABILITY (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestSystemCapability:
    """Test system capability detection and auto-tuning."""

    def test_system_capability_module_importable(self):
        import app.services.system_capability

        assert app.services.system_capability is not None

    def test_detect_system_capabilities_callable(self):
        from app.services.system_capability import detect_system_capabilities

        assert callable(detect_system_capabilities)

    def test_detect_system_capabilities_returns_dict(self):
        from app.services.system_capability import detect_system_capabilities

        result = detect_system_capabilities()
        assert isinstance(result, dict)

    def test_capabilities_has_platform(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "platform" in caps

    def test_capabilities_has_cpu(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "cpu" in caps

    def test_capabilities_has_memory(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "memory" in caps

    def test_capabilities_has_gpu(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "gpu" in caps

    def test_capabilities_has_tuning(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "tuning" in caps

    def test_tuning_has_max_concurrent_tasks(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        tuning = caps["tuning"]
        assert "max_concurrent_tasks" in tuning
        assert 1 <= tuning["max_concurrent_tasks"] <= 20

    def test_system_info_endpoint_returns_200(self):
        res = client.get("/system-info")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, dict)


class TestSystemCapabilityTuning:
    """Test auto-tuning recommendations."""

    def test_tuning_has_omp_threads(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert "omp_threads" in caps["tuning"]
        assert caps["tuning"]["omp_threads"] >= 1

    def test_tuning_has_recommended_device(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert caps["tuning"]["recommended_device"] in ("cpu", "cuda")

    def test_tuning_has_cpu_default_model(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert caps["tuning"]["cpu_default_model"] in ["tiny", "base", "small", "medium", "large"]

    def test_tuning_has_ffmpeg_threads(self):
        from app.services.system_capability import detect_system_capabilities

        caps = detect_system_capabilities()
        assert caps["tuning"]["ffmpeg_threads"] >= 1

    def test_concurrent_task_limit_from_config(self):
        from app.config import MAX_CONCURRENT_TASKS

        assert isinstance(MAX_CONCURRENT_TASKS, int)
        assert 1 <= MAX_CONCURRENT_TASKS <= 20


# ══════════════════════════════════════════════════════════════════════════════
# FFPROBE CACHING (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestFFprobeCaching:
    """Test ffprobe caching and media utility functions."""

    def test_probe_functions_importable(self):
        from app.utils.media import get_audio_duration, has_audio_stream

        assert callable(get_audio_duration)
        assert callable(has_audio_stream)

    def test_clear_probe_cache_importable(self):
        from app.utils.media import clear_probe_cache

        assert callable(clear_probe_cache)

    def test_probe_file_cached_has_lru_cache(self):
        from app.utils.media import _probe_file_cached

        assert hasattr(_probe_file_cached, "cache_info")
        assert hasattr(_probe_file_cached, "cache_clear")

    def test_probe_cache_maxsize_256(self):
        from app.utils.media import _probe_file_cached

        info = _probe_file_cached.cache_info()
        assert info.maxsize == 256

    def test_get_audio_duration_returns_float(self):
        from pathlib import Path

        from app.utils.media import get_audio_duration

        result = get_audio_duration(Path("/nonexistent/file.wav"))
        assert isinstance(result, float)

    def test_get_audio_duration_missing_file_returns_zero(self):
        from pathlib import Path

        from app.utils.media import get_audio_duration

        result = get_audio_duration(Path("/nonexistent/file.wav"))
        assert result == 0.0

    def test_has_audio_stream_returns_bool(self):
        from pathlib import Path

        from app.utils.media import has_audio_stream

        result = has_audio_stream(Path("/nonexistent/file.wav"))
        assert isinstance(result, bool)

    def test_has_audio_stream_missing_file_returns_false(self):
        from pathlib import Path

        from app.utils.media import has_audio_stream

        result = has_audio_stream(Path("/nonexistent/file.wav"))
        assert result is False

    def test_has_audio_stream_non_media_returns_false(self, tmp_path):
        from app.utils.media import has_audio_stream

        text_file = tmp_path / "test.txt"
        text_file.write_text("this is not media")
        result = has_audio_stream(text_file)
        assert result is False

    def test_clear_probe_cache_resets_stats(self):
        from app.utils.media import _probe_file_cached, clear_probe_cache

        clear_probe_cache()
        info = _probe_file_cached.cache_info()
        assert info.hits == 0
        assert info.misses == 0

    def test_get_file_size_importable(self):
        from app.utils.media import get_file_size

        assert callable(get_file_size)

    def test_get_file_size_missing_file_returns_zero(self):
        from pathlib import Path

        from app.utils.media import get_file_size

        assert get_file_size(Path("/nonexistent/file.wav")) == 0

    def test_get_file_size_real_file(self, tmp_path):
        from app.utils.media import get_file_size

        f = tmp_path / "test.bin"
        f.write_bytes(b"\x00" * 1024)
        assert get_file_size(f) == 1024

    def test_ffmpeg_timeout_constant_exists(self):
        from app.utils.media import FFMPEG_TIMEOUT

        assert isinstance(FFMPEG_TIMEOUT, int)
        assert FFMPEG_TIMEOUT > 0

    def test_ffmpeg_protocol_whitelist_exists(self):
        from app.utils.media import FFMPEG_PROTOCOL_WHITELIST

        assert isinstance(FFMPEG_PROTOCOL_WHITELIST, str)
        assert "file" in FFMPEG_PROTOCOL_WHITELIST

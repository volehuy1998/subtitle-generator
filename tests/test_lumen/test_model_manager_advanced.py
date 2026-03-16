"""Phase Lumen L63 — Model manager advanced tests.

Tests get_model cache hit/miss, timeout handling, lock acquisition
failure, and get_model_readiness.
— Scout (QA Lead)
"""

import threading
from unittest.mock import MagicMock, patch

import pytest

from app.services.model_manager import (
    ModelLoadTimeoutError,
    get_model,
    get_model_readiness,
)

# ══════════════════════════════════════════════════════════════════════════════
# GET MODEL — CACHE HIT
# ══════════════════════════════════════════════════════════════════════════════


class TestGetModelCacheHit:
    """Test that cached models are returned without lock acquisition."""

    def test_returns_cached_model_without_lock(self):
        from app import state

        mock_model = MagicMock()
        key = ("tiny", "cpu")

        original_models = state.loaded_models.copy()
        original_lock = state.model_lock
        mock_lock = MagicMock()
        mock_lock.acquire = MagicMock(return_value=True)
        mock_lock.release = MagicMock()
        state.model_lock = mock_lock

        try:
            state.loaded_models[key] = mock_model

            result = get_model("tiny", "cpu")

            assert result is mock_model
            mock_lock.acquire.assert_not_called()
        finally:
            state.loaded_models = original_models
            state.model_lock = original_lock


# ══════════════════════════════════════════════════════════════════════════════
# GET MODEL — CACHE MISS
# ══════════════════════════════════════════════════════════════════════════════


class TestGetModelCacheMiss:
    """Test model loading on cache miss."""

    @patch("app.services.model_manager._load_model_with_timeout")
    @patch("app.services.model_manager.get_gpu_memory_usage")
    def test_acquires_lock_loads_model_and_stores(self, mock_gpu, mock_load):
        from app import state

        mock_model = MagicMock()
        mock_load.return_value = mock_model
        key = ("base", "cpu")

        original_models = state.loaded_models.copy()
        original_lock = state.model_lock
        state.model_lock = threading.Lock()

        try:
            # Ensure not cached
            state.loaded_models.pop(key, None)

            result = get_model("base", "cpu")

            assert result is mock_model
            assert state.loaded_models[key] is mock_model
            mock_load.assert_called_once()
        finally:
            state.loaded_models = original_models
            state.model_lock = original_lock


# ══════════════════════════════════════════════════════════════════════════════
# GET MODEL — TIMEOUTS & ERRORS
# ══════════════════════════════════════════════════════════════════════════════


class TestGetModelTimeouts:
    """Test timeout and error paths in get_model."""

    @patch("app.services.model_manager._load_model_with_timeout")
    def test_load_timeout_raises_model_load_timeout_error(self, mock_load):
        from app import state

        mock_load.side_effect = ModelLoadTimeoutError("timed out")
        key = ("small", "cpu")

        original_models = state.loaded_models.copy()
        original_lock = state.model_lock
        state.model_lock = threading.Lock()

        try:
            state.loaded_models.pop(key, None)

            with pytest.raises(ModelLoadTimeoutError):
                get_model("small", "cpu")
        finally:
            state.loaded_models = original_models
            state.model_lock = original_lock

    @patch("app.services.model_manager._load_model_with_timeout")
    def test_whisper_model_raises_propagated(self, mock_load):
        from app import state

        mock_load.side_effect = RuntimeError("CUDA out of memory")
        key = ("medium", "cpu")

        original_models = state.loaded_models.copy()
        original_lock = state.model_lock
        state.model_lock = threading.Lock()

        try:
            state.loaded_models.pop(key, None)

            with pytest.raises(RuntimeError, match="CUDA out of memory"):
                get_model("medium", "cpu")
        finally:
            state.loaded_models = original_models
            state.model_lock = original_lock

    def test_lock_acquire_returns_false_raises_timeout(self):
        from app import state

        key = ("large", "cpu")

        original_models = state.loaded_models.copy()
        original_lock = state.model_lock
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = False
        state.model_lock = mock_lock

        try:
            state.loaded_models.pop(key, None)

            with pytest.raises(ModelLoadTimeoutError):
                get_model("large", "cpu")
        finally:
            state.loaded_models = original_models
            state.model_lock = original_lock


# ══════════════════════════════════════════════════════════════════════════════
# GET MODEL READINESS
# ══════════════════════════════════════════════════════════════════════════════


class TestGetModelReadiness:
    """Test get_model_readiness status reporting."""

    def test_loaded_model_shows_ready(self):
        from app import state

        original_models = state.loaded_models.copy()
        original_preload = state.model_preload.copy()

        try:
            state.loaded_models[("tiny", "cpu")] = MagicMock()
            state.model_preload = {"status": "idle", "current_model": None}

            result = get_model_readiness()

            assert result["tiny"]["status"] == "ready"
            assert "cpu" in result["tiny"]["loaded_devices"]
        finally:
            state.loaded_models = original_models
            state.model_preload = original_preload

    def test_all_five_model_sizes_in_result(self):
        from app import state

        original_preload = state.model_preload.copy()
        try:
            state.model_preload = {"status": "idle", "current_model": None}
            result = get_model_readiness()
            assert set(result.keys()) == {"tiny", "base", "small", "medium", "large"}
        finally:
            state.model_preload = original_preload

    def test_unloaded_model_shows_not_loaded(self):
        from app import state

        original_models = state.loaded_models.copy()
        original_preload = state.model_preload.copy()

        try:
            # Remove all loaded models
            state.loaded_models = {}
            state.model_preload = {"status": "idle", "current_model": None}

            result = get_model_readiness()

            for model in ("tiny", "base", "small", "medium", "large"):
                assert result[model]["status"] == "not_loaded"
                assert result[model]["loaded_devices"] == []
        finally:
            state.loaded_models = original_models
            state.model_preload = original_preload

    def test_loading_model_shows_loading_status(self):
        from app import state

        original_models = state.loaded_models.copy()
        original_preload = state.model_preload.copy()

        try:
            state.loaded_models = {}
            state.model_preload = {"status": "loading", "current_model": "medium"}

            result = get_model_readiness()

            assert result["medium"]["status"] == "loading"
            assert result["tiny"]["status"] == "not_loaded"
        finally:
            state.loaded_models = original_models
            state.model_preload = original_preload

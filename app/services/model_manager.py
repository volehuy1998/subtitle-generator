"""Whisper model loading and management."""

import logging
import threading
import time

from faster_whisper import WhisperModel

from app import state
from app.config import CPU_COUNT
from app.services.gpu import get_gpu_memory_usage

logger = logging.getLogger("subtitle-generator")

# Sprint L9: Model loading timeout (seconds) — Forge (Sr. Backend Engineer)
MODEL_LOAD_TIMEOUT = 120


class ModelLoadTimeoutError(Exception):
    """Raised when model loading exceeds the timeout threshold."""

    pass


def get_compute_type(device: str, model_size: str) -> str:
    """Select optimal compute type based on device and model size."""
    if device == "cpu":
        return "int8"  # fastest on CPU
    # GPU: int8_float16 for larger models to save VRAM
    if model_size in ("large", "medium"):
        return "int8_float16"
    return "float16"


def _load_model_with_timeout(model_size: str, device: str, compute_type: str, timeout: float) -> WhisperModel:
    """Load a WhisperModel in a thread with a timeout to prevent deadlocks.

    Sprint L9: Queue-based model loading with timeout — Forge (Sr. Backend Engineer)
    """
    result: dict = {}
    error: list = []

    def _do_load():
        try:
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=CPU_COUNT if device == "cpu" else 4,
            )
            result["model"] = model
        except Exception as e:
            error.append(e)

    loader = threading.Thread(target=_do_load, daemon=True)
    loader.start()
    loader.join(timeout=timeout)

    if loader.is_alive():
        logger.error(f"MODEL Loading '{model_size}' on {device.upper()} timed out after {timeout}s")
        raise ModelLoadTimeoutError(f"Model loading timed out after {timeout} seconds. The server may be overloaded.")

    if error:
        raise error[0]

    return result["model"]


def get_model(model_size: str, device: str) -> WhisperModel:
    """Thread-safe cached model loading with timeout protection.

    Uses a lock to prevent concurrent model switches. If loading takes longer
    than MODEL_LOAD_TIMEOUT seconds, raises ModelLoadTimeoutError to prevent
    tasks from getting stuck. — Forge (Sr. Backend Engineer)
    """
    key = (model_size, device)
    if key not in state.loaded_models:
        # Use timeout on lock acquisition to prevent deadlock — Forge (Sr. Backend Engineer)
        acquired = state.model_lock.acquire(timeout=MODEL_LOAD_TIMEOUT)
        if not acquired:
            logger.error(f"MODEL Lock acquisition timed out for '{model_size}' on {device.upper()}")
            raise ModelLoadTimeoutError("Model loading timed out. The server may be overloaded.")
        try:
            if key not in state.loaded_models:
                compute_type = get_compute_type(device, model_size)
                logger.info(f"MODEL Loading '{model_size}' on {device.upper()} (compute_type={compute_type})...")
                if device == "cuda":
                    gpu_mem = get_gpu_memory_usage()
                    logger.info(f"MODEL GPU memory before load: {gpu_mem}")
                t0 = time.time()
                state.loaded_models[key] = _load_model_with_timeout(
                    model_size, device, compute_type, MODEL_LOAD_TIMEOUT
                )
                load_time = time.time() - t0
                logger.info(
                    f"MODEL Loaded '{model_size}' on {device.upper()} in {load_time:.1f}s (compute_type={compute_type})"
                )
                if device == "cuda":
                    gpu_mem = get_gpu_memory_usage()
                    logger.info(f"MODEL GPU memory after load: {gpu_mem}")
        finally:
            state.model_lock.release()
    return state.loaded_models[key]


def get_model_readiness() -> dict:
    """Return readiness status for all model sizes.

    Returns a dict with model sizes as keys and status info as values:
    - "ready": model is loaded and available for immediate use
    - "loading": model is currently being loaded (from preload or request)
    - "not_loaded": model needs to be downloaded/loaded on first use
    """
    from app.config import MODEL_VRAM_GB, VALID_MODELS

    preload = state.model_preload or {}
    preload_status = preload.get("status", "idle")
    current_loading = preload.get("current_model")
    result = {}
    for model in VALID_MODELS:
        # Check if loaded in memory (any device)
        is_loaded = any(k[0] == model for k in state.loaded_models)

        if is_loaded:
            status = "ready"
        elif preload_status == "loading" and current_loading == model:
            status = "loading"
        else:
            status = "not_loaded"

        result[model] = {
            "status": status,
            "size_gb": MODEL_VRAM_GB.get(model, 0),
            "loaded_devices": [k[1] for k in state.loaded_models if k[0] == model],
        }

    return result

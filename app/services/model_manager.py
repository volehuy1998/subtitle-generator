"""Whisper model loading and management."""

import logging
import time

from faster_whisper import WhisperModel

from app import state
from app.config import CPU_COUNT
from app.services.gpu import get_gpu_memory_usage

logger = logging.getLogger("subtitle-generator")


def get_compute_type(device: str, model_size: str) -> str:
    """Select optimal compute type based on device and model size."""
    if device == "cpu":
        return "int8"  # fastest on CPU
    # GPU: int8_float16 for larger models to save VRAM
    if model_size in ("large", "medium"):
        return "int8_float16"
    return "float16"


def get_model(model_size: str, device: str) -> WhisperModel:
    """Thread-safe cached model loading."""
    key = (model_size, device)
    if key not in state.loaded_models:
        with state.model_lock:
            if key not in state.loaded_models:
                compute_type = get_compute_type(device, model_size)
                logger.info(f"MODEL Loading '{model_size}' on {device.upper()} (compute_type={compute_type})...")
                if device == "cuda":
                    gpu_mem = get_gpu_memory_usage()
                    logger.info(f"MODEL GPU memory before load: {gpu_mem}")
                t0 = time.time()
                state.loaded_models[key] = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type,
                    cpu_threads=CPU_COUNT if device == "cpu" else 4,
                )
                load_time = time.time() - t0
                logger.info(
                    f"MODEL Loaded '{model_size}' on {device.upper()} in {load_time:.1f}s (compute_type={compute_type})"
                )
                if device == "cuda":
                    gpu_mem = get_gpu_memory_usage()
                    logger.info(f"MODEL GPU memory after load: {gpu_mem}")
    return state.loaded_models[key]

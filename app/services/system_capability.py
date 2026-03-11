"""System capability detection and auto-tuning for optimal performance.

Queries hardware, OS, and resource information at startup to ensure
optimal processing regardless of platform (Linux, Windows, macOS).
"""

import logging
import os
import platform
import shutil
import subprocess
import sys

import psutil
import torch

from app.config import CPU_COUNT, MODEL_VRAM_GB

logger = logging.getLogger("subtitle-generator")


def detect_system_capabilities() -> dict:
    """Full system capability scan at startup. Returns a dict describing the system."""
    caps = {
        "platform": _detect_platform(),
        "cpu": _detect_cpu(),
        "memory": _detect_memory(),
        "gpu": _detect_gpu(),
        "storage": _detect_storage(),
        "software": _detect_software(),
    }
    caps["tuning"] = _compute_tuning(caps)
    return caps


def _detect_platform() -> dict:
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "python": sys.version.split()[0],
        "python_impl": platform.python_implementation(),
        "is_linux": platform.system() == "Linux",
        "is_windows": platform.system() == "Windows",
        "is_docker": os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"),
    }


def _detect_cpu() -> dict:
    freq = psutil.cpu_freq()
    return {
        "physical_cores": psutil.cpu_count(logical=False) or CPU_COUNT,
        "logical_cores": psutil.cpu_count(logical=True) or CPU_COUNT,
        "max_freq_mhz": round(freq.max, 0) if freq and freq.max else 0,
        "current_freq_mhz": round(freq.current, 0) if freq else 0,
        "brand": _get_cpu_brand(),
        "load_percent": psutil.cpu_percent(interval=0.1),
    }


def _get_cpu_brand() -> str:
    try:
        if platform.system() == "Windows":
            return platform.processor() or "Unknown"
        elif platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        elif platform.system() == "Darwin":
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"


def _detect_memory() -> dict:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(vm.total / 1024**3, 1),
        "available_gb": round(vm.available / 1024**3, 1),
        "used_gb": round(vm.used / 1024**3, 1),
        "percent": vm.percent,
        "swap_total_gb": round(swap.total / 1024**3, 1),
        "swap_used_gb": round(swap.used / 1024**3, 1),
    }


def _detect_gpu() -> dict:
    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": 0,
        "devices": [],
    }
    if not torch.cuda.is_available():
        return info

    info["device_count"] = torch.cuda.device_count()
    info["cuda_version"] = torch.version.cuda or "unknown"
    info["cudnn_version"] = str(torch.backends.cudnn.version()) if torch.backends.cudnn.is_available() else "N/A"

    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        allocated = torch.cuda.memory_allocated(i) / 1024**3
        reserved = torch.cuda.memory_reserved(i) / 1024**3
        total_gb = props.total_memory / 1024**3
        info["devices"].append({
            "index": i,
            "name": props.name,
            "total_gb": round(total_gb, 1),
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "free_gb": round(total_gb - allocated, 1),
            "compute_capability": f"{props.major}.{props.minor}",
            "multi_processor_count": props.multi_processor_count,
        })
    return info


def _detect_storage() -> dict:
    try:
        from app.config import BASE_DIR
        usage = shutil.disk_usage(str(BASE_DIR))
        return {
            "total_gb": round(usage.total / 1024**3, 1),
            "free_gb": round(usage.free / 1024**3, 1),
            "used_percent": round(usage.used / usage.total * 100, 1),
        }
    except Exception:
        return {"total_gb": 0, "free_gb": 0, "used_percent": 0}


def _detect_software() -> dict:
    import faster_whisper

    ffmpeg_version = "not found"
    ffprobe_version = "not found"
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            first_line = result.stdout.split("\n")[0]
            ffmpeg_version = first_line.split(" ")[2] if len(first_line.split(" ")) > 2 else first_line
    except Exception:
        pass
    try:
        result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            ffprobe_version = "found"
    except Exception:
        pass

    # Check for optional pyannote.audio
    pyannote_version = "not installed"
    try:
        import pyannote.audio
        pyannote_version = getattr(pyannote.audio, "__version__", "installed")
    except ImportError:
        pass

    hf_token_set = bool(os.environ.get("HF_TOKEN", ""))

    return {
        "pytorch": torch.__version__,
        "faster_whisper": faster_whisper.__version__,
        "ffmpeg": ffmpeg_version,
        "ffprobe": ffprobe_version,
        "pyannote": pyannote_version,
        "hf_token_configured": hf_token_set,
    }


def _compute_tuning(caps: dict) -> dict:
    """Auto-tune settings based on detected hardware."""
    cpu = caps["cpu"]
    mem = caps["memory"]
    gpu = caps["gpu"]

    physical = cpu["physical_cores"]
    logical = cpu["logical_cores"]
    ram_gb = mem["total_gb"]

    # OMP threads: use physical cores for transcription, leave some for system
    omp_threads = max(1, physical - 1) if physical > 2 else physical

    # Concurrent tasks based on RAM and CPU
    if ram_gb >= 64:
        max_tasks = min(4, physical // 4)
    elif ram_gb >= 32:
        max_tasks = min(3, physical // 3)
    elif ram_gb >= 16:
        max_tasks = 2
    else:
        max_tasks = 1

    # CPU model selection based on RAM
    cpu_default_model = "small"
    if ram_gb >= 32:
        cpu_default_model = "medium"
    elif ram_gb >= 16:
        cpu_default_model = "small"
    elif ram_gb >= 8:
        cpu_default_model = "base"
    else:
        cpu_default_model = "tiny"

    # GPU auto-model
    gpu_default_model = "small"
    if gpu["cuda_available"] and gpu["devices"]:
        free_gb = gpu["devices"][0]["free_gb"]
        for model in ["large", "medium", "small", "base", "tiny"]:
            if MODEL_VRAM_GB[model] + 1.0 <= free_gb:
                gpu_default_model = model
                break

    # ffmpeg threads
    ffmpeg_threads = max(2, physical // 2)

    return {
        "omp_threads": omp_threads,
        "max_concurrent_tasks": max(1, max_tasks),
        "cpu_default_model": cpu_default_model,
        "gpu_default_model": gpu_default_model,
        "ffmpeg_threads": ffmpeg_threads,
        "recommended_device": "cuda" if gpu["cuda_available"] else "cpu",
    }


def log_capabilities(caps: dict):
    """Log system capabilities in a structured, readable format."""
    plat = caps["platform"]
    cpu = caps["cpu"]
    mem = caps["memory"]
    gpu = caps["gpu"]
    stor = caps["storage"]
    sw = caps["software"]
    tune = caps["tuning"]

    logger.info("=" * 70)
    logger.info("SUBTITLE GENERATOR - SYSTEM CAPABILITY SCAN")
    logger.info("=" * 70)
    logger.info(f"OS:              {plat['os']} {plat['os_release']} ({plat['arch']})")
    logger.info(f"Python:          {plat['python']} ({plat['python_impl']})")
    logger.info(f"Container:       {'Yes' if plat['is_docker'] else 'No'}")
    logger.info("-" * 70)
    logger.info(f"CPU:             {cpu['brand']}")
    logger.info(f"Cores:           {cpu['physical_cores']} physical, {cpu['logical_cores']} logical")
    logger.info(f"Frequency:       {cpu['current_freq_mhz']:.0f} / {cpu['max_freq_mhz']:.0f} MHz")
    logger.info(f"Load:            {cpu['load_percent']:.1f}%")
    logger.info("-" * 70)
    logger.info(f"RAM:             {mem['total_gb']} GB total, {mem['available_gb']} GB available ({mem['percent']}% used)")
    logger.info(f"Swap:            {mem['swap_total_gb']} GB total, {mem['swap_used_gb']} GB used")
    logger.info("-" * 70)
    if gpu["cuda_available"]:
        logger.info(f"CUDA:            {gpu.get('cuda_version', 'N/A')} (cuDNN {gpu.get('cudnn_version', 'N/A')})")
        for dev in gpu["devices"]:
            logger.info(
                f"GPU {dev['index']}:           {dev['name']} | {dev['total_gb']}GB total, "
                f"{dev['free_gb']}GB free | CC {dev['compute_capability']} | {dev['multi_processor_count']} SMs"
            )
    else:
        logger.info("GPU:             Not available (CPU-only mode)")
    logger.info("-" * 70)
    logger.info(f"Storage:         {stor['free_gb']} GB free of {stor['total_gb']} GB ({stor['used_percent']}% used)")
    logger.info(f"ffmpeg:          {sw['ffmpeg']}")
    logger.info(f"PyTorch:         {sw['pytorch']}")
    logger.info(f"faster-whisper:  {sw['faster_whisper']}")
    logger.info("-" * 70)
    logger.info(f"TUNING:")
    logger.info(f"  OMP threads:   {tune['omp_threads']}")
    logger.info(f"  Max tasks:     {tune['max_concurrent_tasks']}")
    logger.info(f"  Device:        {tune['recommended_device']}")
    logger.info(f"  CPU model:     {tune['cpu_default_model']}")
    logger.info(f"  GPU model:     {tune['gpu_default_model']}")
    logger.info(f"  ffmpeg threads: {tune['ffmpeg_threads']}")
    logger.info(f"pyannote:        {sw['pyannote']}")
    logger.info(f"HF token:        {'configured' if sw['hf_token_configured'] else 'not set'}")
    logger.info("=" * 70)

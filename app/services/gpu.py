"""GPU detection, VRAM management, auto model selection."""

import torch

from app.config import MODEL_VRAM_GB


def get_system_info() -> dict:
    from app.services.gpu import auto_select_model
    info = {
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": None,
        "gpu_vram": None,
        "gpu_vram_free": None,
        "model_recommendations": {},
        "auto_model": auto_select_model(),
    }
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        total_gb = round(props.total_memory / 1024**3, 1)
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        free_gb = round(total_gb - allocated, 1)
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_vram"] = total_gb
        info["gpu_vram_free"] = free_gb
        for model, req in MODEL_VRAM_GB.items():
            if req <= free_gb:
                info["model_recommendations"][model] = "ok"
            elif req <= free_gb * 1.3:
                info["model_recommendations"][model] = "tight"
            else:
                info["model_recommendations"][model] = "too_large"
    return info


def get_gpu_memory_usage() -> dict:
    if not torch.cuda.is_available():
        return {}
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    reserved = torch.cuda.memory_reserved(0) / 1024**3
    total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    return {
        "allocated_gb": round(allocated, 2),
        "reserved_gb": round(reserved, 2),
        "total_gb": round(total, 1),
        "free_gb": round(total - allocated, 2),
    }


def check_vram_for_model(model_size: str) -> dict:
    """Check if the model will fit in GPU VRAM."""
    if not torch.cuda.is_available():
        return {"fits": False, "reason": "no_gpu"}
    total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    free = total - allocated
    required = MODEL_VRAM_GB.get(model_size, 10.0)
    if required <= free:
        return {"fits": True, "free_gb": round(free, 1), "required_gb": required}
    elif required <= free * 1.3:
        return {"fits": True, "tight": True, "free_gb": round(free, 1), "required_gb": required}
    else:
        return {"fits": False, "reason": "insufficient_vram", "free_gb": round(free, 1), "required_gb": required}


def auto_select_model() -> str:
    """Auto-select the largest model that fits comfortably in VRAM."""
    if not torch.cuda.is_available():
        return "small"
    total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    allocated = torch.cuda.memory_allocated(0) / 1024**3
    free = total - allocated
    for model in ["large", "medium", "small", "base", "tiny"]:
        if MODEL_VRAM_GB[model] + 1.0 <= free:
            return model
    return "tiny"

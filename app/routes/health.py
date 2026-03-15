"""Health check and readiness endpoints for production monitoring."""

import asyncio
import json
import logging
import os
import shutil
import time

from fastapi import APIRouter, Request, Response
from starlette.responses import StreamingResponse

from app import state
from app.config import MAX_CONCURRENT_TASKS, OUTPUT_DIR, UPLOAD_DIR
from app.schemas import HealthResponse, SystemStatusResponse

logger = logging.getLogger("subtitle-generator")

router = APIRouter(tags=["System"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Liveness probe - is the service running?

    Returns 200 if the process is alive. Suitable for Kubernetes liveness probes,
    AWS ALB health checks, and HAProxy checks.
    """
    return {"status": "healthy", "uptime_sec": round(time.time() - _start_time, 1)}


@router.get("/health/live")
async def health_live(response: Response):
    """Minimal liveness probe for load balancers.

    Returns plain 200 with no body processing. Optimized for high-frequency
    polling by load balancers (ALB, NLB, HAProxy, Traefik).
    """
    response.status_code = 200
    return {"status": "ok"}


@router.get("/ready")
async def ready(response: Response):
    """Readiness probe - is the service ready to accept work?

    Returns 200 if ready, 503 if not. Load balancers should route traffic
    only to instances returning 200 on this endpoint.
    """
    checks = {}

    # Check disk space (need at least 1GB free)
    try:
        usage = shutil.disk_usage(str(OUTPUT_DIR))
        free_gb = usage.free / 1024**3
        checks["disk"] = {"ok": free_gb > 1.0, "free_gb": round(free_gb, 1)}
    except Exception:
        checks["disk"] = {"ok": False, "error": "cannot read disk"}

    # Check directories writable
    checks["dirs"] = {
        "uploads": UPLOAD_DIR.exists(),
        "outputs": OUTPUT_DIR.exists(),
    }

    # Check ffmpeg available
    checks["ffmpeg"] = shutil.which("ffmpeg") is not None

    # Check shutdown state
    checks["shutting_down"] = state.shutting_down

    # Database connectivity
    try:
        from app.services.query_layer import check_db_health

        db_result = await check_db_health()
        checks["db"] = {"ok": db_result.get("ok", False), "latency_ms": db_result.get("latency_ms")}
    except Exception:
        checks["db"] = {"ok": False, "error": "connection failed"}

    # Active task count
    active = sum(1 for t in state.tasks.values() if t.get("status") not in ("done", "error", "cancelled"))
    checks["tasks"] = {"active": active}

    all_ok = (
        checks["disk"]["ok"]
        and checks["ffmpeg"]
        and checks.get("db", {}).get("ok", False)
        and all(checks["dirs"].values())
        and not state.shutting_down
    )

    if not all_ok:
        response.status_code = 503

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
        "uptime_sec": round(time.time() - _start_time, 1),
    }


@router.get("/api/model-status")
async def model_status():
    """Get model preload and per-model readiness for frontend display.

    Returns preload progress and per-model status (ready/loading/not_loaded)
    so the UI can show which models are available for immediate use.
    """
    from app.services.model_manager import get_model_readiness

    return {
        "preload": state.model_preload,
        "models": get_model_readiness(),
    }


@router.get("/api/capabilities")
async def capabilities():
    """Report which features are available based on system dependencies."""
    from app.config import AUDIO_ONLY_EXTENSIONS, FFMPEG_AVAILABLE, FFPROBE_AVAILABLE, VIDEO_EXTENSIONS

    return {
        "ffmpeg": FFMPEG_AVAILABLE,
        "ffprobe": FFPROBE_AVAILABLE,
        "features": {
            "transcribe_audio": True,
            "transcribe_video": FFMPEG_AVAILABLE,
            "combine": FFMPEG_AVAILABLE,
            "embed_soft": FFMPEG_AVAILABLE,
            "embed_hard": FFMPEG_AVAILABLE,
            "media_probe": FFPROBE_AVAILABLE,
        },
        "accepted_extensions": list(VIDEO_EXTENSIONS | AUDIO_ONLY_EXTENSIONS)
        if FFMPEG_AVAILABLE
        else list(AUDIO_ONLY_EXTENSIONS),
    }


@router.get("/scale/info")
async def scale_info():
    """Get scaling and infrastructure info for horizontal scaling.

    Returns worker status, storage backend, task backend, and capacity info.
    """
    from app.services.analytics_db import get_db_info
    from app.services.storage import get_storage
    from app.services.task_backend import get_backend_info
    from app.services.worker_health import get_healthy_worker_count, get_worker_status

    return {
        "workers": get_worker_status(),
        "healthy_workers": get_healthy_worker_count(),
        "task_backend": get_backend_info(),
        "storage": get_storage().get_storage_info(),
        "analytics_db": get_db_info(),
        "pid": os.getpid(),
        "uptime_sec": round(time.time() - _start_time, 1),
    }


# ── System Status (lightweight aggregate for frontend health indicator) ──

_status_cache: dict = {"data": None, "expires": 0.0}
_status_lock = None  # asyncio.Lock, created lazily (can't create at import time)


def _get_status_lock():
    global _status_lock
    import asyncio

    if _status_lock is None:
        _status_lock = asyncio.Lock()
    return _status_lock


def _blocking_system_stats() -> dict:
    """Collect all blocking I/O stats in a thread pool worker."""
    result = {}

    # Disk space
    try:
        usage = shutil.disk_usage(str(OUTPUT_DIR))
        if usage.total == 0:
            usage = shutil.disk_usage("/")
        result["disk_free_gb"] = round(usage.free / 1024**3, 1)
        result["disk_ok"] = result["disk_free_gb"] > 1.0
        try:
            result["disk_percent"] = round(usage.used / usage.total * 100)
        except Exception:
            result["disk_percent"] = None
    except Exception:
        result["disk_free_gb"] = None
        result["disk_ok"] = False
        result["disk_percent"] = None

    # ffmpeg
    result["ffmpeg_ok"] = shutil.which("ffmpeg") is not None

    # CPU/Memory
    try:
        import psutil

        result["cpu_percent"] = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()
        result["memory_percent"] = mem.percent
    except Exception:
        result["cpu_percent"] = None
        result["memory_percent"] = None

    # Alerts (uses threading.Lock internally — safe in thread worker)
    try:
        from app.services.monitoring import check_alerts

        alerts = check_alerts()
        result["alerts"] = alerts
        result["alert_count"] = len(alerts)
        result["has_critical"] = any(a.get("severity") == "critical" for a in alerts)
        result["has_warning"] = any(a.get("severity") == "warning" for a in alerts)
    except Exception:
        result["alerts"] = []
        result["alert_count"] = 0
        result["has_critical"] = False
        result["has_warning"] = False

    return result


@router.get("/api/status", response_model=SystemStatusResponse)
async def system_status():
    """Lightweight system status for the frontend health indicator.

    Aggregates service health, DB connectivity, alerts, active tasks,
    and disk space into a single response. Cached for 3 seconds.
    """
    now = time.time()
    if _status_cache["data"] and now < _status_cache["expires"]:
        return _status_cache["data"]

    # Serialize cache fills — only one coroutine recomputes at a time;
    # all others wait and then return the freshly cached value.
    async with _get_status_lock():
        # Re-check after acquiring lock (another coroutine may have filled it)
        now = time.time()
        if _status_cache["data"] and now < _status_cache["expires"]:
            return _status_cache["data"]

        uptime = round(now - _start_time, 1)

        # Active tasks (in-memory dict read — no I/O)
        active_tasks = sum(1 for t in state.tasks.values() if t.get("status") not in ("done", "error", "cancelled"))

        # Run all blocking syscalls off the event loop
        stats = await asyncio.to_thread(_blocking_system_stats)

        # DB connectivity (async — runs normally on event loop)
        db_ok = True
        db_latency_ms = None
        try:
            from app.services.query_layer import check_db_health

            db_result = await check_db_health()
            db_ok = db_result.get("status") == "healthy"
            db_latency_ms = db_result.get("latency_ms")
        except Exception:
            db_ok = False

        # GPU (CUDA calls are fast and non-blocking)
        gpu_available = False
        gpu_name = None
        gpu_vram_total = None
        gpu_vram_used = None
        gpu_vram_free = None
        try:
            import torch

            if torch.cuda.is_available():
                gpu_available = True
                props = torch.cuda.get_device_properties(0)
                gpu_name = torch.cuda.get_device_name(0)
                gpu_vram_total = round(props.total_memory / 1024**3, 1)
                gpu_vram_used = round(torch.cuda.memory_allocated(0) / 1024**3, 2)
                gpu_vram_free = round(gpu_vram_total - gpu_vram_used, 2)
        except Exception:
            pass

        # Overall status
        if stats["has_critical"] or not db_ok or not stats["disk_ok"]:
            overall = "critical"
        elif stats["has_warning"] or not stats["ffmpeg_ok"]:
            overall = "warning"
        else:
            overall = "healthy"

        result = {
            "status": overall,
            "uptime_sec": uptime,
            "active_tasks": active_tasks,
            "max_tasks": MAX_CONCURRENT_TASKS,
            "cpu_percent": stats["cpu_percent"],
            "memory_percent": stats["memory_percent"],
            "disk_free_gb": stats["disk_free_gb"],
            "disk_percent": stats["disk_percent"],
            "disk_ok": stats["disk_ok"],
            "db_ok": db_ok,
            "db_latency_ms": db_latency_ms,
            "ffmpeg_ok": stats["ffmpeg_ok"],
            "gpu_available": gpu_available,
            "gpu_name": gpu_name,
            "gpu_vram_total": gpu_vram_total,
            "gpu_vram_used": gpu_vram_used,
            "gpu_vram_free": gpu_vram_free,
            "shutting_down": state.shutting_down,
            "system_critical": state.system_critical,
            "system_critical_reasons": state.system_critical_reasons,
            "alerts": [
                {"alert": a.get("alert", ""), "severity": a.get("severity", ""), "message": a.get("message", "")}
                for a in stats["alerts"]
            ],
            "alert_count": stats["alert_count"],
            "model_preload": state.model_preload,
        }

        _status_cache["data"] = result
        _status_cache["expires"] = now + 3
        return result


@router.get("/health/stream")
async def health_stream(request: Request):
    """Server-Sent Events stream for real-time system health updates.

    Pushes health status every 3 seconds. The SSE connection itself
    serves as a connectivity signal — if it drops, the client knows immediately.
    """

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await system_status()
                yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                logger.error(f"HEALTH stream error: {e}", exc_info=True)
                yield f"data: {json.dumps({'status': 'error', 'message': 'Health check unavailable'})}\n\n"
            await asyncio.sleep(3)
            if await request.is_disconnected():
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

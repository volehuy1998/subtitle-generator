"""Background health monitor — continuously evaluates system health.

Runs as an asyncio task during the app lifespan. Checks all critical
subsystems every few seconds and sets/clears state.system_critical.

Critical conditions (any one triggers critical state):
- Database unreachable
- Disk space below 500 MB
- System shutting down
- FFmpeg not available
- Memory critically low (<500 MB)
- Output directory not writable
- Redis unreachable (when configured)
- No transcription model available
"""

import asyncio
import logging
import os
import shutil

import psutil

from app import state
from app.config import OUTPUT_DIR, REDIS_URL

logger = logging.getLogger("subtitle-generator")

# How often to check (seconds)
CHECK_INTERVAL = 5

# Minimum free disk space (bytes)
MIN_DISK_FREE_BYTES = 500 * 1024 * 1024  # 500 MB

# Minimum available memory (bytes)
MIN_MEMORY_AVAILABLE_BYTES = 500 * 1024 * 1024  # 500 MB


async def _check_db() -> str | None:
    """Returns reason string if DB is unreachable, None if healthy."""
    try:
        from app.services.query_layer import check_db_health

        result = await check_db_health()
        if not result.get("ok"):
            return "Database connection lost"
    except Exception as e:
        return f"Database check failed: {e}"
    return None


def _check_disk() -> str | None:
    """Returns reason string if disk space is critically low."""
    try:
        usage = shutil.disk_usage(str(OUTPUT_DIR))
        if usage.free < MIN_DISK_FREE_BYTES:
            free_mb = round(usage.free / 1024 / 1024)
            return f"Disk space critically low ({free_mb} MB free)"
    except Exception as e:
        return f"Disk check failed: {e}"
    return None


def _check_ffmpeg() -> str | None:
    """Returns reason string if FFmpeg is not available."""
    if shutil.which("ffmpeg") is None:
        return "FFmpeg not available"
    return None


def _check_memory() -> str | None:
    """Returns reason string if available memory is critically low."""
    try:
        mem = psutil.virtual_memory()
        if mem.available < MIN_MEMORY_AVAILABLE_BYTES:
            avail_mb = round(mem.available / 1024 / 1024)
            return f"Memory critically low ({avail_mb} MB available)"
    except Exception as e:
        return f"Memory check failed: {e}"
    return None


def _check_output_dir() -> str | None:
    """Returns reason string if the output directory is not writable."""
    try:
        if not os.access(str(OUTPUT_DIR), os.W_OK):
            return "Output directory not writable"
    except Exception as e:
        return f"Output dir check failed: {e}"
    return None


async def _check_redis() -> str | None:
    """Returns reason string if Redis is configured but unreachable."""
    if not REDIS_URL:
        return None  # Redis not configured — skip check
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(REDIS_URL, socket_connect_timeout=2)
        try:
            await asyncio.wait_for(client.ping(), timeout=2)
        finally:
            await client.aclose()
    except Exception as e:
        return f"Redis unreachable: {e}"
    return None


def _check_model() -> str | None:
    """Returns reason string if no transcription model is loaded.

    Skips if models are currently being preloaded (status == 'loading').
    """
    if state.model_preload.get("status") == "loading":
        return None  # Still loading — don't flag as missing
    if not state.loaded_models:
        return "No transcription model available"
    return None


async def health_check_loop():
    """Continuous health monitor — runs for the lifetime of the application."""
    # Brief startup grace period to let DB initialize
    await asyncio.sleep(3)

    while True:
        try:
            if state.shutting_down:
                state.set_critical(["System shutting down"])
                return

            reasons = []

            # Check database
            db_reason = await _check_db()
            if db_reason:
                reasons.append(db_reason)

            # Check disk
            disk_reason = _check_disk()
            if disk_reason:
                reasons.append(disk_reason)

            # Check FFmpeg
            ffmpeg_reason = _check_ffmpeg()
            if ffmpeg_reason:
                reasons.append(ffmpeg_reason)

            # Check memory
            memory_reason = _check_memory()
            if memory_reason:
                reasons.append(memory_reason)

            # Check output directory
            output_reason = _check_output_dir()
            if output_reason:
                reasons.append(output_reason)

            # Check Redis (only if configured)
            redis_reason = await _check_redis()
            if redis_reason:
                reasons.append(redis_reason)

            # Check model availability
            model_reason = _check_model()
            if model_reason:
                reasons.append(model_reason)

            # Update state
            if reasons:
                state.set_critical(reasons)
            else:
                state.clear_critical()

            # Auto-detect incidents for status page (runs every cycle)
            try:
                from app.services.incident_logger import auto_detect_incidents

                await auto_detect_incidents()
            except Exception as e:
                logger.debug(f"HEALTH_MONITOR incident detection error: {e}")

        except Exception as e:
            logger.error(f"HEALTH_MONITOR Unexpected error: {e}")
            state.set_critical([f"Health monitor error: {e}"])

        await asyncio.sleep(CHECK_INTERVAL)

"""Background health monitor — continuously evaluates system health.

Runs as an asyncio task during the app lifespan. Checks all critical
subsystems every few seconds and sets/clears state.system_critical.

Critical conditions (any one triggers critical state):
- Database unreachable
- Disk space below 500 MB
- System shutting down
"""

import asyncio
import logging
import shutil

from app import state
from app.config import OUTPUT_DIR

logger = logging.getLogger("subtitle-generator")

# How often to check (seconds)
CHECK_INTERVAL = 5

# Minimum free disk space (bytes)
MIN_DISK_FREE_BYTES = 500 * 1024 * 1024  # 500 MB


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

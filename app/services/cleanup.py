"""Auto-cleanup service for old upload/output files.

Configurable retention period. Runs as a background task on startup
and periodically cleans files older than the retention threshold.
"""

import asyncio
import logging
import time
from pathlib import Path

from app.config import OUTPUT_DIR, UPLOAD_DIR
from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")

# Default retention: 24 hours (in seconds)
DEFAULT_RETENTION_SECONDS = 24 * 3600
# Cleanup interval: check every 30 minutes
CLEANUP_INTERVAL_SECONDS = 30 * 60


def cleanup_old_files(directory: Path, max_age_seconds: int = DEFAULT_RETENTION_SECONDS, dry_run: bool = False) -> dict:
    """Remove files older than max_age_seconds from directory.

    Returns summary of cleanup operation.
    """
    if not directory.exists():
        return {"directory": str(directory), "checked": 0, "removed": 0, "errors": 0}

    now = time.time()
    checked = 0
    removed = 0
    freed_bytes = 0
    errors = 0

    for f in directory.iterdir():
        if not f.is_file():
            continue
        checked += 1
        try:
            age = now - f.stat().st_mtime
            if age > max_age_seconds:
                size = f.stat().st_size
                if not dry_run:
                    f.unlink()
                removed += 1
                freed_bytes += size
                logger.debug(f"CLEANUP Removed {f.name} (age={age / 3600:.1f}h, size={size})")
        except Exception as e:
            errors += 1
            logger.warning(f"CLEANUP Failed to remove {f.name}: {e}")

    return {
        "directory": str(directory.name),
        "checked": checked,
        "removed": removed,
        "freed_bytes": freed_bytes,
        "errors": errors,
    }


async def periodic_cleanup(retention_seconds: int = DEFAULT_RETENTION_SECONDS):
    """Background task that periodically cleans old files."""
    logger.info(
        f"CLEANUP Background cleanup started (retention={retention_seconds / 3600:.1f}h, "
        f"interval={CLEANUP_INTERVAL_SECONDS / 60:.0f}min)"
    )
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)

            upload_result = await asyncio.to_thread(cleanup_old_files, UPLOAD_DIR, retention_seconds)
            output_result = await asyncio.to_thread(cleanup_old_files, OUTPUT_DIR, retention_seconds)

            total_removed = upload_result["removed"] + output_result["removed"]
            total_freed = upload_result["freed_bytes"] + output_result["freed_bytes"]

            if total_removed > 0:
                logger.info(
                    f"CLEANUP Removed {total_removed} files, freed {total_freed / 1024 / 1024:.1f} MB "
                    f"(uploads: {upload_result['removed']}, outputs: {output_result['removed']})"
                )
                log_task_event(
                    "system",
                    "cleanup",
                    uploads=upload_result,
                    outputs=output_result,
                    total_removed=total_removed,
                    total_freed_mb=round(total_freed / 1024 / 1024, 1),
                )

        except asyncio.CancelledError:
            logger.info("CLEANUP Background cleanup stopped")
            break
        except Exception as e:
            logger.error(f"CLEANUP Error during periodic cleanup: {e}")

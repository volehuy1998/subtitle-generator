"""Automatic incident detection and logging for the status page.

Monitors service components and creates/updates incidents when problems
are detected. Also provides manual incident management functions.
"""

import logging
import shutil
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import OUTPUT_DIR
from app.db.status_engine import get_status_session
from app.db.models import StatusIncident, StatusIncidentUpdate

logger = logging.getLogger("subtitle-generator")

# Track known open incidents to avoid duplicates
_open_incidents: dict[str, int] = {}  # component -> incident_id


async def create_incident(
    title: str,
    component: str,
    severity: str = "minor",
    message: str = "",
) -> int | None:
    """Create a new incident with an initial update."""
    try:
        async with get_status_session() as session:
            incident = StatusIncident(
                title=title,
                severity=severity,
                component=component,
                status="investigating",
            )
            session.add(incident)
            await session.flush()

            update = StatusIncidentUpdate(
                incident_id=incident.id,
                status="investigating",
                message=message or f"We are investigating reports of issues with {component}.",
            )
            session.add(update)

            _open_incidents[component] = incident.id
            logger.info(f"STATUS Incident created: [{incident.id}] {title} ({severity})")
            return incident.id
    except Exception as e:
        logger.error(f"STATUS Failed to create incident: {e}")
        return None


async def update_incident(
    incident_id: int,
    status: str,
    message: str,
) -> bool:
    """Add a status update to an existing incident."""
    try:
        async with get_status_session() as session:
            incident = await session.get(StatusIncident, incident_id)
            if not incident:
                return False

            incident.status = status
            if status == "resolved":
                incident.resolved_at = datetime.now(timezone.utc)
                # Remove from open incidents tracking
                for comp, iid in list(_open_incidents.items()):
                    if iid == incident_id:
                        del _open_incidents[comp]

            update = StatusIncidentUpdate(
                incident_id=incident_id,
                status=status,
                message=message,
            )
            session.add(update)

            logger.info(f"STATUS Incident [{incident_id}] updated: {status}")
            return True
    except Exception as e:
        logger.error(f"STATUS Failed to update incident: {e}")
        raise


async def resolve_incident(incident_id: int, message: str = "") -> bool:
    """Resolve an incident."""
    return await update_incident(
        incident_id,
        "resolved",
        message or "This incident has been resolved. All systems are operating normally.",
    )


async def auto_detect_incidents():
    """Run automatic incident detection. Called periodically from health checks.

    Checks each component and creates/resolves incidents based on current state.
    """
    # Check database
    try:
        from app.services.query_layer import check_db_health

        db_result = await check_db_health()
        db_ok = db_result.get("status") == "healthy"
    except Exception:
        db_ok = False

    if not db_ok and "database" not in _open_incidents:
        await create_incident(
            title="Database connectivity issues detected",
            component="database",
            severity="critical",
            message="The database health check is failing. Task persistence, analytics, "
            "and session tracking are affected. Tasks will continue to process "
            "but results may not be saved to the database. In-memory fallback is active.",
        )
    elif db_ok and "database" in _open_incidents:
        await resolve_incident(
            _open_incidents["database"],
            "Database connectivity has been restored. All persistence operations "
            "are functioning normally. Any tasks that were processed during the "
            "outage have been recovered from the in-memory cache.",
        )

    # Check FFmpeg
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    if not ffmpeg_ok and "storage" not in _open_incidents:
        await create_incident(
            title="FFmpeg not available — media processing degraded",
            component="storage",
            severity="major",
            message="FFmpeg is not found on the system PATH. This affects audio extraction "
            "from video files, media probing (duration/codec detection), subtitle "
            "embedding (both soft mux and hard burn), and the video combine feature. "
            "Transcription of pre-extracted audio files (WAV, MP3, FLAC) is still functional.",
        )
    elif ffmpeg_ok and "storage" in _open_incidents:
        await resolve_incident(
            _open_incidents["storage"],
            "FFmpeg is now available. All media processing capabilities have been restored, "
            "including audio extraction, subtitle embedding, and video combining.",
        )

    # Check disk space
    try:
        usage = shutil.disk_usage(str(OUTPUT_DIR))
        free_gb = usage.free / 1024**3
        if free_gb < 1.0 and "storage" not in _open_incidents:
            await create_incident(
                title="Low disk space — file storage at risk",
                component="storage",
                severity="major",
                message=f"Available disk space is critically low ({free_gb:.1f} GB remaining). "
                "New file uploads may fail and output files cannot be generated. "
                "The automatic cleanup job runs every 30 minutes and removes files "
                f"older than the retention period, but manual intervention may be needed.",
            )
    except Exception:
        pass


async def load_open_incidents():
    """Load currently open incidents from DB on startup."""
    try:
        async with get_status_session() as session:
            result = await session.execute(select(StatusIncident).where(StatusIncident.status != "resolved"))
            for inc in result.scalars().all():
                _open_incidents[inc.component] = inc.id
            if _open_incidents:
                logger.info(f"STATUS Loaded {len(_open_incidents)} open incidents")
    except Exception as e:
        logger.error(f"STATUS Failed to load open incidents: {e}")

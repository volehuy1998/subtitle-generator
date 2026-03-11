"""Frontend user activity tracking service.

Captures UI interactions (clicks, views, errors, flow events) and persists
to PostgreSQL for UX analysis, funnel tracking, and bug detection.
Falls back to JSONL file when database is unreachable.
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, and_

from app.config import LOG_DIR
from app.db.engine import get_session
from app.db.models import UIEvent

logger = logging.getLogger("subtitle-generator")

# In-memory buffer for batch writes (fire-and-forget)
_event_buffer: list[dict] = []
_BUFFER_MAX = 50

# File fallback when DB is unreachable
_TRACKING_FILE = LOG_DIR / "ui_events.jsonl"


def _write_event_to_file(event_type: str, target: str = "", session_id: str = "",
                         task_id: str = "", metadata: dict = None):
    """Write a UI event to JSONL file as fallback when DB is down."""
    try:
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "target": target,
            "session_id": session_id,
            "task_id": task_id,
            "metadata": metadata,
        }
        with open(_TRACKING_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Last resort — nothing more we can do


async def record_ui_event(
    event_type: str,
    target: str = "",
    session_id: str = "",
    task_id: str = "",
    metadata: Optional[dict] = None,
):
    """Persist a single UI event to the database, with file fallback."""
    try:
        async with get_session() as session:
            event = UIEvent(
                event_type=event_type,
                target=target,
                session_id=session_id or None,
                task_id=task_id or None,
                extra=json.dumps(metadata, default=str) if metadata else None,
            )
            session.add(event)
    except Exception as e:
        logger.error(f"TRACKING Failed to persist UI event: {e}")
        _write_event_to_file(event_type, target, session_id, task_id, metadata)


async def record_ui_events_batch(events: list[dict], session_id: str = ""):
    """Persist a batch of UI events, with file fallback."""
    try:
        async with get_session() as session:
            for evt in events:
                event = UIEvent(
                    event_type=evt.get("event", "unknown"),
                    target=evt.get("target", ""),
                    session_id=session_id or None,
                    task_id=evt.get("task_id") or None,
                    extra=json.dumps(evt.get("metadata"), default=str) if evt.get("metadata") else None,
                )
                session.add(event)
    except Exception as e:
        logger.error(f"TRACKING Failed to persist batch ({len(events)} events): {e}")
        for evt in events:
            _write_event_to_file(
                evt.get("event", "unknown"), evt.get("target", ""),
                session_id, evt.get("task_id", ""), evt.get("metadata"),
            )


async def get_feature_usage(hours: int = 24, limit: int = 20) -> list[dict]:
    """Get most-used features by click count."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with get_session() as session:
            result = await session.execute(
                select(UIEvent.target, func.count(UIEvent.id).label("count"))
                .where(and_(UIEvent.event_type == "click", UIEvent.timestamp >= cutoff, UIEvent.target.isnot(None)))
                .group_by(UIEvent.target)
                .order_by(func.count(UIEvent.id).desc())
                .limit(limit)
            )
            return [{"target": row.target, "count": row.count} for row in result]
    except Exception:
        return []


async def get_flow_funnel(hours: int = 24) -> dict:
    """Calculate user flow funnel: upload → process → download → embed."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with get_session() as session:
            stages = {}
            for stage in ["upload_start", "upload_complete", "transcription_done", "download_click", "embed_start", "embed_done"]:
                result = await session.execute(
                    select(func.count(func.distinct(UIEvent.session_id)))
                    .where(and_(UIEvent.target == stage, UIEvent.timestamp >= cutoff))
                )
                stages[stage] = result.scalar() or 0
            return stages
    except Exception:
        return {s: 0 for s in ["upload_start", "upload_complete", "transcription_done", "download_click", "embed_start", "embed_done"]}


async def get_error_events(hours: int = 24, limit: int = 50) -> list[dict]:
    """Get recent frontend errors."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with get_session() as session:
            result = await session.execute(
                select(UIEvent)
                .where(and_(UIEvent.event_type == "error", UIEvent.timestamp >= cutoff))
                .order_by(UIEvent.timestamp.desc())
                .limit(limit)
            )
            events = result.scalars().all()
            return [{
                "timestamp": e.timestamp.isoformat(),
                "session_id": e.session_id,
                "target": e.target,
                "metadata": json.loads(e.extra) if e.extra else None,
            } for e in events]
    except Exception:
        return []


async def get_session_activity(session_id: str, limit: int = 100) -> list[dict]:
    """Get activity timeline for a specific session."""
    try:
        async with get_session() as ses:
            result = await ses.execute(
                select(UIEvent)
                .where(UIEvent.session_id == session_id)
                .order_by(UIEvent.timestamp.desc())
                .limit(limit)
            )
            events = result.scalars().all()
            return [{
                "timestamp": e.timestamp.isoformat(),
                "event": e.event_type,
                "target": e.target,
                "task_id": e.task_id,
            } for e in events]
    except Exception:
        return []


async def get_activity_summary(hours: int = 24) -> dict:
    """Get activity summary: total events, unique sessions, top events."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with get_session() as session:
            # Total events
            total = await session.execute(
                select(func.count(UIEvent.id)).where(UIEvent.timestamp >= cutoff)
            )
            total_count = total.scalar() or 0

            # Unique sessions
            sessions = await session.execute(
                select(func.count(func.distinct(UIEvent.session_id))).where(UIEvent.timestamp >= cutoff)
            )
            unique_sessions = sessions.scalar() or 0

            # Events by type
            by_type = await session.execute(
                select(UIEvent.event_type, func.count(UIEvent.id).label("count"))
                .where(UIEvent.timestamp >= cutoff)
                .group_by(UIEvent.event_type)
                .order_by(func.count(UIEvent.id).desc())
            )
            type_counts = {row.event_type: row.count for row in by_type}

            return {
                "total_events": total_count,
                "unique_sessions": unique_sessions,
                "events_by_type": type_counts,
                "hours": hours,
            }
    except Exception:
        return {"total_events": 0, "unique_sessions": 0, "events_by_type": {}, "hours": hours}


async def cleanup_old_events(retention_days: int = 90):
    """Delete UI events older than retention period."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        async with get_session() as session:
            await session.execute(
                UIEvent.__table__.delete().where(UIEvent.timestamp < cutoff)
            )
            logger.info(f"TRACKING Cleaned up events older than {retention_days} days")
    except Exception as e:
        logger.error(f"TRACKING Cleanup failed: {e}")

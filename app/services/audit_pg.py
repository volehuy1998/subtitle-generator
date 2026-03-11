"""PostgreSQL-backed audit logging (replaces audit.jsonl).

Provides async DB operations for security audit events.
Keeps in-memory deque for fast recent-event access; DB for persistence.
"""

import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, text

from app.db.engine import get_session
from app.db.models import AuditLog

logger = logging.getLogger("subtitle-generator")


async def persist_audit_event(event_type: str, **kwargs) -> None:
    """Write an audit event to PostgreSQL."""
    ip = kwargs.pop("ip", None)
    path = kwargs.pop("path", None)
    details = json.dumps(kwargs, default=str) if kwargs else None
    try:
        async with get_session() as session:
            entry = AuditLog(
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                ip=ip,
                path=path,
                details=details,
            )
            session.add(entry)
    except Exception as e:
        logger.error(f"AUDIT_PG persist failed: {e}")


async def get_recent_events(limit: int = 50) -> list[dict]:
    """Get recent audit events from the database."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            events = []
            for r in rows:
                entry = {
                    "timestamp": r.timestamp.replace(tzinfo=timezone.utc).isoformat(),
                    "event": r.event_type,
                }
                if r.ip:
                    entry["ip"] = r.ip
                if r.path:
                    entry["path"] = r.path
                if r.details:
                    try:
                        entry.update(json.loads(r.details))
                    except (json.JSONDecodeError, TypeError):
                        entry["details"] = r.details
                events.append(entry)
            return list(reversed(events))  # chronological order
    except Exception as e:
        logger.error(f"AUDIT_PG get_recent_events failed: {e}")
        return []


async def get_audit_stats() -> dict:
    """Get audit event statistics from the database."""
    try:
        async with get_session() as session:
            # Total count
            total = await session.execute(select(func.count(AuditLog.id)))
            total_count = total.scalar() or 0

            # Count by event type
            result = await session.execute(
                select(AuditLog.event_type, func.count(AuditLog.id))
                .group_by(AuditLog.event_type)
            )
            type_counts = dict(result.all())

            return {
                "total_events": total_count,
                "event_types": type_counts,
            }
    except Exception as e:
        logger.error(f"AUDIT_PG get_audit_stats failed: {e}")
        return {"total_events": 0, "event_types": {}}


async def cleanup_old_events(retention_days: int = 90) -> int:
    """Delete audit events older than retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    try:
        async with get_session() as session:
            result = await session.execute(
                text("DELETE FROM audit_log WHERE timestamp < :cutoff"),
                {"cutoff": cutoff},
            )
            return result.rowcount
    except Exception as e:
        logger.error(f"AUDIT_PG cleanup failed: {e}")
        return 0

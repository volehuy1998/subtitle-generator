"""PostgreSQL-backed analytics persistence (replaces analytics_db.py SQLite).

Provides async DB operations for analytics events, daily aggregates,
and time-series data. In-memory counters in analytics.py remain the
hot-path for reads; this module handles durable writes.
"""

import json
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, text

from app.db.engine import get_session
from app.db.models import AnalyticsEvent, AnalyticsDaily, AnalyticsTimeseries

logger = logging.getLogger("subtitle-generator")


async def record_event(event_type: str, data: dict | None = None) -> None:
    """Record an analytics event to PostgreSQL."""
    try:
        async with get_session() as session:
            event = AnalyticsEvent(
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                data=json.dumps(data or {}, default=str),
            )
            session.add(event)
    except Exception as e:
        logger.error(f"ANALYTICS_PG record_event failed: {e}")


async def update_daily_stats(
    uploads: int = 0,
    completed: int = 0,
    failed: int = 0,
    cancelled: int = 0,
    processing_sec: float = 0,
    file_size: int = 0,
) -> None:
    """Upsert daily aggregated stats."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        async with get_session() as session:
            existing = await session.get(AnalyticsDaily, today)
            if existing:
                existing.uploads += uploads
                existing.completed += completed
                existing.failed += failed
                existing.cancelled += cancelled
                existing.total_processing_sec += processing_sec
            else:
                row = AnalyticsDaily(
                    date=today,
                    uploads=uploads,
                    completed=completed,
                    failed=failed,
                    cancelled=cancelled,
                    total_processing_sec=processing_sec,
                    avg_file_size=file_size,
                )
                session.add(row)
    except Exception as e:
        logger.error(f"ANALYTICS_PG update_daily_stats failed: {e}")


async def upsert_timeseries_point(
    minute_ts: datetime,
    uploads: int = 0,
    completed: int = 0,
    failed: int = 0,
    cancelled: int = 0,
    processing_sec: float = 0,
    task_count: int = 0,
) -> None:
    """Upsert a minute-resolution time-series point."""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(AnalyticsTimeseries).where(AnalyticsTimeseries.timestamp == minute_ts)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.uploads += uploads
                existing.completed += completed
                existing.failed += failed
                existing.cancelled += cancelled
                existing.total_processing_sec += processing_sec
                existing.task_count += task_count
            else:
                point = AnalyticsTimeseries(
                    timestamp=minute_ts,
                    uploads=uploads,
                    completed=completed,
                    failed=failed,
                    cancelled=cancelled,
                    total_processing_sec=processing_sec,
                    task_count=task_count,
                )
                session.add(point)
    except Exception as e:
        logger.error(f"ANALYTICS_PG upsert_timeseries failed: {e}")


async def get_timeseries(minutes: int = 60) -> list[dict]:
    """Get time-series data points for the last N minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    try:
        async with get_session() as session:
            result = await session.execute(
                select(AnalyticsTimeseries)
                .where(AnalyticsTimeseries.timestamp >= cutoff)
                .order_by(AnalyticsTimeseries.timestamp)
            )
            rows = result.scalars().all()
            return [
                {
                    "timestamp": int(r.timestamp.replace(tzinfo=timezone.utc).timestamp()),
                    "time": r.timestamp.replace(tzinfo=timezone.utc).isoformat(),
                    "uploads": r.uploads,
                    "completed": r.completed,
                    "failed": r.failed,
                    "cancelled": r.cancelled,
                    "avg_processing_sec": round(r.total_processing_sec / r.task_count if r.task_count > 0 else 0, 2),
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"ANALYTICS_PG get_timeseries failed: {e}")
        return []


async def get_daily_stats(days: int = 30) -> list[dict]:
    """Get daily aggregated stats for the last N days."""
    try:
        async with get_session() as session:
            result = await session.execute(select(AnalyticsDaily).order_by(AnalyticsDaily.date.desc()).limit(days))
            rows = result.scalars().all()
            return [
                {
                    "date": r.date,
                    "uploads": r.uploads,
                    "completed": r.completed,
                    "failed": r.failed,
                    "cancelled": r.cancelled,
                    "total_processing_sec": r.total_processing_sec,
                    "avg_file_size": r.avg_file_size,
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"ANALYTICS_PG get_daily_stats failed: {e}")
        return []


async def get_event_count(event_type: str | None = None) -> int:
    """Get total event count, optionally filtered by type."""
    try:
        async with get_session() as session:
            q = select(func.count(AnalyticsEvent.id))
            if event_type:
                q = q.where(AnalyticsEvent.event_type == event_type)
            result = await session.execute(q)
            return result.scalar() or 0
    except Exception as e:
        logger.error(f"ANALYTICS_PG get_event_count failed: {e}")
        return 0


async def get_summary_from_db() -> dict:
    """Get aggregated summary from the database (counters + distributions)."""
    try:
        async with get_session() as session:
            # Total counters from daily aggregates
            result = await session.execute(
                select(
                    func.sum(AnalyticsDaily.uploads).label("uploads"),
                    func.sum(AnalyticsDaily.completed).label("completed"),
                    func.sum(AnalyticsDaily.failed).label("failed"),
                    func.sum(AnalyticsDaily.cancelled).label("cancelled"),
                    func.sum(AnalyticsDaily.total_processing_sec).label("total_sec"),
                )
            )
            row = result.one()
            return {
                "uploads_total": row.uploads or 0,
                "completed_total": row.completed or 0,
                "failed_total": row.failed or 0,
                "cancelled_total": row.cancelled or 0,
                "total_processing_sec": row.total_sec or 0.0,
            }
    except Exception as e:
        logger.error(f"ANALYTICS_PG get_summary_from_db failed: {e}")
        return {}


async def cleanup_old_timeseries(retention_hours: int = 48) -> int:
    """Delete time-series points older than retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
    try:
        async with get_session() as session:
            result = await session.execute(
                text("DELETE FROM analytics_timeseries WHERE timestamp < :cutoff"),
                {"cutoff": cutoff},
            )
            return result.rowcount
    except Exception as e:
        logger.error(f"ANALYTICS_PG cleanup failed: {e}")
        return 0

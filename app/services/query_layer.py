"""Query layer for task search, pagination, and data management.

Provides cursor-based pagination, filtering, analytics rollup,
retention enforcement, and bulk export.
"""

import asyncio
import csv
import io
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, asc, desc, func, or_, select, text

from app.db.engine import get_session
from app.db.models import AnalyticsDaily, AnalyticsEvent, AuditLog, TaskRecord

logger = logging.getLogger("subtitle-generator")


class DatabaseUnavailableError(Exception):
    """Raised when a DB query fails due to connection issues."""

    pass


# ── Retention defaults ──

DEFAULT_RETENTION_DAYS = int(__import__("os").environ.get("DATA_RETENTION_DAYS", "90"))


# ── Task Search & Filtering ──


async def search_tasks(
    status: str = None,
    language: str = None,
    date_from: datetime = None,
    date_to: datetime = None,
    session_id: str = None,
    filename: str = None,
    cursor: str = None,
    limit: int = 20,
    sort: str = "desc",
) -> dict:
    """Search and filter tasks with cursor-based pagination.

    Returns {items: [...], next_cursor: str|None, total: int}.
    """
    try:
        async with get_session() as session:
            query = select(TaskRecord)
            count_query = select(func.count(TaskRecord.id))

            conditions = []
            if status:
                conditions.append(TaskRecord.status == status)
            if language:
                conditions.append(or_(TaskRecord.language == language, TaskRecord.language_requested == language))
            if date_from:
                conditions.append(TaskRecord.created_at >= date_from)
            if date_to:
                conditions.append(TaskRecord.created_at <= date_to)
            if session_id:
                conditions.append(TaskRecord.session_id == session_id)
            if filename:
                conditions.append(TaskRecord.filename.ilike(f"%{filename}%"))

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            # Cursor-based pagination (cursor = created_at ISO string)
            if cursor:
                try:
                    cursor_dt = datetime.fromisoformat(cursor)
                    if sort == "desc":
                        query = query.where(TaskRecord.created_at < cursor_dt)
                    else:
                        query = query.where(TaskRecord.created_at > cursor_dt)
                except ValueError:
                    pass

            # Ordering
            if sort == "desc":
                query = query.order_by(desc(TaskRecord.created_at))
            else:
                query = query.order_by(asc(TaskRecord.created_at))

            query = query.limit(limit + 1)  # Fetch one extra for next_cursor

            result = await session.execute(query)
            rows = result.scalars().all()

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            items = []
            next_cursor = None

            for i, task in enumerate(rows):
                if i >= limit:
                    # This extra row tells us there's more
                    next_cursor = items[-1]["created_at"] if items else None
                    break
                items.append(
                    {
                        "id": task.id,
                        "status": task.status,
                        "filename": task.filename,
                        "language": task.language,
                        "language_requested": task.language_requested,
                        "model_size": task.model_size,
                        "device": task.device,
                        "percent": task.percent,
                        "duration": task.duration,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "session_id": task.session_id,
                    }
                )

            return {"items": items, "next_cursor": next_cursor, "total": total, "limit": limit}
    except Exception as e:
        logger.error(f"QUERY search_tasks error: {e}")
        raise DatabaseUnavailableError(f"Task search unavailable: {e}") from e


# ── Analytics Rollup ──


async def get_analytics_rollup(period: str = "daily", days: int = 30) -> list[dict]:
    """Get aggregated analytics for the given period.

    period: 'daily', 'weekly', 'monthly'
    """
    try:
        async with get_session() as session:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            result = await session.execute(
                select(AnalyticsDaily).where(AnalyticsDaily.date >= cutoff).order_by(desc(AnalyticsDaily.date))
            )
            rows = result.scalars().all()
            items = [
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

            if period == "weekly":
                return _aggregate_by_week(items)
            elif period == "monthly":
                return _aggregate_by_month(items)
            return items
    except Exception as e:
        logger.error(f"QUERY analytics_rollup error: {e}")
        raise DatabaseUnavailableError(f"Analytics rollup unavailable: {e}") from e


def _aggregate_by_week(daily_items: list[dict]) -> list[dict]:
    """Aggregate daily data into weekly buckets."""
    from collections import defaultdict

    weeks = defaultdict(
        lambda: {"uploads": 0, "completed": 0, "failed": 0, "cancelled": 0, "total_processing_sec": 0.0}
    )
    for item in daily_items:
        try:
            dt = datetime.strptime(item["date"], "%Y-%m-%d")
            week_start = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
            w = weeks[week_start]
            for k in ("uploads", "completed", "failed", "cancelled"):
                w[k] += item.get(k, 0)
            w["total_processing_sec"] += item.get("total_processing_sec", 0.0)
        except (ValueError, KeyError):
            continue
    return [{"week": k, **v} for k, v in sorted(weeks.items(), reverse=True)]


def _aggregate_by_month(daily_items: list[dict]) -> list[dict]:
    """Aggregate daily data into monthly buckets."""
    from collections import defaultdict

    months = defaultdict(
        lambda: {"uploads": 0, "completed": 0, "failed": 0, "cancelled": 0, "total_processing_sec": 0.0}
    )
    for item in daily_items:
        try:
            month_key = item["date"][:7]  # YYYY-MM
            m = months[month_key]
            for k in ("uploads", "completed", "failed", "cancelled"):
                m[k] += item.get(k, 0)
            m["total_processing_sec"] += item.get("total_processing_sec", 0.0)
        except (ValueError, KeyError):
            continue
    return [{"month": k, **v} for k, v in sorted(months.items(), reverse=True)]


# ── Data Retention ──


async def enforce_retention(retention_days: int = None) -> dict:
    """Delete data older than retention period. Returns counts of deleted records."""
    days = retention_days or DEFAULT_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = {"retention_days": days, "deleted": {}}

    try:
        async with get_session() as session:
            # Tasks
            r = await session.execute(TaskRecord.__table__.delete().where(TaskRecord.created_at < cutoff))
            results["deleted"]["tasks"] = r.rowcount

            # Analytics events
            r = await session.execute(AnalyticsEvent.__table__.delete().where(AnalyticsEvent.timestamp < cutoff))
            results["deleted"]["analytics_events"] = r.rowcount

            # Audit logs
            r = await session.execute(AuditLog.__table__.delete().where(AuditLog.timestamp < cutoff))
            results["deleted"]["audit_logs"] = r.rowcount

        logger.info(f"RETENTION Enforced {days}d retention: {results['deleted']}")
    except Exception as e:
        logger.error(f"RETENTION enforcement error: {e}")
        raise DatabaseUnavailableError(f"Retention enforcement unavailable: {e}") from e

    return results


# ── Bulk Export ──


async def export_tasks_csv(status: str = None, limit: int = 10000) -> str:
    """Export tasks as CSV string."""
    try:
        async with get_session() as session:
            query = select(TaskRecord).order_by(desc(TaskRecord.created_at)).limit(limit)
            if status:
                query = query.where(TaskRecord.status == status)
            result = await session.execute(query)
            rows = result.scalars().all()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                ["id", "status", "filename", "language", "model_size", "device", "percent", "duration", "created_at"]
            )
            for r in rows:
                writer.writerow(
                    [
                        r.id,
                        r.status,
                        r.filename,
                        r.language,
                        r.model_size,
                        r.device,
                        r.percent,
                        r.duration,
                        r.created_at,
                    ]
                )
            return output.getvalue()
    except Exception as e:
        logger.error(f"EXPORT tasks CSV error: {e}")
        raise DatabaseUnavailableError(f"Task export unavailable: {e}") from e


async def export_tasks_json(status: str = None, limit: int = 10000) -> list[dict]:
    """Export tasks as JSON list."""
    try:
        async with get_session() as session:
            query = select(TaskRecord).order_by(desc(TaskRecord.created_at)).limit(limit)
            if status:
                query = query.where(TaskRecord.status == status)
            result = await session.execute(query)
            rows = result.scalars().all()
            return [r.to_dict() for r in rows]
    except Exception as e:
        logger.error(f"EXPORT tasks JSON error: {e}")
        raise DatabaseUnavailableError(f"Task export unavailable: {e}") from e


# ── DB Health Check ──


async def _db_health_ping() -> None:
    """Execute a simple SELECT 1 to verify database connectivity."""
    async with get_session() as session:
        await session.execute(text("SELECT 1"))


async def check_db_health() -> dict:
    """Check database health: pool status and query latency."""
    try:
        start = time.time()
        await asyncio.wait_for(_db_health_ping(), timeout=3.0)
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "ok": True,
        }
    except Exception as e:
        logger.error(f"DB health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "ok": False,
        }

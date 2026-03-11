"""Query layer routes: search, pagination, export, retention.

Provides efficient data access endpoints for tasks, analytics, and admin operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse

from app.services.query_layer import (
    search_tasks,
    get_analytics_rollup,
    enforce_retention,
    export_tasks_csv,
    export_tasks_json,
    check_db_health,
    DatabaseUnavailableError,
)

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Query"])


@router.get("/tasks/search")
async def task_search(
    status: Optional[str] = Query(None, description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    filename: Optional[str] = Query(None, description="Search by filename"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (ISO datetime)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query("desc", description="Sort order: asc or desc"),
):
    """Search and filter tasks with cursor-based pagination."""
    try:
        result = await search_tasks(
            status=status,
            language=language,
            filename=filename,
            cursor=cursor,
            limit=limit,
            sort=sort,
        )
        return result
    except DatabaseUnavailableError:
        raise HTTPException(503, "Database unavailable — task search requires a database connection.")


@router.get("/analytics/rollup")
async def analytics_rollup(
    period: str = Query("daily", description="Aggregation: daily, weekly, monthly"),
    days: int = Query(30, ge=1, le=365, description="Lookback days"),
):
    """Get aggregated analytics data."""
    try:
        data = await get_analytics_rollup(period=period, days=days)
        return {"period": period, "days": days, "data": data}
    except DatabaseUnavailableError:
        raise HTTPException(503, "Database unavailable — analytics rollup requires a database connection.")


@router.post("/admin/retention")
async def run_retention(
    days: int = Query(90, ge=1, le=3650, description="Retention period in days"),
):
    """Enforce data retention policy (delete old records)."""
    try:
        result = await enforce_retention(retention_days=days)
        return result
    except DatabaseUnavailableError:
        raise HTTPException(503, "Database unavailable — retention enforcement requires a database connection.")


@router.get("/admin/export/tasks")
async def export_tasks(
    format: str = Query("json", description="Export format: json or csv"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(1000, ge=1, le=10000, description="Max records"),
):
    """Export tasks as CSV or JSON."""
    try:
        if format == "csv":
            data = await export_tasks_csv(status=status, limit=limit)
            return PlainTextResponse(data, media_type="text/csv", headers={
                "Content-Disposition": "attachment; filename=tasks_export.csv"
            })
        data = await export_tasks_json(status=status, limit=limit)
        return {"tasks": data, "count": len(data)}
    except DatabaseUnavailableError:
        raise HTTPException(503, "Database unavailable — task export requires a database connection.")


@router.get("/health/db")
async def db_health():
    """Check database health and query latency."""
    result = await check_db_health()
    return result

"""Analytics endpoints: summary statistics, time-series, user tracking, export."""

import logging

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.services import analytics_pg
from app.services.analytics import export_analytics_csv, get_summary, get_timeseries, get_user_stats

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Analytics"])


@router.get("/analytics/summary")
async def analytics_summary():
    """Get analytics summary: totals, rates, averages, distributions.

    Returns counters (uploads, completions, failures), success/error rates,
    processing time stats (avg, p95, by model), and top language/model/device distributions.
    """
    return get_summary()


@router.get("/analytics/timeseries")
async def analytics_timeseries(
    minutes: int = Query(60, ge=1, le=1440, description="Number of minutes of data (1-1440)"),
):
    """Get time-series data points for charting.

    Returns per-minute data: uploads, completions, failures, avg processing time.
    Default: last 60 minutes. Max: 1440 minutes (24 hours).
    """
    # Try DB first for persistent data, fallback to in-memory
    db_points = await analytics_pg.get_timeseries(minutes)
    if db_points:
        return {"points": db_points, "minutes": minutes, "source": "db"}
    return {"points": get_timeseries(minutes), "minutes": minutes, "source": "memory"}


@router.get("/analytics/users")
async def analytics_users():
    """Get user tracking statistics.

    Returns unique users, user agent distribution, top users by request count,
    and error category breakdown.
    """
    return get_user_stats()


@router.get("/analytics/daily")
async def analytics_daily(days: int = Query(30, ge=1, le=365, description="Number of days of data")):
    """Get daily aggregated analytics from the database."""
    return {"days": await analytics_pg.get_daily_stats(days)}


@router.get("/analytics/export", response_class=PlainTextResponse)
async def analytics_export(format: str = Query("csv", description="Export format: csv or json")):
    """Export analytics data as CSV or JSON.

    CSV: time-series data (24h) with columns: timestamp, uploads, completed, failed, cancelled, avg_processing_sec.
    JSON: full analytics summary with user stats.
    """
    if format == "json":
        import json

        # Try DB time-series first
        db_ts = await analytics_pg.get_timeseries(minutes=1440)
        ts = db_ts if db_ts else get_timeseries(minutes=1440)
        data = {
            "summary": get_summary(),
            "users": get_user_stats(),
            "timeseries": ts,
            "daily": await analytics_pg.get_daily_stats(30),
        }
        return PlainTextResponse(
            json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_export.json"},
        )
    else:
        csv = export_analytics_csv()
        return PlainTextResponse(
            csv,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
        )

"""Monitoring & observability routes.

Provides business metrics, alerts, performance profiling,
and health dashboard endpoints.
"""

import logging

from fastapi import APIRouter, Query

from app.services.monitoring import (
    check_alerts,
    get_alert_history,
    get_alert_thresholds,
    get_business_metrics,
    get_health_dashboard,
    get_performance_profile,
    set_alert_threshold,
)

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Monitoring"])


@router.get("/monitoring/metrics")
async def business_metrics():
    """Get business metrics: uploads/hour, success rate, processing times."""
    return get_business_metrics()


@router.get("/monitoring/alerts")
async def active_alerts():
    """Check and return currently triggered alerts."""
    alerts = check_alerts()
    return {"alerts": alerts, "count": len(alerts), "status": "degraded" if alerts else "ok"}


@router.get("/monitoring/thresholds")
async def alert_thresholds():
    """Get current alert threshold configuration."""
    return get_alert_thresholds()


@router.put("/monitoring/thresholds/{name}")
async def update_threshold(name: str, value: float = Query(..., description="New threshold value")):
    """Update an alert threshold."""
    thresholds = get_alert_thresholds()
    if name not in thresholds:
        from fastapi import HTTPException

        raise HTTPException(404, f"Unknown threshold: {name}")
    set_alert_threshold(name, value)
    return {"ok": True, "name": name, "value": value}


@router.get("/monitoring/performance")
async def performance_profile():
    """Get performance profiling data by processing stage."""
    return get_performance_profile()


@router.get("/monitoring/alerts/history")
async def alert_history():
    """Alert history — last 200 triggered alerts with timestamps."""
    history = get_alert_history()
    return {"history": history, "count": len(history)}


@router.get("/monitoring/dashboard")
async def health_dashboard():
    """Comprehensive health dashboard (Grafana-compatible JSON)."""
    return get_health_dashboard()

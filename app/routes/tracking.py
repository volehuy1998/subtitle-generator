"""User activity tracking routes.

Receives frontend events (clicks, views, errors, flow events) and provides
analytics endpoints for UX analysis.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.tracking import (
    record_ui_event,
    record_ui_events_batch,
    get_feature_usage,
    get_flow_funnel,
    get_error_events,
    get_session_activity,
    get_activity_summary,
)

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Tracking"])


class TrackEvent(BaseModel):
    """Single UI event."""
    event: str = Field(..., max_length=50)
    target: str = Field("", max_length=100)
    task_id: str = Field("", max_length=36)
    metadata: Optional[dict] = None


class TrackBatch(BaseModel):
    """Batch of UI events."""
    events: list[TrackEvent] = Field(..., max_length=100)


@router.post("/track")
async def track_event(body: TrackEvent, request: Request):
    """Record a single frontend UI event."""
    session_id = getattr(request.state, "session_id", "")
    await record_ui_event(
        event_type=body.event,
        target=body.target,
        session_id=session_id,
        task_id=body.task_id,
        metadata=body.metadata,
    )
    return {"ok": True}


@router.post("/track/batch")
async def track_batch(body: TrackBatch, request: Request):
    """Record a batch of frontend UI events."""
    session_id = getattr(request.state, "session_id", "")
    events = [e.model_dump() for e in body.events]
    await record_ui_events_batch(events, session_id=session_id)
    return {"ok": True, "count": len(events)}


@router.get("/analytics/activity")
async def activity_summary(hours: int = 24):
    """Get user activity summary for the last N hours."""
    summary = await get_activity_summary(hours=hours)
    return summary


@router.get("/analytics/features")
async def feature_usage(hours: int = 24):
    """Get feature usage ranking (most-clicked buttons/features)."""
    features = await get_feature_usage(hours=hours)
    return {"features": features, "hours": hours}


@router.get("/analytics/funnel")
async def funnel_analysis(hours: int = 24):
    """Get user flow funnel: upload → process → download → embed."""
    funnel = await get_flow_funnel(hours=hours)

    # Calculate conversion rates
    rates = {}
    stages = ["upload_start", "upload_complete", "transcription_done", "download_click", "embed_start", "embed_done"]
    for i, stage in enumerate(stages):
        if i == 0:
            rates[stage] = 100.0
        elif funnel.get(stages[0], 0) > 0:
            rates[stage] = round(funnel.get(stage, 0) / funnel[stages[0]] * 100, 1)
        else:
            rates[stage] = 0.0

    return {"funnel": funnel, "conversion_rates": rates, "hours": hours}


@router.get("/analytics/errors")
async def frontend_errors(hours: int = 24, limit: int = 50):
    """Get recent frontend JavaScript errors."""
    errors = await get_error_events(hours=hours, limit=limit)
    return {"errors": errors, "count": len(errors)}


@router.get("/analytics/session/{session_id}")
async def session_timeline(session_id: str, limit: int = 100):
    """Get activity timeline for a specific session."""
    events = await get_session_activity(session_id, limit=limit)
    return {"session_id": session_id, "events": events, "count": len(events)}

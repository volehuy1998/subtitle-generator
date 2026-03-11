"""User feedback collection route."""

import json
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from app.config import LOG_DIR
from app.db.engine import get_session
from app.db.models import Feedback
from app.logging_setup import log_task_event

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["User"])

FEEDBACK_FILE = LOG_DIR / "feedback.jsonl"


class FeedbackRequest(BaseModel):
    task_id: str = ""
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit user feedback (1-5 star rating + optional comment)."""
    # Write to JSONL first (guaranteed local persistence)
    try:
        entry = {"timestamp": time.time(), "task_id": req.task_id,
                 "rating": req.rating, "comment": req.comment.strip()}
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"FEEDBACK file write failed: {e}")

    # Write to database (best-effort, feedback is safe in JSONL)
    try:
        async with get_session() as session:
            fb = Feedback(
                task_id=req.task_id or None,
                rating=req.rating,
                comment=req.comment.strip() or None,
            )
            session.add(fb)
    except Exception as e:
        logger.error(f"FEEDBACK DB save failed: {e}")
        # Don't raise — feedback is already persisted to JSONL file

    logger.info(f"FEEDBACK Rating={req.rating} Task={req.task_id[:8] if req.task_id else 'none'}")
    if req.task_id:
        log_task_event(req.task_id, "feedback", rating=req.rating)

    return {"message": "Thank you for your feedback!", "rating": req.rating}


@router.get("/feedback/summary")
async def feedback_summary():
    """Get feedback summary statistics."""
    try:
        async with get_session() as session:
            # Total count and average
            result = await session.execute(
                select(
                    func.count(Feedback.id).label("total"),
                    func.avg(Feedback.rating).label("avg_rating"),
                )
            )
            row = result.one()
            total = row.total or 0
            avg = round(float(row.avg_rating), 2) if row.avg_rating else 0

            # Distribution by rating
            dist_result = await session.execute(
                select(Feedback.rating, func.count(Feedback.id))
                .group_by(Feedback.rating)
            )
            ratings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for r, count in dist_result.all():
                if 1 <= r <= 5:
                    ratings[r] = count

            return {"total": total, "average_rating": avg, "ratings": ratings}
    except Exception as e:
        logger.error(f"FEEDBACK summary from DB failed: {e}")
        return {"total": 0, "average_rating": 0, "ratings": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}

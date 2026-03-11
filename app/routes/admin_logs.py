"""Admin log export endpoint.

Provides paginated, filterable access to structured JSON logs.
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

from app.config import LOG_DIR

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Admin"])

_DURATION_RE = re.compile(r"^(\d+)([hmd])$")


def _parse_since(since: str) -> Optional[datetime]:
    """Parse a duration string like '1h', '30m', '7d' into a cutoff datetime."""
    m = _DURATION_RE.match(since.strip())
    if not m:
        return None
    value, unit = int(m.group(1)), m.group(2)
    delta = {"h": timedelta(hours=value), "m": timedelta(minutes=value), "d": timedelta(days=value)}[unit]
    return datetime.now(timezone.utc) - delta


@router.get("/admin/logs")
async def export_logs(
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR)"),
    since: Optional[str] = Query(None, description="Time window (e.g., 1h, 30m, 7d)"),
    task_id: Optional[str] = Query(None, description="Filter by task_id"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Skip N entries"),
):
    """Export structured log entries with optional filtering."""
    log_file = LOG_DIR / "app.jsonl"
    entries = []

    cutoff = _parse_since(since) if since else None

    if not log_file.exists():
        return {"entries": [], "total": 0, "limit": limit, "offset": offset}

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Read in reverse (newest first)
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Apply filters
            if level and entry.get("level", "").upper() != level.upper():
                continue
            if task_id and entry.get("task_id") != task_id:
                continue
            if cutoff:
                try:
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts < cutoff:
                        break  # Entries are chronological, stop early
                except (KeyError, ValueError):
                    continue

            entries.append(entry)
            if len(entries) >= offset + limit:
                break

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        return {"entries": [], "total": 0, "error": str(e)}

    # Apply offset
    paginated = entries[offset:offset + limit]

    return {
        "entries": paginated,
        "total": len(entries),
        "limit": limit,
        "offset": offset,
    }

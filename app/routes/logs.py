"""Log viewing routes.

SECURITY NOTE: These endpoints expose application logs and task event logs.
Access control relies on the API key middleware in app/middleware/ -- when API_KEYS
is configured, all routes (including these) require a valid key. If API_KEYS is
empty (default dev mode), these endpoints are publicly accessible. Ensure API_KEYS
is set in production to prevent unauthorized log access.
"""

import json
from typing import Optional

from fastapi import APIRouter, Query

from app.config import LOG_DIR
from app.logging_setup import task_log_path

router = APIRouter()


@router.get("/logs/recent")
async def recent_logs(lines: int = Query(default=100, le=500)):
    log_file = LOG_DIR / "app.log"
    if not log_file.exists():
        return {"logs": []}
    content = log_file.read_text(encoding="utf-8")
    all_lines = content.strip().split("\n")
    return {"logs": all_lines[-lines:]}


@router.get("/logs/tasks")
async def task_logs(
    task_id: Optional[str] = Query(default=None, min_length=8, max_length=36),
    limit: int = Query(default=50, le=500),
):
    if not task_log_path.exists():
        return {"events": []}
    events = []
    with open(task_log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if task_id is None or entry.get("task_id", "").startswith(task_id):
                    events.append(entry)
            except json.JSONDecodeError:
                continue
    return {"events": events[-limit:]}

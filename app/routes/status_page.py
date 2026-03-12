"""Public status page — service health, uptime history, and incident timeline."""

import asyncio
import json
import logging
import shutil
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func

from app import state
from app.config import OUTPUT_DIR
from app.db.engine import get_session
from app.db.models import StatusIncident, StatusIncidentUpdate, TaskRecord

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Status"])
templates = Jinja2Templates(directory="templates")

_start_time = time.time()

# Service component definitions
COMPONENTS = [
    {"id": "transcription", "name": "Transcription Engine", "description": "faster-whisper AI transcription pipeline"},
    {"id": "combine", "name": "Video Combine", "description": "Subtitle embedding and video muxing"},
    {"id": "api", "name": "Web Application", "description": "FastAPI backend and frontend UI"},
    {"id": "database", "name": "Database", "description": "PostgreSQL task persistence and analytics"},
    {"id": "storage", "name": "File Storage", "description": "Upload and output file management"},
]


async def _check_component_status(component_id: str) -> dict:
    """Check real-time status of a service component."""
    if component_id == "transcription":
        active = sum(1 for t in state.tasks.values()
                     if t.get("status") in ("transcribing", "extracting"))
        return {"status": "operational", "detail": f"{active} active"}
    elif component_id == "combine":
        active = sum(1 for t in state.tasks.values()
                     if t.get("status") == "combining")
        return {"status": "operational", "detail": f"{active} active"}
    elif component_id == "api":
        return {"status": "operational", "detail": "serving requests"}
    elif component_id == "database":
        try:
            from app.services.query_layer import check_db_health
            result = await check_db_health()
            if result.get("status") == "healthy":
                latency = result.get("latency_ms", "?")
                return {"status": "operational", "detail": f"{latency}ms latency"}
            return {"status": "degraded", "detail": "slow response"}
        except Exception:
            return {"status": "outage", "detail": "connection failed"}
    elif component_id == "storage":
        try:
            usage = shutil.disk_usage(str(OUTPUT_DIR))
            free_gb = round(usage.free / 1024**3, 1)
            ffmpeg_ok = shutil.which("ffmpeg") is not None
            if not ffmpeg_ok:
                return {"status": "degraded", "detail": "ffmpeg missing"}
            if free_gb < 1.0:
                return {"status": "degraded", "detail": f"{free_gb}GB free"}
            return {"status": "operational", "detail": f"{free_gb}GB free"}
        except Exception:
            return {"status": "outage", "detail": "disk error"}
    return {"status": "operational", "detail": ""}


async def _get_uptime_history(days: int = 90) -> dict:
    """Calculate daily uptime for each component over the last N days."""
    history = {}
    today = datetime.now(timezone.utc).date()

    try:
        async with get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            result = await session.execute(
                select(StatusIncident).where(
                    StatusIncident.created_at >= cutoff
                ).order_by(StatusIncident.created_at.desc())
            )
            incidents = result.scalars().all()

            # Build per-component per-day incident map
            incident_days = defaultdict(lambda: defaultdict(list))
            for inc in incidents:
                start = inc.created_at.date()
                end = (inc.resolved_at or datetime.now(timezone.utc)).date()
                d = start
                while d <= end and d <= today:
                    incident_days[inc.component][d].append(inc.severity)
                    d += timedelta(days=1)

            for comp in COMPONENTS:
                comp_id = comp["id"]
                daily = []
                for i in range(days):
                    d = today - timedelta(days=days - 1 - i)
                    day_incidents = incident_days[comp_id].get(d, [])
                    if any(s in ("critical", "major") for s in day_incidents):
                        daily.append({"date": d.isoformat(), "status": "outage"})
                    elif any(s in ("minor",) for s in day_incidents):
                        daily.append({"date": d.isoformat(), "status": "degraded"})
                    elif any(s in ("maintenance",) for s in day_incidents):
                        daily.append({"date": d.isoformat(), "status": "maintenance"})
                    else:
                        daily.append({"date": d.isoformat(), "status": "operational"})

                operational_days = sum(1 for d in daily if d["status"] == "operational")
                uptime_pct = round((operational_days / days) * 100, 2) if days > 0 else 100.0
                history[comp_id] = {"daily": daily, "uptime_pct": uptime_pct}

    except Exception as e:
        logger.error(f"STATUS uptime history failed: {e}")
        for comp in COMPONENTS:
            history[comp["id"]] = {
                "daily": [{"date": (today - timedelta(days=days - 1 - i)).isoformat(),
                           "status": "operational"} for i in range(days)],
                "uptime_pct": 100.0,
            }

    return history


async def _get_incidents(days: int = 14, limit: int = 20) -> list:
    """Get recent incidents with their update timeline."""
    try:
        async with get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            result = await session.execute(
                select(StatusIncident).where(
                    StatusIncident.created_at >= cutoff
                ).order_by(StatusIncident.created_at.desc()).limit(limit)
            )
            incidents = result.scalars().all()

            items = []
            for inc in incidents:
                # Load updates
                updates_result = await session.execute(
                    select(StatusIncidentUpdate).where(
                        StatusIncidentUpdate.incident_id == inc.id
                    ).order_by(StatusIncidentUpdate.created_at.desc())
                )
                updates = updates_result.scalars().all()

                items.append({
                    "id": inc.id,
                    "title": inc.title,
                    "severity": inc.severity,
                    "component": inc.component,
                    "status": inc.status,
                    "created_at": inc.created_at.isoformat(),
                    "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
                    "updates": [{
                        "status": u.status,
                        "message": u.message,
                        "created_at": u.created_at.isoformat(),
                    } for u in updates],
                })
            return items
    except Exception as e:
        logger.error(f"STATUS get_incidents failed: {e}")
        return []


async def _get_task_stats() -> dict:
    """Get task completion stats for the last 24 hours."""
    try:
        async with get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await session.execute(
                select(
                    TaskRecord.status,
                    func.count(TaskRecord.id).label("count"),
                ).where(
                    TaskRecord.created_at >= cutoff
                ).group_by(TaskRecord.status)
            )
            stats = {row.status: row.count for row in result}
            return {
                "total_24h": sum(stats.values()),
                "completed_24h": stats.get("done", 0),
                "failed_24h": stats.get("error", 0),
                "cancelled_24h": stats.get("cancelled", 0),
            }
    except Exception:
        return {"total_24h": 0, "completed_24h": 0, "failed_24h": 0, "cancelled_24h": 0}


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Public status page — inspired by status.claude.com."""
    return templates.TemplateResponse("status.html", {"request": request})


_GITHUB_REPO = "volehuy1998/subtitle-generator"

# Cache commit data (refresh every 5 minutes)
_commits_cache: dict = {"data": None, "ts": 0}
_COMMITS_CACHE_TTL = 300


async def _fetch_github_json(path: str) -> dict | list | None:
    """Fetch JSON from GitHub API (public, no auth needed)."""
    import urllib.request
    url = f"https://api.github.com/repos/{_GITHUB_REPO}{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SubForge-Status",
    })
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=15))
    return json.loads(resp.read().decode())


@router.get("/api/status/commits")
async def status_commits():
    """Git commit history with CI/CD status from GitHub API."""
    now = time.time()
    if _commits_cache["data"] and (now - _commits_cache["ts"]) < _COMMITS_CACHE_TTL:
        return _commits_cache["data"]

    try:
        # Fetch commits and CI runs in parallel from GitHub API
        commits_data, runs_data = await asyncio.gather(
            _fetch_github_json("/commits?per_page=20"),
            _fetch_github_json("/actions/runs?per_page=30"),
            return_exceptions=True,
        )

        if isinstance(commits_data, Exception) or not commits_data:
            logger.error(f"GitHub commits fetch failed: {commits_data}")
            return {"commits": []}

        # Build CI status map
        ci_map = {}
        if not isinstance(runs_data, Exception) and runs_data:
            for run in runs_data.get("workflow_runs", []):
                sha = run.get("head_sha")
                if sha and sha not in ci_map:
                    ci_map[sha] = run.get("conclusion") or run.get("status", "unknown")

        commits = []
        for gh_commit in commits_data:
            sha = gh_commit["sha"]
            info = gh_commit.get("commit", {})
            message = info.get("message", "")
            # Split subject and body
            msg_parts = message.split("\n", 1)
            subject = msg_parts[0].strip()
            body = msg_parts[1].strip() if len(msg_parts) > 1 else ""
            # Remove Co-Authored-By lines
            body_lines = [ln for ln in body.split("\n")
                          if not ln.strip().startswith("Co-Authored-By:")]
            body = "\n".join(body_lines).strip()

            date = info.get("author", {}).get("date", "")
            files = gh_commit.get("files", [])

            commits.append({
                "sha": sha,
                "sha_short": sha[:7],
                "subject": subject,
                "body": body,
                "date": date,
                "ci_status": ci_map.get(sha, "unknown"),
                "files": [{"action": f.get("status", "modified")[0].upper(), "path": f["filename"]}
                          for f in files] if files else [],
                "files_count": len(files) if files else 0,
            })

        # If files not included in list endpoint, fetch per-commit detail for files
        # (GitHub /commits list doesn't include files, need per-commit endpoint)
        async def _fetch_commit_files(commit):
            try:
                detail = await _fetch_github_json(f"/commits/{commit['sha']}")
                if detail and "files" in detail:
                    commit["files"] = [
                        {"action": f.get("status", "modified")[0].upper(), "path": f["filename"]}
                        for f in detail["files"]
                    ]
                    commit["files_count"] = len(commit["files"])
            except Exception:
                pass

        # Fetch file details for all commits in parallel
        await asyncio.gather(*[_fetch_commit_files(c) for c in commits], return_exceptions=True)

        result = {"commits": commits}
        _commits_cache["data"] = result
        _commits_cache["ts"] = now
        return result
    except Exception as e:
        logger.error(f"STATUS commits failed: {e}")
        return {"commits": [], "error": str(e)}


@router.get("/api/status/page")
async def status_page_data():
    """JSON API for status page data — components, uptime, incidents."""
    uptime_sec = round(time.time() - _start_time, 1)

    # Check all components
    components = []
    overall = "operational"
    for comp in COMPONENTS:
        status_info = await _check_component_status(comp["id"])
        components.append({**comp, **status_info})
        if status_info["status"] == "outage":
            overall = "outage"
        elif status_info["status"] == "degraded" and overall == "operational":
            overall = "degraded"

    # Get uptime history
    uptime = await _get_uptime_history(90)

    # Get incidents
    incidents = await _get_incidents(14)

    # Get task stats
    task_stats = await _get_task_stats()

    return {
        "overall": overall,
        "uptime_sec": uptime_sec,
        "components": components,
        "uptime_history": uptime,
        "incidents": incidents,
        "task_stats": task_stats,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

"""Public status page — service health, uptime history, and incident timeline."""

import asyncio
import json
import logging
import os
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
from app.db.status_engine import get_status_session
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
    """Calculate uptime for each component using actual incident durations.

    Uptime % is based on total minutes, not whole days.
    Daily bars still show worst-severity status for each day.
    """
    history = {}
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    window_start = now_utc - timedelta(days=days)
    total_minutes = days * 24 * 60

    try:
        async with get_status_session() as session:
            cutoff = now_utc - timedelta(days=days)
            result = await session.execute(
                select(StatusIncident).where(
                    StatusIncident.created_at >= cutoff
                ).order_by(StatusIncident.created_at.desc())
            )
            incidents = result.scalars().all()

            # Build per-component incident list with clamped timestamps
            comp_incidents = defaultdict(list)
            for inc in incidents:
                # SQLite returns naive datetimes — make them timezone-aware
                inc_start = inc.created_at.replace(tzinfo=timezone.utc) if inc.created_at.tzinfo is None else inc.created_at
                inc_end = inc.resolved_at
                if inc_end is not None and inc_end.tzinfo is None:
                    inc_end = inc_end.replace(tzinfo=timezone.utc)
                start = max(inc_start, window_start)
                end = inc_end or now_utc
                end = min(end, now_utc)
                comp_incidents[inc.component].append({
                    "start": start, "end": end, "severity": inc.severity,
                })

            for comp in COMPONENTS:
                comp_id = comp["id"]
                inc_list = comp_incidents.get(comp_id, [])

                # Calculate total downtime minutes (critical/major = outage)
                downtime_minutes = 0.0
                for inc in inc_list:
                    if inc["severity"] in ("critical", "major"):
                        delta = (inc["end"] - inc["start"]).total_seconds() / 60.0
                        downtime_minutes += max(delta, 0)

                if total_minutes > 0 and downtime_minutes > 0:
                    uptime_pct = ((total_minutes - downtime_minutes) / total_minutes) * 100
                    uptime_pct = max(0.0, min(99.999999, uptime_pct))  # Never round to 100 if any downtime
                else:
                    uptime_pct = 100.0

                # Build daily status bars (worst severity per day for visual display)
                daily_severity = defaultdict(list)
                for inc in inc_list:
                    d = inc["start"].date()
                    end_date = inc["end"].date()
                    while d <= end_date and d <= today:
                        daily_severity[d].append(inc["severity"])
                        d += timedelta(days=1)

                daily = []
                for i in range(days):
                    d = today - timedelta(days=days - 1 - i)
                    sev_list = daily_severity.get(d, [])
                    if any(s in ("critical", "major") for s in sev_list):
                        daily.append({"date": d.isoformat(), "status": "outage"})
                    elif any(s == "minor" for s in sev_list):
                        daily.append({"date": d.isoformat(), "status": "degraded"})
                    elif any(s == "maintenance" for s in sev_list):
                        daily.append({"date": d.isoformat(), "status": "maintenance"})
                    else:
                        daily.append({"date": d.isoformat(), "status": "operational"})

                history[comp_id] = {
                    "daily": daily,
                    "uptime_pct": uptime_pct,
                    "downtime_min": round(downtime_minutes, 2),
                }

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
        async with get_status_session() as session:
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


def _get_inmemory_task_stats() -> dict:
    """Count task stats from in-memory state (includes tasks that failed to persist to DB)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    stats = defaultdict(int)
    seen_ids = set()
    for tid, t in state.tasks.items():
        task_status = t.get("status")
        if task_status not in ("done", "error", "cancelled"):
            continue
        created = t.get("created_at", "")
        if created:
            try:
                ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except (ValueError, TypeError):
                continue
        stats[task_status] += 1
        seen_ids.add(tid)
    return dict(stats), seen_ids


async def _get_task_stats() -> dict:
    """Get task completion stats for the last 24 hours.

    Queries PostgreSQL first, then merges in-memory state to capture tasks
    that failed to persist to DB (e.g. when DB was down during a critical abort).
    """
    db_stats = {}
    db_task_ids = set()
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
            db_stats = {row.status: row.count for row in result}
            # Get IDs already in DB to avoid double-counting
            id_result = await session.execute(
                select(TaskRecord.task_id).where(
                    TaskRecord.created_at >= cutoff
                )
            )
            db_task_ids = {row.task_id for row in id_result}
    except Exception:
        pass

    # Merge in-memory tasks not yet in DB
    mem_stats, mem_ids = _get_inmemory_task_stats()
    merged = dict(db_stats)
    for status, count in mem_stats.items():
        # Count how many in-memory tasks of this status are NOT in DB
        missing = 0
        for tid, t in state.tasks.items():
            if t.get("status") == status and tid not in db_task_ids:
                created = t.get("created_at", "")
                if created:
                    try:
                        ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                        if ts < cutoff:
                            continue
                    except (ValueError, TypeError):
                        continue
                missing += 1
        if missing > 0:
            merged[status] = merged.get(status, 0) + missing

    return {
        "total_24h": sum(merged.values()),
        "completed_24h": merged.get("done", 0),
        "failed_24h": merged.get("error", 0),
        "cancelled_24h": merged.get("cancelled", 0),
    }


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Public status page — inspired by status.claude.com."""
    return templates.TemplateResponse("status.html", {"request": request})


@router.get("/status/manage", response_class=HTMLResponse)
async def status_manage_page(request: Request):
    """Admin panel for managing service status and incidents."""
    return templates.TemplateResponse("status_admin.html", {"request": request})


@router.get("/api/status/incidents/open")
async def status_open_incidents():
    """Return all currently open (unresolved) incidents for the admin panel."""
    try:
        async with get_status_session() as session:
            result = await session.execute(
                select(StatusIncident).where(
                    StatusIncident.status != "resolved"
                ).order_by(StatusIncident.created_at.desc())
            )
            incidents = result.scalars().all()
            items = []
            for inc in incidents:
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
                    "updates": [{
                        "status": u.status,
                        "message": u.message,
                        "created_at": u.created_at.isoformat(),
                    } for u in updates],
                })
            return {"incidents": items}
    except Exception as e:
        logger.error(f"STATUS open_incidents failed: {e}")
        return {"incidents": []}


class CreateIncidentRequest(dict):
    pass


@router.post("/api/status/incidents")
async def create_incident_api(request: Request):
    """Create a new incident. Requires auth when API_KEYS is configured."""
    from app.services.incident_logger import create_incident
    try:
        body = await request.json()
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})

    title = (body.get("title") or "").strip()
    component = (body.get("component") or "").strip()
    severity = body.get("severity", "minor")
    message = (body.get("message") or "").strip()

    if not title or not component:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={"detail": "title and component are required"})
    if severity not in ("minor", "major", "critical", "maintenance"):
        severity = "minor"
    if component not in {c["id"] for c in COMPONENTS}:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={"detail": f"Unknown component: {component}"})

    incident_id = await create_incident(title=title, component=component, severity=severity, message=message)
    if incident_id is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": "Failed to create incident"})
    return {"id": incident_id, "title": title, "status": "investigating"}


@router.post("/api/status/incidents/{incident_id}/update")
async def update_incident_api(incident_id: int, request: Request):
    """Add a status update to an existing incident."""
    from app.services.incident_logger import update_incident
    try:
        body = await request.json()
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})

    status = (body.get("status") or "").strip()
    message = (body.get("message") or "").strip()

    if status not in ("investigating", "identified", "monitoring", "resolved"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={"detail": "Invalid status"})
    if not message:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=422, content={"detail": "message is required"})

    ok = await update_incident(incident_id, status, message)
    if not ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": "Incident not found"})
    return {"id": incident_id, "status": status}


@router.post("/api/status/incidents/{incident_id}/resolve")
async def resolve_incident_api(incident_id: int, request: Request):
    """Resolve an incident."""
    from app.services.incident_logger import resolve_incident
    try:
        body = await request.json()
    except Exception:
        body = {}
    message = (body.get("message") or "").strip()
    try:
        ok = await resolve_incident(incident_id, message)
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": f"Database error: {e}"})
    if not ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": "Incident not found"})
    return {"id": incident_id, "status": "resolved"}


_GITHUB_REPO = "volehuy1998/subtitle-generator"

# Cache commit data (300s TTL to stay within GitHub's 60 req/hr unauthenticated limit)
_commits_cache: dict = {"data": None, "ts": 0}
_COMMITS_CACHE_TTL = 300

# Optional GitHub token for higher rate limits (5000/hr vs 60/hr)
_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


async def _fetch_github_json(path: str) -> dict | list | None:
    """Fetch JSON from GitHub API."""
    import urllib.request
    url = f"https://api.github.com/repos/{_GITHUB_REPO}{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SubForge-Status",
    }
    if _GITHUB_TOKEN:
        headers["Authorization"] = f"token {_GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
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
        # Fetch commits and CI runs in parallel (2 API calls only)
        commits_data, runs_data = await asyncio.gather(
            _fetch_github_json("/commits?per_page=20"),
            _fetch_github_json("/actions/runs?per_page=30"),
            return_exceptions=True,
        )

        if isinstance(commits_data, Exception) or not commits_data:
            logger.error(f"GitHub commits fetch failed: {commits_data}")
            # On failure, serve stale cache if available; otherwise empty
            # Back off for 5 minutes before retrying to avoid hammering rate limit
            _commits_cache["ts"] = now - _COMMITS_CACHE_TTL + 300
            if _commits_cache["data"]:
                return _commits_cache["data"]
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

            commits.append({
                "sha": sha,
                "sha_short": sha[:7],
                "subject": subject,
                "body": body,
                "date": date,
                "ci_status": ci_map.get(sha, "unknown"),
                "stats": gh_commit.get("stats", {}),
            })

        # Fetch file details only for the 5 most recent commits (saves rate limit)
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

        await asyncio.gather(
            *[_fetch_commit_files(c) for c in commits[:5]],
            return_exceptions=True,
        )

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
        "sla_target": 99.9,
        "components": components,
        "uptime_history": uptime,
        "incidents": incidents,
        "task_stats": task_stats,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

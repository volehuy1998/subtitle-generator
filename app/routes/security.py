"""Security audit routes."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from app.middleware.auth import is_auth_enabled, validate_api_key
from app.services.audit import get_recent_audit_events, get_audit_stats, log_audit_event
from app.middleware.brute_force import get_brute_force_stats

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["System"])

_ASSERTIONS_FILE = Path(__file__).parent.parent.parent / "data" / "security_assertions.json"


def load_security_assertions() -> dict:
    """Load security assertion data from JSON store."""
    try:
        with open(_ASSERTIONS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"last_updated": None, "last_run_commit": None, "assertions": []}


def _require_admin(request: Request):
    """Require API key auth for security endpoints."""
    if not is_auth_enabled():
        return  # No auth configured, allow access
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key or not validate_api_key(api_key):
        raise HTTPException(403, "Admin access required")


@router.get("/security/audit")
async def security_audit(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Number of recent events"),
):
    """Get recent security audit events (admin only).

    Returns audit log entries including auth events, API key usage,
    file quarantine events, and rate limit triggers.
    """
    _require_admin(request)
    log_audit_event("audit_accessed", ip=request.client.host if request.client else "unknown")
    events = get_recent_audit_events(limit)
    stats = get_audit_stats()
    brute_force = get_brute_force_stats()
    return {
        "events": events,
        "stats": stats,
        "brute_force": brute_force,
    }


@router.get("/api/security/assertions")
async def get_security_assertions():
    """Return current security assertion statuses (public)."""
    return load_security_assertions()


@router.post("/api/security/assertions")
async def update_security_assertions(request: Request, payload: dict):
    """Update security assertion statuses (admin only).

    Accepts the same JSON shape as security_assertions.json.
    Typically called by the update_security_assertions.py script via CI.
    """
    _require_admin(request)
    import json as _json

    _ASSERTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_ASSERTIONS_FILE, "w") as f:
        _json.dump(payload, f, indent=2)
    return {"ok": True, "message": "Assertions updated"}

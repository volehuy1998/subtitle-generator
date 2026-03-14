"""Audit logging service for security events and admin actions.

Records all auth events, API key usage, and security-relevant actions
to a dedicated audit log file (logs/audit.jsonl).
"""

import asyncio
import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone

from app.config import LOG_DIR

logger = logging.getLogger("subtitle-generator")
_lock = threading.Lock()

# In-memory audit buffer for quick access
_audit_entries: deque[dict] = deque(maxlen=1000)
_audit_log_path = LOG_DIR / "audit.jsonl"


def log_audit_event(event_type: str, **kwargs):
    """Log a security audit event.

    Event types: auth_success, auth_failure, upload, download, share_created,
    webhook_registered, rate_limited, suspicious_file, etc.
    """
    entry = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "event": event_type,
        **kwargs,
    }

    with _lock:
        _audit_entries.append(entry)

    # Write to audit log file
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(_audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")

    logger.info(f"AUDIT {event_type} {kwargs}")

    # Persist to PostgreSQL (fire-and-forget)
    from app import state

    loop = state.main_event_loop
    if loop is not None and not loop.is_closed():
        from app.services import audit_pg

        asyncio.run_coroutine_threadsafe(audit_pg.persist_audit_event(event_type, **kwargs), loop)


def get_recent_audit_events(limit: int = 50) -> list[dict]:
    """Get recent audit events from memory buffer."""
    with _lock:
        events = list(_audit_entries)
    return events[-limit:]


def get_audit_stats() -> dict:
    """Get summary statistics from audit events."""
    with _lock:
        events = list(_audit_entries)

    type_counts = {}
    for e in events:
        t = e.get("event", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_events": len(events),
        "event_types": type_counts,
    }

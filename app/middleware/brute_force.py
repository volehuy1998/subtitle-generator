"""Brute force protection middleware.

Tracks failed authentication attempts per IP and blocks IPs that exceed
the threshold within the time window.
"""

import logging
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.access import get_client_ip

logger = logging.getLogger("subtitle-generator")
_lock = threading.Lock()

# Config
MAX_FAILURES = 10  # max failed attempts before blocking
WINDOW_SEC = 300  # 5-minute window
BLOCK_SEC = 600  # 10-minute block

# State: ip -> {"failures": [(timestamp, ...)], "blocked_until": float}
_tracker: dict[str, dict] = {}


def record_auth_failure(ip: str):
    """Record a failed auth attempt for an IP."""
    now = time.time()
    with _lock:
        entry = _tracker.setdefault(ip, {"failures": [], "blocked_until": 0})
        entry["failures"].append(now)
        # Prune old failures
        cutoff = now - WINDOW_SEC
        entry["failures"] = [t for t in entry["failures"] if t > cutoff]
        if len(entry["failures"]) >= MAX_FAILURES:
            entry["blocked_until"] = now + BLOCK_SEC
            logger.warning(f"BRUTE_FORCE IP {ip} blocked for {BLOCK_SEC}s after {len(entry['failures'])} failures")


def is_ip_blocked(ip: str) -> bool:
    """Check if an IP is currently blocked."""
    with _lock:
        entry = _tracker.get(ip)
        if not entry:
            return False
        if entry["blocked_until"] > time.time():
            return True
        return False


def get_brute_force_stats() -> dict:
    """Get brute force protection statistics."""
    now = time.time()
    with _lock:
        blocked = sum(1 for e in _tracker.values() if e["blocked_until"] > now)
        tracked = len(_tracker)
    return {
        "tracked_ips": tracked,
        "currently_blocked": blocked,
        "max_failures": MAX_FAILURES,
        "window_sec": WINDOW_SEC,
        "block_sec": BLOCK_SEC,
    }


class BruteForceMiddleware(BaseHTTPMiddleware):
    """Block requests from IPs with too many failed auth attempts."""

    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        if is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Too many failed attempts. Your IP is temporarily blocked for {BLOCK_SEC // 60} minutes."
                },
            )
        return await call_next(request)

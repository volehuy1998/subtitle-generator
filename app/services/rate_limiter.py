"""Sliding window rate limiter with per-user/IP tracking.

Provides in-memory rate limiting with optional DB persistence,
IP allowlist/blocklist, and per-user concurrent task quotas.
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Optional

from app.config import MAX_CONCURRENT_TASKS

logger = logging.getLogger("subtitle-generator")

_lock = threading.Lock()

# ── Rate limit buckets: key -> [(timestamp, ...)] ──
_buckets: dict[str, list[float]] = defaultdict(list)

# ── IP allowlist/blocklist ──
_ip_allowlist: set[str] = set()
_ip_blocklist: set[str] = set()

# ── Per-user concurrent task tracking ──
_user_tasks: dict[str, int] = defaultdict(int)

# ── Configuration ──
DEFAULT_RATE_LIMIT = 60  # requests per window
DEFAULT_WINDOW_SEC = 60  # 1-minute window
UPLOAD_RATE_LIMIT = 5    # uploads per minute
PER_USER_MAX_TASKS = int(__import__("os").environ.get("PER_USER_MAX_TASKS", str(MAX_CONCURRENT_TASKS)))


def check_rate_limit(key: str, limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_WINDOW_SEC) -> tuple[bool, dict]:
    """Check if a request is within rate limits.

    Returns (allowed, info) where info contains retry_after, remaining, limit.
    """
    now = time.time()
    cutoff = now - window

    with _lock:
        bucket = _buckets[key]
        # Prune old entries
        _buckets[key] = [t for t in bucket if t > cutoff]
        bucket = _buckets[key]

        if len(bucket) >= limit:
            retry_after = int(bucket[0] + window - now) + 1
            return False, {
                "retry_after": max(retry_after, 1),
                "remaining": 0,
                "limit": limit,
                "window": window,
            }

        bucket.append(now)
        return True, {
            "retry_after": 0,
            "remaining": limit - len(bucket),
            "limit": limit,
            "window": window,
        }


def get_rate_limit_headers(info: dict) -> dict:
    """Generate standard rate limit response headers."""
    headers = {
        "X-RateLimit-Limit": str(info["limit"]),
        "X-RateLimit-Remaining": str(info["remaining"]),
    }
    if info["retry_after"] > 0:
        headers["Retry-After"] = str(info["retry_after"])
    return headers


# ── IP allowlist/blocklist ──

def add_to_allowlist(ip: str):
    with _lock:
        _ip_allowlist.add(ip)


def remove_from_allowlist(ip: str):
    with _lock:
        _ip_allowlist.discard(ip)


def add_to_blocklist(ip: str):
    with _lock:
        _ip_blocklist.add(ip)


def remove_from_blocklist(ip: str):
    with _lock:
        _ip_blocklist.discard(ip)


def is_ip_allowed(ip: str) -> Optional[bool]:
    """Check IP against allowlist/blocklist.

    Returns True (allowed), False (blocked), or None (no list match).
    """
    with _lock:
        if ip in _ip_blocklist:
            return False
        if _ip_allowlist and ip in _ip_allowlist:
            return True
    return None


def get_ip_lists() -> dict:
    """Get current allowlist and blocklist."""
    with _lock:
        return {
            "allowlist": sorted(_ip_allowlist),
            "blocklist": sorted(_ip_blocklist),
        }


# ── Per-user task quota ──

def check_user_task_quota(user_id: str) -> bool:
    """Check if user can start a new task (within quota)."""
    with _lock:
        return _user_tasks.get(user_id, 0) < PER_USER_MAX_TASKS


def increment_user_tasks(user_id: str):
    with _lock:
        _user_tasks[user_id] = _user_tasks.get(user_id, 0) + 1


def decrement_user_tasks(user_id: str):
    with _lock:
        count = _user_tasks.get(user_id, 0)
        if count > 0:
            _user_tasks[user_id] = count - 1


def get_user_task_count(user_id: str) -> int:
    with _lock:
        return _user_tasks.get(user_id, 0)


def get_rate_limit_stats() -> dict:
    """Get rate limiting statistics."""
    with _lock:
        return {
            "active_buckets": len(_buckets),
            "allowlist_size": len(_ip_allowlist),
            "blocklist_size": len(_ip_blocklist),
            "tracked_users": len(_user_tasks),
            "per_user_max_tasks": PER_USER_MAX_TASKS,
        }

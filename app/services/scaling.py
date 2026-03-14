"""Scalability utilities for multi-instance deployment.

Provides Redis-compatible cache/session interface, worker management,
connection pool configuration, and task queue abstractions.
"""

import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("subtitle-generator")

# ── Redis Configuration ──

REDIS_URL = os.environ.get("REDIS_URL", "")  # e.g., redis://localhost:6379/0
REDIS_ENABLED = bool(REDIS_URL)


class MemoryCache:
    """In-memory cache backend (fallback when Redis unavailable).

    Thread-safe, TTL-aware, compatible with Redis-like interface.
    """

    def __init__(self):
        self._store: dict[str, tuple[float, str]] = {}  # key -> (expires_at, value)
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if expires_at and time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: str, ttl: int = 0):
        with self._lock:
            expires_at = time.time() + ttl if ttl > 0 else 0
            self._store[key] = (expires_at, value)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def incr(self, key: str) -> int:
        with self._lock:
            entry = self._store.get(key)
            if entry:
                expires_at, value = entry
                try:
                    new_val = int(value) + 1
                except ValueError:
                    new_val = 1
                self._store[key] = (expires_at, str(new_val))
                return new_val
            self._store[key] = (0, "1")
            return 1

    def keys(self, pattern: str = "*") -> list[str]:
        with self._lock:
            if pattern == "*":
                return list(self._store.keys())
            import fnmatch

            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def flush(self):
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            now = time.time()
            active = sum(1 for exp, _ in self._store.values() if not exp or exp > now)
            return {"total_keys": len(self._store), "active_keys": active}


# Global cache instance
_cache = MemoryCache()


def get_cache() -> MemoryCache:
    """Get the cache backend (MemoryCache or Redis wrapper)."""
    return _cache


# ── Worker Management ──

_WORKER_ID = str(uuid.uuid4())[:12]
_WORKER_START = datetime.now(timezone.utc)
_workers: dict[str, dict] = {}  # worker_id -> info
_workers_lock = threading.Lock()


def get_worker_id() -> str:
    """Get this instance's unique worker ID."""
    return _WORKER_ID


def register_worker(worker_id: str = None, hostname: str = None):
    """Register a worker (self or remote)."""
    wid = worker_id or _WORKER_ID
    with _workers_lock:
        _workers[wid] = {
            "id": wid,
            "hostname": hostname or os.environ.get("HOSTNAME", "localhost"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "tasks_processed": 0,
        }


def heartbeat_worker(worker_id: str = None):
    """Update worker heartbeat timestamp."""
    wid = worker_id or _WORKER_ID
    with _workers_lock:
        if wid in _workers:
            _workers[wid]["last_heartbeat"] = datetime.now(timezone.utc).isoformat()


def get_workers() -> list[dict]:
    """Get all registered workers."""
    with _workers_lock:
        return list(_workers.values())


def cleanup_dead_workers(timeout_sec: int = 120) -> int:
    """Remove workers with stale heartbeats. Returns count removed."""
    cutoff = time.time() - timeout_sec
    removed = 0
    with _workers_lock:
        dead = []
        for wid, info in _workers.items():
            try:
                hb = datetime.fromisoformat(info["last_heartbeat"])
                if hb.timestamp() < cutoff:
                    dead.append(wid)
            except (KeyError, ValueError):
                dead.append(wid)
        for wid in dead:
            del _workers[wid]
            removed += 1
    return removed


# ── Connection Pool Configuration ──


def get_pool_config() -> dict:
    """Get database connection pool configuration from environment."""
    from app.config import DB_MAX_OVERFLOW, DB_POOL_RECYCLE, DB_POOL_SIZE

    return {
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "pool_recycle": DB_POOL_RECYCLE,
        "pool_pre_ping": True,
    }


# ── Task Queue Abstraction ──


class InMemoryTaskQueue:
    """Simple in-memory task queue (replaced by Redis in production)."""

    def __init__(self, max_size: int = 100):
        self._queue: list[dict] = []
        self._lock = threading.Lock()
        self._max_size = max_size

    def enqueue(self, task: dict) -> bool:
        with self._lock:
            if len(self._queue) >= self._max_size:
                return False
            self._queue.append(task)
            return True

    def dequeue(self) -> Optional[dict]:
        with self._lock:
            return self._queue.pop(0) if self._queue else None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def peek(self) -> Optional[dict]:
        with self._lock:
            return self._queue[0] if self._queue else None

    def clear(self):
        with self._lock:
            self._queue.clear()


_task_queue = InMemoryTaskQueue()


def get_task_queue() -> InMemoryTaskQueue:
    """Get the task queue backend."""
    return _task_queue


# ── Scale Info ──


def get_scale_info() -> dict:
    """Get scaling/multi-instance status information."""
    return {
        "worker_id": _WORKER_ID,
        "started_at": _WORKER_START.isoformat(),
        "redis_enabled": REDIS_ENABLED,
        "redis_url": REDIS_URL[:20] + "..." if REDIS_URL else "",
        "workers": get_workers(),
        "pool_config": get_pool_config(),
        "cache_stats": _cache.stats(),
        "queue_size": _task_queue.size(),
    }


# Register self on import
register_worker()

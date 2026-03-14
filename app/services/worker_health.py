"""Worker health monitoring.

Tracks worker heartbeats and provides health status for each worker.
In single-process mode, monitors the main worker.
Designed for multi-worker monitoring in horizontal scaling scenarios.
"""

import logging
import os
import threading
import time

logger = logging.getLogger("subtitle-generator")
_lock = threading.Lock()

# Worker registry: worker_id -> {last_heartbeat, status, tasks_processed, started_at}
_workers: dict[str, dict] = {}

HEARTBEAT_INTERVAL = 30  # seconds
WORKER_TIMEOUT = 90  # consider dead after this many seconds without heartbeat


def register_worker(worker_id: str | None = None) -> str:
    """Register a worker and return its ID."""
    if worker_id is None:
        worker_id = f"worker-{os.getpid()}"

    now = time.time()
    with _lock:
        _workers[worker_id] = {
            "last_heartbeat": now,
            "status": "active",
            "tasks_processed": 0,
            "started_at": now,
            "pid": os.getpid(),
        }
    logger.info(f"WORKER Registered: {worker_id} (PID {os.getpid()})")
    return worker_id


def heartbeat(worker_id: str) -> None:
    """Update worker heartbeat timestamp."""
    with _lock:
        if worker_id in _workers:
            _workers[worker_id]["last_heartbeat"] = time.time()


def record_task_processed(worker_id: str) -> None:
    """Increment task counter for a worker."""
    with _lock:
        if worker_id in _workers:
            _workers[worker_id]["tasks_processed"] += 1


def get_worker_status() -> list[dict]:
    """Get status of all registered workers."""
    now = time.time()
    result = []
    with _lock:
        for wid, info in _workers.items():
            elapsed = now - info["last_heartbeat"]
            status = "active" if elapsed < WORKER_TIMEOUT else "unresponsive"
            uptime = now - info["started_at"]
            result.append(
                {
                    "worker_id": wid,
                    "status": status,
                    "pid": info["pid"],
                    "tasks_processed": info["tasks_processed"],
                    "uptime_sec": round(uptime, 1),
                    "last_heartbeat_sec_ago": round(elapsed, 1),
                }
            )
    return result


def get_healthy_worker_count() -> int:
    """Count workers that are responsive."""
    now = time.time()
    with _lock:
        return sum(1 for info in _workers.values() if now - info["last_heartbeat"] < WORKER_TIMEOUT)


def cleanup_dead_workers() -> int:
    """Remove workers that haven't sent heartbeat in a long time. Returns count removed."""
    now = time.time()
    removed = 0
    with _lock:
        dead = [wid for wid, info in _workers.items() if now - info["last_heartbeat"] > WORKER_TIMEOUT * 3]
        for wid in dead:
            del _workers[wid]
            removed += 1
    if removed:
        logger.warning(f"WORKER Cleaned up {removed} dead worker(s)")
    return removed

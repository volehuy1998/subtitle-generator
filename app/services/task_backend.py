"""Task state backend abstraction.

Provides a pluggable backend for task state storage. Default: in-memory (dict).
When TASK_BACKEND=redis and REDIS_URL is set, uses Redis for shared state
across multiple workers (not yet implemented, placeholder for future).

This abstraction allows swapping storage without touching business logic.
"""

import logging
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger("subtitle-generator")


class TaskBackend(ABC):
    """Abstract task state storage backend."""

    @abstractmethod
    def get(self, task_id: str) -> dict | None:
        """Get task data by ID."""

    @abstractmethod
    def set(self, task_id: str, data: dict) -> None:
        """Set task data."""

    @abstractmethod
    def delete(self, task_id: str) -> None:
        """Delete a task."""

    @abstractmethod
    def items(self) -> list[tuple[str, dict]]:
        """Return all (task_id, data) pairs."""

    @abstractmethod
    def keys(self) -> list[str]:
        """Return all task IDs."""

    @abstractmethod
    def contains(self, task_id: str) -> bool:
        """Check if task exists."""

    @abstractmethod
    def count(self) -> int:
        """Return total task count."""


class InMemoryTaskBackend(TaskBackend):
    """Default in-memory task backend using a dict with thread lock."""

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def set(self, task_id: str, data: dict) -> None:
        self._tasks[task_id] = data

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def items(self) -> list[tuple[str, dict]]:
        return list(self._tasks.items())

    def keys(self) -> list[str]:
        return list(self._tasks.keys())

    def contains(self, task_id: str) -> bool:
        return task_id in self._tasks

    def count(self) -> int:
        return len(self._tasks)

    @property
    def raw(self) -> dict[str, dict]:
        """Direct access to underlying dict for backward compatibility."""
        return self._tasks


# Singleton
_backend: TaskBackend | None = None


def get_task_backend() -> TaskBackend:
    """Get the configured task backend.

    Priority: Redis (if REDIS_URL set and ROLE != standalone) > Database > In-memory.
    """
    global _backend
    if _backend is None:
        from app.config import REDIS_URL, ROLE

        if REDIS_URL and ROLE != "standalone":
            try:
                from app.services.task_backend_redis import RedisTaskBackend

                _backend = RedisTaskBackend()
                return _backend
            except Exception as e:
                logger.warning(f"BACKEND Redis backend unavailable ({e}), trying database")

        try:
            from app.db.task_backend_db import DatabaseTaskBackend

            _backend = DatabaseTaskBackend()
            logger.info("BACKEND Using database task backend")
        except Exception as e:
            logger.warning(f"BACKEND DB backend unavailable ({e}), falling back to in-memory")
            _backend = InMemoryTaskBackend()
    return _backend


def set_task_backend(backend: TaskBackend) -> None:
    """Override the task backend (used in tests)."""
    global _backend
    _backend = backend


def get_backend_info() -> dict:
    """Get info about the active backend."""
    backend = get_task_backend()
    return {
        "type": type(backend).__name__,
        "task_count": backend.count(),
    }

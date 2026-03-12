"""Redis-backed task state backend for multi-server deployments."""

import json
import logging

from app.services.task_backend import TaskBackend

logger = logging.getLogger("subtitle-generator")

# Fields that cannot be serialized to JSON (thread objects, events, etc.)
_SKIP_FIELDS = {"pause_event", "transcription_profiler", "_subprocess", "_thread_id"}


def _serialize(data: dict) -> str:
    """Serialize task dict to JSON, skipping non-serializable fields."""
    clean = {k: v for k, v in data.items() if k not in _SKIP_FIELDS}
    return json.dumps(clean, default=str)


def _deserialize(raw: str) -> dict:
    return json.loads(raw)


class RedisTaskBackend(TaskBackend):
    """Task backend using Redis hashes for shared state across servers."""

    KEY_PREFIX = "task:"

    def __init__(self):
        from app.services.redis_client import get_sync_redis
        self._redis = get_sync_redis()
        logger.info("BACKEND Using Redis task backend")

    def _key(self, task_id: str) -> str:
        return f"{self.KEY_PREFIX}{task_id}"

    def get(self, task_id: str) -> dict | None:
        raw = self._redis.get(self._key(task_id))
        if raw is None:
            return None
        return _deserialize(raw)

    def set(self, task_id: str, data: dict) -> None:
        self._redis.set(self._key(task_id), _serialize(data), ex=86400 * 7)  # 7-day TTL

    def delete(self, task_id: str) -> None:
        self._redis.delete(self._key(task_id))

    def items(self) -> list[tuple[str, dict]]:
        result = []
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor, match=f"{self.KEY_PREFIX}*", count=100)
            for key in keys:
                raw = self._redis.get(key)
                if raw:
                    task_id = key[len(self.KEY_PREFIX):]
                    result.append((task_id, _deserialize(raw)))
            if cursor == 0:
                break
        return result

    def keys(self) -> list[str]:
        result = []
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor, match=f"{self.KEY_PREFIX}*", count=100)
            result.extend(k[len(self.KEY_PREFIX):] for k in keys)
            if cursor == 0:
                break
        return result

    def contains(self, task_id: str) -> bool:
        return self._redis.exists(self._key(task_id)) > 0

    def count(self) -> int:
        return len(self.keys())

    def update_field(self, task_id: str, field: str, value) -> None:
        """Update a single field in a task without reading the whole object."""
        data = self.get(task_id)
        if data:
            data[field] = value
            self.set(task_id, data)

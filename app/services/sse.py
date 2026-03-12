"""Server-Sent Events: thread-safe event emission.

In standalone mode, uses in-process queues.
In multi-server mode (REDIS_URL set), publishes to Redis Pub/Sub.
"""

import logging
import queue
import time

from app import state
from app.config import REDIS_URL

logger = logging.getLogger("subtitle-generator")


def create_event_queue(task_id: str, maxsize: int = 1000):
    """Create an SSE event queue for a task (standalone mode only)."""
    if not REDIS_URL:
        state.task_event_queues[task_id] = queue.Queue(maxsize=maxsize)


def emit_event(task_id: str, event_type: str, data: dict = None):
    """Thread-safe event emission to SSE queue and task state.

    In standalone mode: pushes to in-process queue.
    In multi-server mode: publishes to Redis Pub/Sub.
    """
    if data is None:
        data = {}

    # Always update local task state for polling fallback
    if task_id in state.tasks:
        for k, v in data.items():
            if k not in ("type", "timestamp"):
                state.tasks[task_id][k] = v

    if REDIS_URL:
        # Multi-server: publish via Redis Pub/Sub
        from app.services.pubsub import publish_event
        publish_event(task_id, event_type, data)

        # Also update Redis task backend
        try:
            from app.services.task_backend_redis import RedisTaskBackend
            backend = RedisTaskBackend()
            task_data = state.tasks.get(task_id)
            if task_data:
                backend.set(task_id, task_data)
        except Exception:
            pass
    else:
        # Standalone: use in-process queue
        q = state.task_event_queues.get(task_id)
        if q:
            event = {"type": event_type, "timestamp": time.time(), **data}
            try:
                q.put_nowait(event)
            except queue.Full:
                pass  # drop event if queue is full

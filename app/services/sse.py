"""Server-Sent Events: thread-safe event emission.

In standalone mode, uses in-process queues with multi-subscriber support.
In multi-server mode (REDIS_URL set), publishes to Redis Pub/Sub.
"""

import logging
import queue
import threading
import time

from app import state
from app.config import REDIS_URL

logger = logging.getLogger("subtitle-generator")

# Lock for managing subscriber lists
_subscribers_lock = threading.Lock()


def create_event_queue(task_id: str, maxsize: int = 1000):
    """Create an SSE subscriber list for a task (standalone mode only)."""
    if not REDIS_URL:
        with _subscribers_lock:
            if task_id not in state.task_event_queues:
                state.task_event_queues[task_id] = []


def subscribe(task_id: str, maxsize: int = 1000) -> queue.Queue:
    """Add a new subscriber queue for an SSE connection. Returns the queue."""
    q = queue.Queue(maxsize=maxsize)
    with _subscribers_lock:
        subs = state.task_event_queues.get(task_id)
        if subs is None:
            state.task_event_queues[task_id] = []
            subs = state.task_event_queues[task_id]
        subs.append(q)
    return q


def unsubscribe(task_id: str, q: queue.Queue):
    """Remove a subscriber queue when an SSE connection closes."""
    with _subscribers_lock:
        subs = state.task_event_queues.get(task_id)
        if subs and q in subs:
            subs.remove(q)


def emit_event(task_id: str, event_type: str, data: dict = None):
    """Thread-safe event emission to all SSE subscribers and task state.

    In standalone mode: broadcasts to all subscriber queues.
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
        # Standalone: broadcast to all subscriber queues
        event = {"type": event_type, "timestamp": time.time(), **data}
        with _subscribers_lock:
            subs = state.task_event_queues.get(task_id, [])
            for q in subs:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass  # drop event if queue is full

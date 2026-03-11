"""Server-Sent Events: thread-safe event emission."""

import logging
import queue
import time

from app import state

logger = logging.getLogger("subtitle-generator")


def create_event_queue(task_id: str, maxsize: int = 1000):
    """Create an SSE event queue for a task."""
    state.task_event_queues[task_id] = queue.Queue(maxsize=maxsize)


def emit_event(task_id: str, event_type: str, data: dict = None):
    """Thread-safe event emission to SSE queue and task state."""
    if data is None:
        data = {}
    q = state.task_event_queues.get(task_id)
    if q:
        event = {"type": event_type, "timestamp": time.time(), **data}
        try:
            q.put_nowait(event)
        except queue.Full:
            pass  # drop event if queue is full
    # Also update tasks dict for polling fallback
    if task_id in state.tasks:
        for k, v in data.items():
            if k not in ("type", "timestamp"):
                state.tasks[task_id][k] = v

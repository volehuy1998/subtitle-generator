"""Redis Pub/Sub abstraction for cross-server event delivery."""

import json
import logging
import time

logger = logging.getLogger("subtitle-generator")


def _channel_name(task_id: str) -> str:
    return f"events:{task_id}"


def publish_event(task_id: str, event_type: str, data: dict | None = None):
    """Publish an event to Redis Pub/Sub (sync, for use in worker threads)."""
    from app.services.redis_client import get_sync_redis

    if data is None:
        data = {}
    event = {"type": event_type, "timestamp": time.time(), **data}
    try:
        r = get_sync_redis()
        r.publish(_channel_name(task_id), json.dumps(event, default=str))
    except Exception as e:
        logger.warning(f"PUBSUB Failed to publish event for [{task_id[:8]}]: {e}")


async def subscribe_events(task_id: str):
    """Async generator that yields events from Redis Pub/Sub for a task.

    Yields dicts like {"type": "step_change", "status": "extracting", ...}.
    Terminates when a terminal event (done/error/cancelled) is received.
    """
    from app.services.redis_client import get_async_redis

    r = get_async_redis()
    pubsub = r.pubsub()
    channel = _channel_name(task_id)

    try:
        await pubsub.subscribe(channel)
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=2.0)
            if msg is not None and msg["type"] == "message":
                try:
                    event = json.loads(msg["data"])
                    yield event
                    etype = event.get("type", "")
                    if etype in ("done", "error", "cancelled", "embed_done", "embed_error"):
                        break
                except json.JSONDecodeError:
                    continue
            else:
                # No message within timeout — yield heartbeat
                yield {"type": "heartbeat"}
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

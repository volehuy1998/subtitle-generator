"""WebSocket endpoint for real-time task updates (replaces SSE for supported clients).

In standalone mode: reads from in-process queues.
In multi-server mode: subscribes to Redis Pub/Sub.
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import state
from app.config import REDIS_URL, SSE_HEARTBEAT_INTERVAL

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Progress"])

# Active WebSocket connections: task_id -> set of WebSocket
_connections: dict[str, set] = {}

_SKIP_FIELDS = ("pause_event", "transcription_profiler", "cancel_requested")


def _get_task_data(task_id: str) -> dict | None:
    """Get task data from local state or Redis backend."""
    if task_id in state.tasks:
        return state.tasks[task_id]
    if REDIS_URL:
        try:
            from app.services.task_backend import get_task_backend

            backend = get_task_backend()
            return backend.get(task_id)
        except Exception:
            pass
    return None


async def broadcast_to_task(task_id: str, event: dict):
    """Broadcast an event to all WebSocket connections for a task."""
    conns = _connections.get(task_id, set())
    dead = set()
    for ws in conns:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    conns -= dead


@router.websocket("/ws/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task progress."""
    await websocket.accept()

    if task_id not in _connections:
        _connections[task_id] = set()
    _connections[task_id].add(websocket)

    logger.debug(f"WS [{task_id[:8]}] Client connected ({len(_connections[task_id])} total)")

    try:
        # Send current state immediately
        task_data = _get_task_data(task_id)
        if task_data:
            data = {k: v for k, v in task_data.items() if k not in _SKIP_FIELDS}
            await websocket.send_json({"type": "state", **data})

            if data.get("status") in ("done", "error", "cancelled"):
                await websocket.close()
                return

        if REDIS_URL:
            # Multi-server: subscribe to Redis Pub/Sub
            from app.services.pubsub import subscribe_events

            async for event in subscribe_events(task_id):
                etype = event.get("type", "update")
                if etype == "heartbeat":
                    await websocket.send_json({"type": "heartbeat"})
                    continue
                await websocket.send_json(event)
                if etype in ("done", "error", "cancelled"):
                    break
        else:
            # Standalone: each WS connection gets its own subscriber queue
            from app.services.sse import subscribe, unsubscribe

            q = subscribe(task_id)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(
                            asyncio.to_thread(q.get, timeout=SSE_HEARTBEAT_INTERVAL),
                            timeout=SSE_HEARTBEAT_INTERVAL + 1,
                        )
                        await websocket.send_json(event)
                        if event.get("type") in ("done", "error", "cancelled"):
                            break
                    except asyncio.TimeoutError:
                        await websocket.send_json({"type": "heartbeat"})
                        status = state.tasks.get(task_id, {}).get("status")
                        if status in ("done", "error", "cancelled"):
                            data = {k: v for k, v in state.tasks.get(task_id, {}).items() if k not in _SKIP_FIELDS}
                            await websocket.send_json({"type": status, **data})
                            break
            finally:
                unsubscribe(task_id, q)

    except WebSocketDisconnect:
        logger.debug(f"WS [{task_id[:8]}] Client disconnected")
    except Exception as e:
        logger.warning(f"WS [{task_id[:8]}] Error: {e}")
    finally:
        _connections.get(task_id, set()).discard(websocket)
        if task_id in _connections and not _connections[task_id]:
            del _connections[task_id]

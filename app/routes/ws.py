"""WebSocket endpoint for real-time task updates (replaces SSE for supported clients)."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import state

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Progress"])

# Active WebSocket connections: task_id -> set of WebSocket
_connections: dict[str, set] = {}


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
        if task_id in state.tasks:
            data = {k: v for k, v in state.tasks[task_id].items()
                    if k not in ("pause_event", "transcription_profiler", "cancel_requested")}
            await websocket.send_json({"type": "state", **data})

            # If task is already terminal, close immediately
            if data.get("status") in ("done", "error", "cancelled"):
                await websocket.close()
                return

        # Poll for updates via the SSE queue (shared with SSE endpoint)
        q = state.task_event_queues.get(task_id)

        while True:
            try:
                if q:
                    event = await asyncio.wait_for(
                        asyncio.to_thread(q.get, timeout=1),
                        timeout=2,
                    )
                    await websocket.send_json(event)
                    if event.get("type") in ("done", "error", "cancelled"):
                        break
                else:
                    await asyncio.sleep(1)
                    # Check if task is done
                    status = state.tasks.get(task_id, {}).get("status")
                    if status in ("done", "error", "cancelled"):
                        data = {k: v for k, v in state.tasks.get(task_id, {}).items()
                                if k not in ("pause_event", "transcription_profiler", "cancel_requested")}
                        await websocket.send_json({"type": status, **data})
                        break

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                status = state.tasks.get(task_id, {}).get("status")
                if status in ("done", "error", "cancelled"):
                    data = {k: v for k, v in state.tasks.get(task_id, {}).items()
                            if k not in ("pause_event", "transcription_profiler", "cancel_requested")}
                    await websocket.send_json({"type": status, **data})
                    break

    except WebSocketDisconnect:
        logger.debug(f"WS [{task_id[:8]}] Client disconnected")
    except Exception as e:
        logger.warning(f"WS [{task_id[:8]}] Error: {e}")
    finally:
        _connections.get(task_id, set()).discard(websocket)
        if task_id in _connections and not _connections[task_id]:
            del _connections[task_id]

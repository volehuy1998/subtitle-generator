"""SSE and polling endpoints for real-time task updates.

In standalone mode: reads from in-process queues.
In multi-server mode: subscribes to Redis Pub/Sub.
"""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import TaskProgressResponse

from app import state
from app.config import REDIS_URL

router = APIRouter(tags=["Progress"])


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


def _filter_task(data: dict) -> dict:
    return {k: v for k, v in data.items()
            if k not in ("pause_event", "transcription_profiler")}


@router.get("/events/{task_id}")
async def task_events_sse(task_id: str):
    """Server-Sent Events endpoint for real-time task updates."""
    from app.services.sse import subscribe, unsubscribe

    has_subs = task_id in state.task_event_queues
    task_data = _get_task_data(task_id)
    if not has_subs and task_data is None:
        raise HTTPException(404, "Task not found")

    async def event_generator():
        # Send initial state
        data = _get_task_data(task_id)
        if data:
            yield f"event: state\ndata: {json.dumps(_filter_task(data), default=str)}\n\n"

        if REDIS_URL:
            # Multi-server: subscribe to Redis Pub/Sub
            from app.services.pubsub import subscribe_events
            async for event in subscribe_events(task_id):
                etype = event.get("type", "update")
                if etype == "heartbeat":
                    yield "event: heartbeat\ndata: {}\n\n"
                    continue
                yield f"event: {etype}\ndata: {json.dumps(event, default=str)}\n\n"
                if etype in ("done", "error", "cancelled", "embed_done", "embed_error"):
                    break
        else:
            # Standalone: each SSE connection gets its own subscriber queue
            q = subscribe(task_id)
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(
                            asyncio.to_thread(q.get, timeout=1),
                            timeout=2,
                        )
                        etype = event.get("type", "update")
                        yield f"event: {etype}\ndata: {json.dumps(event, default=str)}\n\n"
                        if etype in ("done", "error", "cancelled"):
                            task = state.tasks.get(task_id, {})
                            if not task.get("embed_in_progress"):
                                break
                        if etype in ("embed_done", "embed_error"):
                            break
                    except (asyncio.TimeoutError, Exception):
                        yield "event: heartbeat\ndata: {}\n\n"
                        task = state.tasks.get(task_id, {})
                        status = task.get("status")
                        if status in ("done", "error", "cancelled") and not task.get("embed_in_progress"):
                            data = _filter_task(task)
                            yield f"event: {status}\ndata: {json.dumps(data, default=str)}\n\n"
                            break
            finally:
                unsubscribe(task_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/progress/{task_id}", response_model=TaskProgressResponse)
async def progress(task_id: str):
    """Polling fallback for progress."""
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    return _filter_task(task_data)

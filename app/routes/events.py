"""SSE and polling endpoints for real-time task updates."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app import state

router = APIRouter(tags=["Progress"])


@router.get("/events/{task_id}")
async def task_events_sse(task_id: str):
    """Server-Sent Events endpoint for real-time task updates."""
    q = state.task_event_queues.get(task_id)
    if not q and task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    async def event_generator():
        if task_id in state.tasks:
            data = {k: v for k, v in state.tasks[task_id].items()
                    if k not in ("pause_event", "transcription_profiler")}
            yield f"event: state\ndata: {json.dumps(data, default=str)}\n\n"

        if not q:
            return

        while True:
            try:
                event = await asyncio.wait_for(
                    asyncio.to_thread(q.get, timeout=1),
                    timeout=2,
                )
                etype = event.get("type", "update")
                yield f"event: {etype}\ndata: {json.dumps(event, default=str)}\n\n"
                # Stop on terminal events, but NOT if embed is in progress
                if etype in ("done", "error", "cancelled"):
                    task = state.tasks.get(task_id, {})
                    if not task.get("embed_in_progress"):
                        break
                # Stop on embed terminal events
                if etype in ("embed_done", "embed_error"):
                    break
            except (asyncio.TimeoutError, Exception):
                yield f"event: heartbeat\ndata: {{}}\n\n"
                task = state.tasks.get(task_id, {})
                status = task.get("status")
                # Only close if terminal AND no embed running
                if status in ("done", "error", "cancelled") and not task.get("embed_in_progress"):
                    # Don't auto-close if client just reconnected for embed
                    data = {k: v for k, v in task.items()
                            if k not in ("pause_event", "transcription_profiler")}
                    yield f"event: {status}\ndata: {json.dumps(data, default=str)}\n\n"
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/progress/{task_id}")
async def progress(task_id: str):
    """Polling fallback for progress."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    data = {k: v for k, v in state.tasks[task_id].items()
            if k not in ("pause_event", "transcription_profiler")}
    return data

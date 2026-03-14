"""Task queue, history, retry, and management routes."""

import logging
import uuid

from fastapi import APIRouter, Request, Query, HTTPException

from app import state

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Tasks"])


def _estimate_queue_position(task_id: str) -> dict:
    """Estimate queue position and ETA for a task."""
    task = state.tasks.get(task_id)
    if not task:
        return {"position": -1, "estimated_wait_sec": 0}

    status = task.get("status", "unknown")
    if status != "queued":
        return {"position": 0, "estimated_wait_sec": 0}

    # Count tasks ahead in queue
    position = 0
    for tid, t in state.tasks.items():
        if tid == task_id:
            break
        if t.get("status") in ("queued", "extracting", "transcribing"):
            position += 1

    # Rough ETA: ~60 seconds per active task ahead
    estimated_wait = position * 60
    return {"position": position, "estimated_wait_sec": estimated_wait}


@router.get("/tasks")
async def list_tasks(request: Request, session_only: bool = Query(False)):
    """List tasks with queue position estimates. Use session_only=true for your tasks only."""
    session_id = getattr(request.state, "session_id", "") if session_only else ""
    result = []
    for tid, t in state.tasks.items():
        if session_only and t.get("session_id") != session_id:
            continue
        queue_info = _estimate_queue_position(tid) if t.get("status") == "queued" else {}
        result.append(
            {
                "task_id": tid,
                "status": t.get("status", "unknown"),
                "percent": t.get("percent", 0),
                "filename": t.get("filename", "unknown"),
                "message": t.get("message", ""),
                "model_size": t.get("model_size", ""),
                "device": t.get("device", ""),
                "language": t.get("language", ""),
                "segments": t.get("segments", 0),
                "created_at": t.get("created_at", ""),
                "own": t.get("session_id", "") == getattr(request.state, "session_id", ""),
                **queue_info,
            }
        )
    # Sort newest first, limit to last 100
    result.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    result = result[:100]
    return {"tasks": result}


@router.get("/tasks/{task_id}/position")
async def task_queue_position(task_id: str):
    """Get queue position and estimated wait time for a task."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    return _estimate_queue_position(task_id)


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed or cancelled task.

    Creates a new task with the same parameters. The original file must still be available
    or the user will need to re-upload.
    """
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[task_id]
    if task.get("status") not in ("error", "cancelled"):
        raise HTTPException(400, "Only failed or cancelled tasks can be retried")

    # Create a new retry task entry
    new_task_id = str(uuid.uuid4())
    state.tasks[new_task_id] = {
        "status": "retry_pending",
        "percent": 0,
        "message": f"Retry of {task_id[:8]}. Please re-upload the file.",
        "filename": task.get("filename", "unknown"),
        "language_requested": task.get("language_requested", "auto"),
        "retry_of": task_id,
        "session_id": task.get("session_id", ""),
    }

    logger.info(f"RETRY [{task_id[:8]}] -> [{new_task_id[:8]}]")
    return {
        "new_task_id": new_task_id,
        "message": "Retry registered. Please re-upload the file to start processing.",
        "original_task_id": task_id,
    }


@router.get("/tasks/duplicates")
async def check_duplicates(filename: str = Query(...), file_size: int = Query(0)):
    """Check if a file has already been processed (deduplication).

    Matches by filename and file_size. Returns matching tasks if found.
    """
    matches = []
    for tid, t in state.tasks.items():
        if (
            t.get("filename") == filename
            and t.get("status") == "done"
            and (file_size == 0 or t.get("file_size") == file_size)
        ):
            matches.append(
                {
                    "task_id": tid,
                    "filename": t.get("filename"),
                    "language": t.get("language", ""),
                    "segments": t.get("segments", 0),
                    "model_size": t.get("model_size", ""),
                }
            )

    return {
        "duplicates_found": len(matches) > 0,
        "matches": matches,
    }

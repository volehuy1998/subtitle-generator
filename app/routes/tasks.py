"""Task queue, history, retry, and management routes."""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from app import state
from app.config import OUTPUT_DIR, UPLOAD_DIR
from app.logging_setup import log_task_event
from app.utils.access import check_task_access

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


@router.get("/tasks/stats", tags=["Tasks"])
async def task_stats(request: Request):
    """Get aggregate task statistics for the current session."""
    session_id = getattr(request.state, "session_id", "")

    total = 0
    done = 0
    failed = 0
    cancelled = 0
    total_segments = 0
    total_duration_sec = 0.0
    models_used = {}

    for tid, t in state.tasks.items():
        if session_id and t.get("session_id") != session_id:
            continue
        total += 1
        status = t.get("status", "")
        if status == "done":
            done += 1
            total_segments += t.get("segments", 0)
            total_duration_sec += t.get("audio_duration", 0) or 0
            model = t.get("model_size", "unknown")
            models_used[model] = models_used.get(model, 0) + 1
        elif status == "error":
            failed += 1
        elif status == "cancelled":
            cancelled += 1

    return {
        "total_tasks": total,
        "completed": done,
        "failed": failed,
        "cancelled": cancelled,
        "active": total - done - failed - cancelled,
        "total_segments": total_segments,
        "total_audio_duration_sec": round(total_duration_sec, 1),
        "models_used": models_used,
    }


@router.put("/tasks/{task_id}/tags")
async def update_task_tags(task_id: str, request: Request):
    """Update tags/labels for a task."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    body = await request.json()
    tags = body.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 10:
        raise HTTPException(400, "Tags must be a list of up to 10 strings")
    tags = [str(t).strip()[:50] for t in tags if str(t).strip()]

    state.tasks[task_id]["tags"] = tags
    logger.info(f"TAGS [{task_id[:8]}] Updated tags: {tags}")
    log_task_event(task_id, "tags_updated", tags=tags)
    return {"task_id": task_id, "tags": tags}


@router.put("/tasks/{task_id}/note")
async def update_task_note(task_id: str, request: Request):
    """Attach or update a note on a task."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    body = await request.json()
    note = str(body.get("note", "")).strip()[:1000]  # Max 1000 chars

    state.tasks[task_id]["note"] = note
    logger.info(f"NOTE [{task_id[:8]}] Note {'set' if note else 'cleared'}")
    log_task_event(task_id, "note_updated", note_length=len(note))
    return {"task_id": task_id, "note": note}


# Terminal statuses — tasks that are no longer processing
_TERMINAL_STATUSES = frozenset({"done", "error", "cancelled"})


def _delete_task_files(task_id: str, task: dict) -> dict:
    """Delete all files associated with a task. Returns summary of deletions."""
    deleted = []
    errors = []

    # Collect candidate file paths: uploaded file, extracted audio, outputs
    candidates: list[Path] = []

    # Uploaded files: {task_id}.{ext} in UPLOAD_DIR
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if f.is_file() and f.stem == task_id:
                candidates.append(f)

    # Output files: {task_id}.{ext} in OUTPUT_DIR (srt, vtt, json, embedded video)
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            if f.is_file() and f.stem == task_id:
                candidates.append(f)

    for fpath in candidates:
        try:
            fpath.unlink()
            deleted.append(fpath.name)
            logger.debug(f"DELETE [{task_id[:8]}] Removed file: {fpath.name}")
        except Exception as e:
            errors.append({"file": fpath.name, "error": str(e)})
            logger.warning(f"DELETE [{task_id[:8]}] Failed to remove {fpath.name}: {e}")

    return {"deleted_files": deleted, "errors": errors}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, request: Request):
    """Delete a completed, failed, or cancelled task and its associated files.

    Only tasks in terminal state (done, error, cancelled) can be deleted.
    Active tasks must be cancelled first.
    """
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[task_id]

    # Session access check (same pattern as cancel endpoint)
    check_task_access(task, request)

    # Only allow deletion of terminal tasks
    status = task.get("status", "unknown")
    if status not in _TERMINAL_STATUSES:
        raise HTTPException(
            400,
            f"Cannot delete an active task (status: {status}). Cancel the task first.",
        )

    # Delete associated files
    file_summary = _delete_task_files(task_id, task)

    # Remove from in-memory state
    state.tasks.pop(task_id, None)

    # Remove from database backend
    try:
        from app.services.task_backend import get_task_backend

        backend = get_task_backend()
        backend.delete(task_id)
    except Exception as e:
        logger.warning(f"DELETE [{task_id[:8]}] Backend delete failed: {e}")

    # Persist updated task history
    state.save_task_history()

    logger.info(
        f"DELETE [{task_id[:8]}] Task deleted (was: {status}, files_removed: {len(file_summary['deleted_files'])})"
    )
    log_task_event(
        task_id,
        "deleted",
        previous_status=status,
        deleted_files=file_summary["deleted_files"],
        file_errors=file_summary["errors"],
    )

    return {
        "message": "Task deleted",
        "task_id": task_id,
        "deleted_files": file_summary["deleted_files"],
    }

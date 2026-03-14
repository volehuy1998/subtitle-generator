"""Task control routes: cancel, pause, resume."""

import ctypes
import logging

from fastapi import APIRouter, HTTPException, Request

from app import state
from app.logging_setup import log_task_event
from app.utils.access import check_task_access

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Progress"])


@router.post("/cancel/{task_id}")
async def cancel(task_id: str, request: Request):
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    task = state.tasks[task_id]
    check_task_access(task, request)
    if task["status"] in ("done", "error", "cancelled"):
        raise HTTPException(400, "Task already finished")
    if task.get("cancel_requested"):
        return {"message": "Cancel already requested"}
    logger.info(f"CANCEL [{task_id[:8]}] Cancel requested (status={task['status']})")
    log_task_event(task_id, "cancel_requested", status=task["status"])
    task["cancel_requested"] = True
    # Unblock paused tasks so they can see the cancel
    pause_event = task.get("pause_event")
    if pause_event:
        pause_event.set()
    # Kill running subprocess (ffmpeg) immediately
    proc = task.get("_subprocess")
    if proc is not None:
        try:
            proc.kill()
            logger.info(f"CANCEL [{task_id[:8]}] Killed subprocess PID {proc.pid}")
        except (OSError, ProcessLookupError):
            pass
    # Inject CancelledError into pipeline thread for immediate stop
    thread_id = task.get("_thread_id")
    if thread_id is not None:
        try:
            from app.exceptions import CancelledError

            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(thread_id),
                ctypes.py_object(CancelledError),
            )
            if res == 1:
                logger.info(f"CANCEL [{task_id[:8]}] Injected abort into thread {thread_id}")
            elif res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread_id), None)
        except Exception as e:
            logger.error(f"CANCEL [{task_id[:8]}] Thread injection failed: {e}")
    return {"message": "Cancel requested"}


@router.post("/pause/{task_id}")
async def pause(task_id: str, request: Request):
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    task = state.tasks[task_id]
    check_task_access(task, request)
    if task["status"] not in ("transcribing",):
        # Already paused or not in a pausable state
        if task["status"] == "paused":
            return {"message": "Already paused"}
        raise HTTPException(400, "Can only pause during transcription")
    pause_event = task.get("pause_event")
    if pause_event and not pause_event.is_set():
        return {"message": "Already pausing"}
    logger.info(f"PAUSE [{task_id[:8]}] Pause requested (will take effect at next segment boundary)")
    log_task_event(task_id, "paused")
    if pause_event:
        pause_event.clear()
    return {"message": "Pause requested — will pause after current segment"}


@router.post("/resume/{task_id}")
async def resume(task_id: str, request: Request):
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    check_task_access(state.tasks[task_id], request)
    logger.info(f"RESUME [{task_id[:8]}] Resumed")
    log_task_event(task_id, "resumed")
    pause_event = state.tasks[task_id].get("pause_event")
    if pause_event:
        pause_event.set()
    return {"message": "Resumed"}

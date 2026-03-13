"""Global in-process state. Single source of truth for mutable shared data."""

import ctypes
import json
import logging
import queue
import threading
import time

from app.config import TASK_HISTORY_FILE, MAX_TASK_HISTORY

logger = logging.getLogger("subtitle-generator")

# Task status/progress store: task_id -> {status, percent, message, ...}
tasks: dict[str, dict] = {}

# Cached WhisperModel instances: (model_size, device) -> WhisperModel
loaded_models: dict[tuple[str, str], object] = {}
model_lock = threading.Lock()

# Cached argos-translate models: (source_lang, target_lang) -> translation object
translation_models: dict[tuple[str, str], object] = {}
translation_model_lock = threading.Lock()

# SSE event queues: task_id -> Queue
task_event_queues: dict[str, queue.Queue] = {}

# Semaphore to limit concurrent transcription tasks
_task_semaphore: threading.Semaphore | None = None

# Shutdown flag - when True, no new tasks accepted
shutting_down: bool = False

# Critical state - when True, ALL user-facing operations are blocked.
# Only health/monitoring endpoints remain accessible.
system_critical: bool = False
system_critical_reasons: list[str] = []

# Main asyncio event loop reference (set during startup for thread-safe scheduling)
main_event_loop: object | None = None


def set_critical(reasons: list[str]):
    """Activate critical state with one or more reasons.

    When transitioning from healthy → critical, force-aborts ALL active tasks:
    sets cancel_requested, unblocks paused tasks, and emits critical_abort SSE events.
    """
    global system_critical, system_critical_reasons
    was_critical = system_critical
    system_critical = bool(reasons)
    system_critical_reasons = reasons

    # On transition to critical: force-abort every active task
    if not was_critical and system_critical:
        logger.error(f"CRITICAL System entering critical state: {'; '.join(reasons)}")
        _force_abort_active_tasks(reasons)


def _force_abort_active_tasks(reasons: list[str]):
    """Force-abort all in-flight tasks when entering critical state.

    - Sets cancel_requested so pipeline/transcription loops will stop
    - Unblocks any paused tasks (sets pause_event) so they can see the cancel
    - Kills any running subprocess (ffmpeg extract/embed) immediately
    - Emits critical_abort SSE event so the frontend knows immediately
    """
    reason_text = "; ".join(reasons) if reasons else "Unknown"
    aborted = 0
    killed_procs = 0
    killed_threads = 0
    for task_id, task in tasks.items():
        status = task.get("status", "")
        if status in ("done", "error", "cancelled"):
            continue

        # Force cancel
        task["cancel_requested"] = True

        # Unblock paused tasks so they can exit
        pause_event = task.get("pause_event")
        if pause_event:
            pause_event.set()

        # Kill running subprocess (ffmpeg) immediately
        proc = task.get("_subprocess")
        if proc is not None:
            try:
                proc.kill()
                killed_procs += 1
                logger.warning(f"CRITICAL Killed subprocess PID {proc.pid} for task [{task_id[:8]}]")
            except (OSError, ProcessLookupError):
                pass  # Already dead

        # Inject CriticalAbortError into pipeline thread
        # This forces the thread to abort at the next Python bytecode instruction,
        # even if it's blocked in model loading or between C extension calls.
        thread_id = task.get("_thread_id")
        if thread_id is not None:
            try:
                from app.exceptions import CriticalAbortError
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulong(thread_id),
                    ctypes.py_object(CriticalAbortError),
                )
                if res == 1:
                    killed_threads += 1
                    logger.warning(f"CRITICAL Injected abort into thread {thread_id} for task [{task_id[:8]}]")
                elif res > 1:
                    # Reset if more than one thread affected (shouldn't happen)
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread_id), None)
                    logger.error(f"CRITICAL Thread abort affected multiple threads for [{task_id[:8]}], reset")
            except Exception as e:
                logger.error(f"CRITICAL Failed to inject abort into thread for [{task_id[:8]}]: {e}")

        # Emit SSE event for this task
        from app.services.sse import emit_event
        emit_event(task_id, "critical_abort", {
            "status": "error",
            "message": f"System critical — all operations halted: {reason_text}",
            "reasons": reasons,
        })

        aborted += 1

    if aborted:
        msg = f"CRITICAL Force-aborted {aborted} active task(s)"
        if killed_procs:
            msg += f", killed {killed_procs} subprocess(es)"
        if killed_threads:
            msg += f", injected abort into {killed_threads} thread(s)"
        logger.warning(msg)


def clear_critical():
    """Deactivate critical state (all checks passed)."""
    global system_critical, system_critical_reasons
    if system_critical:
        logger.info("CRITICAL System recovered — leaving critical state")
    system_critical = False
    system_critical_reasons = []


def get_task_semaphore(max_tasks: int = 3) -> threading.Semaphore:
    global _task_semaphore
    if _task_semaphore is None:
        _task_semaphore = threading.Semaphore(max_tasks)
    return _task_semaphore


def get_active_task_count() -> int:
    """Count currently processing tasks."""
    return sum(1 for t in tasks.values()
               if t.get("status") not in ("done", "error", "cancelled", "queued"))


def drain_tasks(timeout: float = 60.0) -> bool:
    """Wait for all in-flight tasks to complete. Returns True if all drained."""
    start = time.time()
    while time.time() - start < timeout:
        active = get_active_task_count()
        if active == 0:
            return True
        logger.info(f"SHUTDOWN Draining: {active} task(s) still in progress...")
        time.sleep(2)
    remaining = get_active_task_count()
    if remaining > 0:
        logger.warning(f"SHUTDOWN Timeout: {remaining} task(s) still running after {timeout}s")
    return remaining == 0


# Fields safe to persist (no threads, events, profiler objects)
_PERSIST_FIELDS = {
    "status", "percent", "message", "filename", "duration", "file_size",
    "file_size_fmt", "audio_size_fmt", "segments", "language",
    "language_requested", "device", "model_size",
    "word_timestamps", "diarize", "speakers", "session_id", "created_at",
}


def save_task_history():
    """Persist completed/failed tasks to disk (last N tasks)."""
    try:
        persistable = {}
        for tid, t in tasks.items():
            if t.get("status") in ("done", "error", "cancelled"):
                persistable[tid] = {k: v for k, v in t.items() if k in _PERSIST_FIELDS}

        # Keep only last MAX_TASK_HISTORY entries
        items = list(persistable.items())[-MAX_TASK_HISTORY:]
        TASK_HISTORY_FILE.write_text(
            json.dumps(dict(items), indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Failed to save task history: {e}")


def load_task_history():
    """Load task history from disk on startup."""
    if not TASK_HISTORY_FILE.exists():
        return
    try:
        data = json.loads(TASK_HISTORY_FILE.read_text(encoding="utf-8"))
        for tid, t in data.items():
            if tid not in tasks:
                tasks[tid] = t
        logger.info(f"Loaded {len(data)} tasks from history")
    except Exception as e:
        logger.error(f"Failed to load task history: {e}")

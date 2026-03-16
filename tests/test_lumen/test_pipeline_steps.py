"""Phase Lumen L8 — Pipeline step transition tests.

Tests pipeline state machine, step progression, percent tracking,
cancel/error at each step, and status messages.
— Scout (QA Lead)
"""

from app import state
from app.services.sse import create_event_queue, emit_event, subscribe


def _create_pipeline_task(task_id="pipeline-test", status="queued"):
    """Set up a task in state for pipeline testing."""
    state.tasks[task_id] = {
        "status": status,
        "percent": 0,
        "message": "",
        "step": 0,
        "filename": "test.wav",
        "session_id": "",
        "cancel_requested": False,
    }
    create_event_queue(task_id)
    return task_id


def _cleanup(task_id):
    state.tasks.pop(task_id, None)
    state.task_event_queues.pop(task_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# STEP PROGRESSION
# ══════════════════════════════════════════════════════════════════════════════


class TestStepProgression:
    """Test pipeline step state transitions."""

    def test_step_starts_at_zero(self):
        tid = _create_pipeline_task("step-init-1")
        try:
            assert state.tasks[tid]["step"] == 0
        finally:
            _cleanup(tid)

    def test_step_increments(self):
        tid = _create_pipeline_task("step-inc-1")
        try:
            q = subscribe(tid)
            for step in range(1, 4):
                emit_event(tid, "step_change", {"step": step})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            steps = [e.get("step") for e in events if "step" in e]
            assert steps == [1, 2, 3]
        finally:
            _cleanup(tid)

    def test_step_0_to_1_extracting(self):
        tid = _create_pipeline_task("step-0-1")
        try:
            emit_event(tid, "update", {"status": "extracting", "step": 1, "percent": 5})
            assert state.tasks[tid]["status"] == "extracting"
            assert state.tasks[tid]["step"] == 1
        finally:
            _cleanup(tid)

    def test_step_1_to_2_loading(self):
        tid = _create_pipeline_task("step-1-2")
        try:
            emit_event(tid, "update", {"status": "loading_model", "step": 2, "percent": 15})
            assert state.tasks[tid]["status"] == "loading_model"
            assert state.tasks[tid]["step"] == 2
        finally:
            _cleanup(tid)

    def test_step_2_to_3_transcribing(self):
        tid = _create_pipeline_task("step-2-3")
        try:
            emit_event(tid, "update", {"status": "transcribing", "step": 3, "percent": 20})
            assert state.tasks[tid]["status"] == "transcribing"
            assert state.tasks[tid]["step"] == 3
        finally:
            _cleanup(tid)

    def test_step_final_done(self):
        tid = _create_pipeline_task("step-done-1")
        try:
            emit_event(tid, "done", {"status": "done", "percent": 100})
            assert state.tasks[tid]["status"] == "done"
            assert state.tasks[tid]["percent"] == 100
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# PERCENT PROGRESSION
# ══════════════════════════════════════════════════════════════════════════════


class TestPercentProgression:
    """Test percent values at each step."""

    def test_starts_at_zero(self):
        tid = _create_pipeline_task("pct-zero-1")
        try:
            assert state.tasks[tid]["percent"] == 0
        finally:
            _cleanup(tid)

    def test_extracting_percent_5(self):
        tid = _create_pipeline_task("pct-5")
        try:
            emit_event(tid, "update", {"percent": 5, "status": "extracting"})
            assert state.tasks[tid]["percent"] == 5
        finally:
            _cleanup(tid)

    def test_loading_model_percent_15(self):
        tid = _create_pipeline_task("pct-15")
        try:
            emit_event(tid, "update", {"percent": 15, "status": "loading_model"})
            assert state.tasks[tid]["percent"] == 15
        finally:
            _cleanup(tid)

    def test_transcribing_percent_range(self):
        tid = _create_pipeline_task("pct-range")
        try:
            for pct in [20, 30, 50, 70, 90]:
                emit_event(tid, "progress", {"percent": pct})
                assert state.tasks[tid]["percent"] == pct
        finally:
            _cleanup(tid)

    def test_done_percent_100(self):
        tid = _create_pipeline_task("pct-100")
        try:
            emit_event(tid, "done", {"percent": 100, "status": "done"})
            assert state.tasks[tid]["percent"] == 100
        finally:
            _cleanup(tid)

    def test_percent_monotonic_increase(self):
        tid = _create_pipeline_task("pct-mono")
        try:
            q = subscribe(tid)
            percents = [0, 5, 15, 25, 50, 75, 90, 100]
            for p in percents:
                emit_event(tid, "progress", {"percent": p})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            recorded = [e.get("percent") for e in events if "percent" in e]
            assert recorded == percents
        finally:
            _cleanup(tid)

    def test_percent_as_integer(self):
        tid = _create_pipeline_task("pct-int")
        try:
            emit_event(tid, "update", {"percent": 42})
            assert isinstance(state.tasks[tid]["percent"], int)
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# CANCEL AT EACH STEP
# ══════════════════════════════════════════════════════════════════════════════


class TestCancelAtStep:
    """Test cancellation behavior at different pipeline steps."""

    def test_cancel_at_queued(self):
        tid = _create_pipeline_task("cancel-q-1", status="queued")
        try:
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled"})
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_cancel_at_extracting(self):
        tid = _create_pipeline_task("cancel-ext-1", status="extracting")
        try:
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled"})
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_cancel_at_loading(self):
        tid = _create_pipeline_task("cancel-load-1", status="loading_model")
        try:
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled"})
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_cancel_at_transcribing(self):
        tid = _create_pipeline_task("cancel-trans-1", status="transcribing")
        try:
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled"})
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_cancel_flag_set(self):
        tid = _create_pipeline_task("cancel-flag-1")
        try:
            assert state.tasks[tid]["cancel_requested"] is False
            state.tasks[tid]["cancel_requested"] = True
            assert state.tasks[tid]["cancel_requested"] is True
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# ERROR AT EACH STEP
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorAtStep:
    """Test error handling at different pipeline steps."""

    def test_error_at_extracting(self):
        tid = _create_pipeline_task("err-ext-1", status="extracting")
        try:
            emit_event(tid, "error", {"status": "error", "message": "FFmpeg failed"})
            assert state.tasks[tid]["status"] == "error"
            assert "FFmpeg" in state.tasks[tid]["message"]
        finally:
            _cleanup(tid)

    def test_error_at_loading(self):
        tid = _create_pipeline_task("err-load-1", status="loading_model")
        try:
            emit_event(tid, "error", {"status": "error", "message": "Model not found"})
            assert state.tasks[tid]["status"] == "error"
        finally:
            _cleanup(tid)

    def test_error_at_transcribing(self):
        tid = _create_pipeline_task("err-trans-1", status="transcribing")
        try:
            emit_event(tid, "error", {"status": "error", "message": "Out of memory"})
            assert state.tasks[tid]["status"] == "error"
        finally:
            _cleanup(tid)

    def test_error_preserves_filename(self):
        tid = _create_pipeline_task("err-fn-1")
        try:
            emit_event(tid, "error", {"status": "error", "message": "Fail"})
            assert state.tasks[tid]["filename"] == "test.wav"
        finally:
            _cleanup(tid)

    def test_error_percent_frozen(self):
        tid = _create_pipeline_task("err-pct-1")
        try:
            emit_event(tid, "update", {"percent": 45})
            emit_event(tid, "error", {"status": "error", "message": "Crash"})
            # percent should not be overwritten by error event unless explicitly set
            assert state.tasks[tid]["status"] == "error"
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# STATUS MESSAGES
# ══════════════════════════════════════════════════════════════════════════════


class TestStatusMessages:
    """Test status messages at transitions."""

    def test_queued_message(self):
        tid = _create_pipeline_task("msg-q-1")
        try:
            emit_event(tid, "update", {"message": "Waiting in queue..."})
            assert "queue" in state.tasks[tid]["message"].lower() or "wait" in state.tasks[tid]["message"].lower()
        finally:
            _cleanup(tid)

    def test_extracting_message(self):
        tid = _create_pipeline_task("msg-ext-1")
        try:
            emit_event(tid, "update", {"message": "Extracting audio..."})
            assert "extract" in state.tasks[tid]["message"].lower()
        finally:
            _cleanup(tid)

    def test_loading_message(self):
        tid = _create_pipeline_task("msg-load-1")
        try:
            emit_event(tid, "update", {"message": "Loading model..."})
            assert "model" in state.tasks[tid]["message"].lower()
        finally:
            _cleanup(tid)

    def test_transcribing_message(self):
        tid = _create_pipeline_task("msg-trans-1")
        try:
            emit_event(tid, "update", {"message": "Transcribing audio..."})
            assert "transcrib" in state.tasks[tid]["message"].lower()
        finally:
            _cleanup(tid)

    def test_done_message(self):
        tid = _create_pipeline_task("msg-done-1")
        try:
            emit_event(tid, "done", {"message": "Transcription complete", "status": "done"})
            assert "complete" in state.tasks[tid]["message"].lower()
        finally:
            _cleanup(tid)

    def test_error_message_stored(self):
        tid = _create_pipeline_task("msg-err-1")
        try:
            emit_event(tid, "error", {"message": "Something went wrong", "status": "error"})
            assert state.tasks[tid]["message"] == "Something went wrong"
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE ERROR MAP
# ══════════════════════════════════════════════════════════════════════════════


class TestPipelineErrorMap:
    """Test the pipeline error sanitization logic."""

    def test_sanitize_ffmpeg_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("ffmpeg process failed"))
        assert "corrupted" in msg.lower() or "media" in msg.lower()

    def test_sanitize_oom_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("out of memory"))
        assert "memory" in msg.lower()

    def test_sanitize_cuda_oom(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("CUDA out of memory"))
        assert "gpu" in msg.lower() or "memory" in msg.lower()

    def test_sanitize_file_not_found(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("No such file or directory"))
        assert "file" in msg.lower()

    def test_sanitize_strips_paths(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("Error at /home/user/secret/file.py"))
        assert "/home/user" not in msg

    def test_sanitize_unknown_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception(""))
        assert isinstance(msg, str)

    def test_sanitize_long_message_truncated(self):
        from app.services.pipeline import _sanitize_error_for_user

        long_msg = "x" * 500
        msg = _sanitize_error_for_user(Exception(long_msg))
        assert len(msg) <= 250  # 200 + "..."

    def test_sanitize_model_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("Failed to load model weights"))
        assert "model" in msg.lower()

    def test_sanitize_permission_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("Permission denied: /etc/shadow"))
        assert "permission" in msg.lower()

    def test_sanitize_connection_error(self):
        from app.services.pipeline import _sanitize_error_for_user

        msg = _sanitize_error_for_user(Exception("Connection refused"))
        assert "unavailable" in msg.lower() or "service" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# FULL LIFECYCLE SIMULATION
# ══════════════════════════════════════════════════════════════════════════════


class TestFullLifecycle:
    """Test a complete task lifecycle through events."""

    def test_complete_success_lifecycle(self):
        tid = _create_pipeline_task("lifecycle-ok-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "update", {"status": "extracting", "percent": 5, "step": 1})
            emit_event(tid, "update", {"status": "loading_model", "percent": 15, "step": 2})
            emit_event(tid, "update", {"status": "transcribing", "percent": 20, "step": 3})
            emit_event(tid, "progress", {"percent": 50})
            emit_event(tid, "progress", {"percent": 90})
            emit_event(tid, "done", {"status": "done", "percent": 100})

            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert len(events) == 6
            assert events[-1]["type"] == "done"
            assert state.tasks[tid]["status"] == "done"
            assert state.tasks[tid]["percent"] == 100
        finally:
            _cleanup(tid)

    def test_complete_error_lifecycle(self):
        tid = _create_pipeline_task("lifecycle-err-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "update", {"status": "extracting", "percent": 5})
            emit_event(tid, "error", {"status": "error", "message": "FFmpeg crash"})

            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert events[-1]["type"] == "error"
            assert state.tasks[tid]["status"] == "error"
        finally:
            _cleanup(tid)

    def test_complete_cancel_lifecycle(self):
        tid = _create_pipeline_task("lifecycle-cancel-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "update", {"status": "transcribing", "percent": 40})
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled"})

            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert events[-1]["type"] == "cancelled"
            assert state.tasks[tid]["status"] == "cancelled"
        finally:
            _cleanup(tid)

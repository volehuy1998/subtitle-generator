"""Phase Lumen L8 — Task management tests.

Tests task CRUD: listing, progress, cancel, retry, delete,
queue position, duplicate detection, and session access.
— Scout (QA Lead)
"""

import struct
import uuid
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def _add_task(task_id=None, status="done", **kwargs):
    """Add a task to state. Returns task_id."""
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test.wav",
        "session_id": "",
        "language_requested": "auto",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    task.update(kwargs)
    state.tasks[tid] = task
    return tid


def _cleanup(*task_ids):
    for tid in task_ids:
        state.tasks.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# LIST TASKS
# ══════════════════════════════════════════════════════════════════════════════


class TestListTasks:
    """Test GET /tasks endpoint."""

    def test_list_tasks_returns_200(self):
        res = client.get("/tasks")
        assert res.status_code == 200

    def test_list_tasks_has_tasks_key(self):
        res = client.get("/tasks")
        assert "tasks" in res.json()

    def test_list_tasks_returns_array(self):
        res = client.get("/tasks")
        assert isinstance(res.json()["tasks"], list)

    def test_list_tasks_includes_added_task(self):
        tid = _add_task(status="done")
        try:
            res = client.get("/tasks")
            task_ids = [t["task_id"] for t in res.json()["tasks"]]
            assert tid in task_ids
        finally:
            _cleanup(tid)

    def test_list_tasks_fields(self):
        tid = _add_task(status="done", filename="hello.wav")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            task = next(t for t in tasks if t["task_id"] == tid)
            assert "status" in task
            assert "percent" in task
            assert "filename" in task
            assert task["filename"] == "hello.wav"
        finally:
            _cleanup(tid)

    def test_list_tasks_max_100(self):
        tids = [_add_task() for _ in range(110)]
        try:
            res = client.get("/tasks")
            assert len(res.json()["tasks"]) <= 100
        finally:
            for t in tids:
                _cleanup(t)

    def test_list_tasks_newest_first(self):
        t1 = _add_task(created_at="2026-01-01T00:00:00+00:00")
        t2 = _add_task(created_at="2026-01-02T00:00:00+00:00")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            ids = [t["task_id"] for t in tasks]
            if t1 in ids and t2 in ids:
                assert ids.index(t2) < ids.index(t1)
        finally:
            _cleanup(t1, t2)

    def test_list_tasks_session_only_param(self):
        res = client.get("/tasks?session_only=true")
        assert res.status_code == 200

    def test_list_empty_when_no_tasks(self):
        original = dict(state.tasks)
        state.tasks.clear()
        try:
            res = client.get("/tasks")
            assert res.json()["tasks"] == []
        finally:
            state.tasks.update(original)


# ══════════════════════════════════════════════════════════════════════════════
# PROGRESS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestProgressEndpoint:
    """Test GET /progress/{task_id}."""

    def test_progress_valid_task(self):
        tid = _add_task(status="transcribing", percent=42)
        try:
            res = client.get(f"/progress/{tid}")
            assert res.status_code == 200
            assert res.json()["percent"] == 42
        finally:
            _cleanup(tid)

    def test_progress_invalid_task(self):
        res = client.get("/progress/nonexistent-task")
        assert res.status_code == 404

    def test_progress_completed_task(self):
        tid = _add_task(status="done", percent=100)
        try:
            res = client.get(f"/progress/{tid}")
            assert res.status_code == 200
            assert res.json()["status"] == "done"
        finally:
            _cleanup(tid)

    def test_progress_error_task(self):
        tid = _add_task(status="error", message="Failed")
        try:
            res = client.get(f"/progress/{tid}")
            assert res.status_code == 200
            assert res.json()["status"] == "error"
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# CANCEL ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestCancelEndpoint:
    """Test POST /cancel/{task_id}."""

    def test_cancel_active_task(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 200
            assert state.tasks[tid].get("cancel_requested") is True
        finally:
            _cleanup(tid)

    def test_cancel_done_task_fails(self):
        tid = _add_task(status="done")
        try:
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_cancel_error_task_fails(self):
        tid = _add_task(status="error")
        try:
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_cancel_cancelled_task_fails(self):
        tid = _add_task(status="cancelled")
        try:
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_cancel_invalid_task(self):
        res = client.post("/cancel/nonexistent-task")
        assert res.status_code == 404

    def test_cancel_queued_task(self):
        tid = _add_task(status="queued")
        try:
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_double_cancel_idempotent(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(f"/cancel/{tid}")
            res = client.post(f"/cancel/{tid}")
            assert res.status_code == 200
            assert "already" in res.json()["message"].lower()
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# RETRY ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestRetryEndpoint:
    """Test POST /tasks/{task_id}/retry."""

    def test_retry_failed_task(self):
        tid = _add_task(status="error")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            assert res.status_code == 200
            data = res.json()
            assert "new_task_id" in data
            new_tid = data["new_task_id"]
            assert new_tid in state.tasks
            _cleanup(new_tid)
        finally:
            _cleanup(tid)

    def test_retry_cancelled_task(self):
        tid = _add_task(status="cancelled")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            assert res.status_code == 200
            new_tid = res.json()["new_task_id"]
            _cleanup(new_tid)
        finally:
            _cleanup(tid)

    def test_retry_done_task_fails(self):
        tid = _add_task(status="done")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_retry_active_task_fails(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_retry_nonexistent_task(self):
        res = client.post("/tasks/nonexistent-task/retry")
        assert res.status_code == 404

    def test_retry_creates_new_task(self):
        tid = _add_task(status="error", filename="original.wav")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            new_tid = res.json()["new_task_id"]
            assert state.tasks[new_tid]["filename"] == "original.wav"
            assert state.tasks[new_tid]["status"] == "retry_pending"
            _cleanup(new_tid)
        finally:
            _cleanup(tid)

    def test_retry_preserves_original_reference(self):
        tid = _add_task(status="error")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            new_tid = res.json()["new_task_id"]
            assert state.tasks[new_tid].get("retry_of") == tid
            _cleanup(new_tid)
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# DELETE ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteTask:
    """Test DELETE /tasks/{task_id} endpoint."""

    def test_delete_done_task_returns_200(self):
        tid = _add_task(status="done")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 200
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)

    def test_delete_error_task_returns_200(self):
        tid = _add_task(status="error")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_delete_cancelled_task_returns_200(self):
        tid = _add_task(status="cancelled")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_delete_removes_from_state(self):
        tid = _add_task(status="done")
        client.delete(f"/tasks/{tid}")
        assert tid not in state.tasks

    def test_delete_nonexistent_returns_404(self):
        res = client.delete("/tasks/nonexistent-id")
        assert res.status_code == 404

    def test_delete_active_task_returns_400(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 400
            assert "Cancel" in res.json()["detail"] or "active" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_delete_queued_task_returns_400(self):
        tid = _add_task(status="queued")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_delete_extracting_task_returns_400(self):
        tid = _add_task(status="extracting")
        try:
            res = client.delete(f"/tasks/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_delete_response_has_message(self):
        tid = _add_task(status="done")
        res = client.delete(f"/tasks/{tid}")
        data = res.json()
        assert "message" in data
        assert data["message"] == "Task deleted"

    def test_delete_response_has_deleted_files(self):
        tid = _add_task(status="done")
        res = client.delete(f"/tasks/{tid}")
        data = res.json()
        assert "deleted_files" in data
        assert isinstance(data["deleted_files"], list)

    def test_delete_twice_returns_404(self):
        tid = _add_task(status="done")
        res1 = client.delete(f"/tasks/{tid}")
        assert res1.status_code == 200
        res2 = client.delete(f"/tasks/{tid}")
        assert res2.status_code == 404


class TestTaskStateManagement:
    """Test task state management."""

    def test_task_has_status_field(self):
        tid = _add_task(status="done")
        try:
            assert state.tasks[tid]["status"] == "done"
        finally:
            _cleanup(tid)

    def test_task_has_percent_field(self):
        tid = _add_task(status="done", percent=100)
        try:
            assert state.tasks[tid]["percent"] == 100
        finally:
            _cleanup(tid)

    def test_task_has_filename_field(self):
        tid = _add_task(status="done", filename="test.wav")
        try:
            assert state.tasks[tid]["filename"] == "test.wav"
        finally:
            _cleanup(tid)

    def test_task_has_session_id(self):
        tid = _add_task(status="done", session_id="abc123")
        try:
            assert state.tasks[tid]["session_id"] == "abc123"
        finally:
            _cleanup(tid)

    def test_task_has_created_at(self):
        tid = _add_task(status="done")
        try:
            assert "created_at" in state.tasks[tid]
        finally:
            _cleanup(tid)

    def test_multiple_tasks_independent(self):
        t1 = _add_task(status="done", filename="a.wav")
        t2 = _add_task(status="error", filename="b.wav")
        try:
            assert state.tasks[t1]["filename"] == "a.wav"
            assert state.tasks[t2]["filename"] == "b.wav"
            assert state.tasks[t1]["status"] != state.tasks[t2]["status"]
        finally:
            _cleanup(t1, t2)

    def test_task_removal_from_state(self):
        tid = _add_task(status="done")
        state.tasks.pop(tid, None)
        assert tid not in state.tasks


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE POSITION
# ══════════════════════════════════════════════════════════════════════════════


class TestQueuePosition:
    """Test GET /tasks/{task_id}/position."""

    def test_queue_position_for_queued_task(self):
        tid = _add_task(status="queued")
        try:
            res = client.get(f"/tasks/{tid}/position")
            assert res.status_code == 200
            data = res.json()
            assert "position" in data
            assert "estimated_wait_sec" in data
        finally:
            _cleanup(tid)

    def test_queue_position_for_active_task(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.get(f"/tasks/{tid}/position")
            assert res.status_code == 200
            assert res.json()["position"] == 0
        finally:
            _cleanup(tid)

    def test_queue_position_nonexistent(self):
        res = client.get("/tasks/nonexistent/position")
        assert res.status_code == 404

    def test_queue_position_done_is_zero(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/tasks/{tid}/position")
            assert res.json()["position"] == 0
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# DUPLICATE DETECTION
# ══════════════════════════════════════════════════════════════════════════════


class TestDuplicateDetection:
    """Test GET /tasks/duplicates."""

    def test_no_duplicates(self):
        res = client.get("/tasks/duplicates?filename=unique_file.wav")
        assert res.status_code == 200
        assert res.json()["duplicates_found"] is False

    def test_duplicate_found(self):
        tid = _add_task(status="done", filename="duplicate.wav")
        try:
            res = client.get("/tasks/duplicates?filename=duplicate.wav")
            data = res.json()
            assert data["duplicates_found"] is True
            assert len(data["matches"]) >= 1
        finally:
            _cleanup(tid)

    def test_duplicate_only_done_tasks(self):
        tid1 = _add_task(status="error", filename="test_dup.wav")
        tid2 = _add_task(status="done", filename="test_dup.wav")
        try:
            res = client.get("/tasks/duplicates?filename=test_dup.wav")
            matches = res.json()["matches"]
            match_ids = [m["task_id"] for m in matches]
            assert tid2 in match_ids
            assert tid1 not in match_ids
        finally:
            _cleanup(tid1, tid2)

    def test_duplicate_missing_filename_param(self):
        res = client.get("/tasks/duplicates")
        assert res.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# PAUSE / RESUME
# ══════════════════════════════════════════════════════════════════════════════


class TestPauseResume:
    """Test POST /pause and /resume endpoints."""

    def test_pause_nonexistent_task(self):
        res = client.post("/pause/nonexistent-task")
        assert res.status_code == 404

    def test_resume_nonexistent_task(self):
        res = client.post("/resume/nonexistent-task")
        assert res.status_code == 404

    def test_pause_non_transcribing_task(self):
        tid = _add_task(status="queued")
        try:
            res = client.post(f"/pause/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_resume_task(self):
        tid = _add_task(status="paused")
        try:
            res = client.post(f"/resume/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD → TASK CREATION INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestUploadCreatesTask:
    """Test that upload creates a task entry."""

    def test_upload_creates_task_entry(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        assert res.status_code == 200
        tid = res.json()["task_id"]
        assert tid in state.tasks
        # Cleanup
        _cleanup(tid)

    def test_upload_task_has_status(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        tid = res.json()["task_id"]
        assert "status" in state.tasks[tid]
        _cleanup(tid)

    def test_upload_task_has_filename(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("my_audio.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        tid = res.json()["task_id"]
        assert state.tasks[tid]["filename"] == "my_audio.wav"
        _cleanup(tid)

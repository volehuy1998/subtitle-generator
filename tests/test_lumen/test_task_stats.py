"""Phase Lumen L17 — Task stats and history tests.

Tests task statistics endpoint, task list filtering, and task lifecycle
interactions with the list/stats endpoints.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app

# Use cookies_enabled client so session middleware assigns a persistent session_id
client = TestClient(app, base_url="https://testserver", cookies={"sg_session": "test-session-L17"})

# Fixed session ID matching the cookie above
_SESSION_ID = "test-session-L17"


def _add_task(task_id=None, status="done", **kwargs):
    """Add a task to state with matching session_id. Returns task_id."""
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test.wav",
        "session_id": _SESSION_ID,
        "language_requested": "auto",
        "model_size": "tiny",
        "device": "cpu",
        "language": "en",
        "segments": 0,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    task.update(kwargs)
    state.tasks[tid] = task
    return tid


def _cleanup(*task_ids):
    for tid in task_ids:
        state.tasks.pop(tid, None)


def _save_and_clear():
    """Save current tasks and clear state. Returns saved tasks."""
    saved = dict(state.tasks)
    state.tasks.clear()
    return saved


def _restore(saved):
    """Restore previously saved tasks."""
    state.tasks.clear()
    state.tasks.update(saved)


# ══════════════════════════════════════════════════════════════════════════════
# STATS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestStatsEndpoint:
    """Test GET /tasks/stats endpoint."""

    def test_stats_returns_200(self):
        res = client.get("/tasks/stats")
        assert res.status_code == 200

    def test_stats_has_total_tasks_key(self):
        res = client.get("/tasks/stats")
        assert "total_tasks" in res.json()

    def test_stats_has_completed_key(self):
        res = client.get("/tasks/stats")
        assert "completed" in res.json()

    def test_stats_has_failed_key(self):
        res = client.get("/tasks/stats")
        assert "failed" in res.json()

    def test_stats_has_cancelled_key(self):
        res = client.get("/tasks/stats")
        assert "cancelled" in res.json()

    def test_stats_has_active_key(self):
        res = client.get("/tasks/stats")
        assert "active" in res.json()

    def test_stats_has_total_segments_key(self):
        res = client.get("/tasks/stats")
        data = res.json()
        assert "total_segments" in data
        assert isinstance(data["total_segments"], int)

    def test_stats_has_total_audio_duration_sec_key(self):
        res = client.get("/tasks/stats")
        data = res.json()
        assert "total_audio_duration_sec" in data
        assert isinstance(data["total_audio_duration_sec"], (int, float))

    def test_stats_has_models_used_key(self):
        res = client.get("/tasks/stats")
        data = res.json()
        assert "models_used" in data
        assert isinstance(data["models_used"], dict)

    def test_stats_empty_state_returns_all_zeros(self):
        saved = _save_and_clear()
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_tasks"] == 0
            assert data["completed"] == 0
            assert data["failed"] == 0
            assert data["cancelled"] == 0
            assert data["active"] == 0
            assert data["total_segments"] == 0
            assert data["total_audio_duration_sec"] == 0
            assert data["models_used"] == {}
        finally:
            _restore(saved)

    def test_stats_single_done_task_counted_in_completed(self):
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["completed"] == 1
            assert data["total_tasks"] == 1
        finally:
            _restore(saved)

    def test_stats_single_error_task_counted_in_failed(self):
        saved = _save_and_clear()
        _add_task(status="error")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["failed"] == 1
            assert data["total_tasks"] == 1
        finally:
            _restore(saved)

    def test_stats_single_cancelled_task_counted_in_cancelled(self):
        saved = _save_and_clear()
        _add_task(status="cancelled")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["cancelled"] == 1
        finally:
            _restore(saved)

    def test_stats_active_task_counted_in_active(self):
        saved = _save_and_clear()
        _add_task(status="transcribing")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["active"] == 1
        finally:
            _restore(saved)

    def test_stats_multiple_tasks_correct_split(self):
        saved = _save_and_clear()
        _add_task(status="done")
        _add_task(status="done")
        _add_task(status="error")
        _add_task(status="cancelled")
        _add_task(status="transcribing")
        _add_task(status="queued")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_tasks"] == 6
            assert data["completed"] == 2
            assert data["failed"] == 1
            assert data["cancelled"] == 1
            assert data["active"] == 2
        finally:
            _restore(saved)

    def test_stats_total_segments_sums_across_done_tasks(self):
        saved = _save_and_clear()
        _add_task(status="done", segments=10)
        _add_task(status="done", segments=25)
        _add_task(status="error", segments=99)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_segments"] == 35
        finally:
            _restore(saved)

    def test_stats_total_audio_duration_sums_done_tasks(self):
        saved = _save_and_clear()
        _add_task(status="done", audio_duration=120.5)
        _add_task(status="done", audio_duration=60.3)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_audio_duration_sec"] == 180.8
        finally:
            _restore(saved)

    def test_stats_models_used_tracks_model_names_with_counts(self):
        saved = _save_and_clear()
        _add_task(status="done", model_size="tiny")
        _add_task(status="done", model_size="tiny")
        _add_task(status="done", model_size="base")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["models_used"]["tiny"] == 2
            assert data["models_used"]["base"] == 1
        finally:
            _restore(saved)

    def test_stats_models_used_ignores_non_done_tasks(self):
        saved = _save_and_clear()
        _add_task(status="done", model_size="small")
        _add_task(status="error", model_size="large")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert "small" in data["models_used"]
            assert "large" not in data["models_used"]
        finally:
            _restore(saved)

    def test_stats_session_scoped_only_own_tasks(self):
        """Stats only count tasks belonging to the current session."""
        saved = _save_and_clear()
        _add_task(status="done", session_id=_SESSION_ID)
        _add_task(status="done", session_id="other-session-xyz")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            # Only the task matching our session should be counted
            assert data["total_tasks"] == 1
            assert data["completed"] == 1
        finally:
            _restore(saved)


# ══════════════════════════════════════════════════════════════════════════════
# TASK LIST FILTERING
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskListFiltering:
    """Test GET /tasks list filtering and field validation."""

    def test_list_tasks_returns_array(self):
        res = client.get("/tasks")
        assert isinstance(res.json()["tasks"], list)

    def test_list_tasks_session_only_filters(self):
        saved = _save_and_clear()
        _add_task(status="done", session_id=_SESSION_ID)
        _add_task(status="done", session_id="other-session")
        try:
            res = client.get("/tasks?session_only=true")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            # Only our session's task should appear
            assert len(tasks) == 1
        finally:
            _restore(saved)

    def test_list_tasks_sorted_by_created_at_descending(self):
        saved = _save_and_clear()
        t1 = _add_task(created_at="2026-01-01T00:00:00+00:00")
        t2 = _add_task(created_at="2026-01-03T00:00:00+00:00")
        t3 = _add_task(created_at="2026-01-02T00:00:00+00:00")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            ids = [t["task_id"] for t in tasks]
            assert ids.index(t2) < ids.index(t3) < ids.index(t1)
        finally:
            _restore(saved)

    def test_list_tasks_limited_to_100(self):
        saved = _save_and_clear()
        for _ in range(105):
            _add_task()
        try:
            res = client.get("/tasks")
            assert len(res.json()["tasks"]) <= 100
        finally:
            _restore(saved)

    def test_list_task_has_required_fields(self):
        saved = _save_and_clear()
        _add_task(status="done", filename="hello.wav", percent=100)
        try:
            res = client.get("/tasks")
            task = res.json()["tasks"][0]
            assert "task_id" in task
            assert "status" in task
            assert "filename" in task
            assert "percent" in task
        finally:
            _restore(saved)

    def test_done_tasks_include_segments_count(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", segments=42)
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            assert task["segments"] == 42
        finally:
            _restore(saved)

    def test_error_tasks_include_error_info(self):
        saved = _save_and_clear()
        tid = _add_task(status="error", message="Transcription failed")
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            assert task["message"] == "Transcription failed"
        finally:
            _restore(saved)

    def test_list_handles_mixed_statuses(self):
        saved = _save_and_clear()
        _add_task(status="done")
        _add_task(status="error")
        _add_task(status="transcribing")
        _add_task(status="cancelled")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            statuses = {t["status"] for t in tasks}
            assert "done" in statuses
            assert "error" in statuses
            assert "transcribing" in statuses
            assert "cancelled" in statuses
        finally:
            _restore(saved)

    def test_list_task_has_model_size_field(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", model_size="small")
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            assert task["model_size"] == "small"
        finally:
            _restore(saved)

    def test_list_task_has_created_at_field(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", created_at="2026-03-16T12:00:00+00:00")
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            assert task["created_at"] == "2026-03-16T12:00:00+00:00"
        finally:
            _restore(saved)


# ══════════════════════════════════════════════════════════════════════════════
# TASK LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskLifecycle:
    """Test task lifecycle interactions with list and stats."""

    def test_create_task_appears_in_list(self):
        saved = _save_and_clear()
        tid = _add_task(status="done")
        try:
            res = client.get("/tasks")
            task_ids = [t["task_id"] for t in res.json()["tasks"]]
            assert tid in task_ids
        finally:
            _restore(saved)

    def test_delete_task_removed_from_list(self):
        saved = _save_and_clear()
        tid = _add_task(status="done")
        try:
            client.delete(f"/tasks/{tid}")
            res = client.get("/tasks")
            task_ids = [t["task_id"] for t in res.json()["tasks"]]
            assert tid not in task_ids
        finally:
            _restore(saved)

    def test_cancel_task_status_changes_in_list(self):
        saved = _save_and_clear()
        tid = _add_task(status="transcribing")
        try:
            client.post(f"/cancel/{tid}")
            assert state.tasks[tid].get("cancel_requested") is True
        finally:
            _restore(saved)

    def test_retry_task_new_task_appears(self):
        saved = _save_and_clear()
        tid = _add_task(status="error", filename="retry_me.wav")
        try:
            res = client.post(f"/tasks/{tid}/retry")
            new_tid = res.json()["new_task_id"]
            list_res = client.get("/tasks")
            task_ids = [t["task_id"] for t in list_res.json()["tasks"]]
            assert new_tid in task_ids
            _cleanup(new_tid)
        finally:
            _restore(saved)

    def test_queue_position_for_queued_tasks(self):
        saved = _save_and_clear()
        _add_task(status="queued")
        t2 = _add_task(status="queued")
        try:
            res = client.get(f"/tasks/{t2}/position")
            assert res.status_code == 200
            data = res.json()
            assert "position" in data
            assert "estimated_wait_sec" in data
        finally:
            _restore(saved)

    def test_multiple_concurrent_tasks_in_list(self):
        saved = _save_and_clear()
        _add_task(status="transcribing", filename="a.wav")
        _add_task(status="transcribing", filename="b.wav")
        _add_task(status="queued", filename="c.wav")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            assert len(tasks) == 3
            active = [t for t in tasks if t["status"] in ("transcribing", "queued")]
            assert len(active) == 3
        finally:
            _restore(saved)

    def test_task_timestamps_are_iso_format(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", created_at="2026-03-16T14:30:00+00:00")
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            created = task["created_at"]
            assert "T" in created
            assert ":" in created
        finally:
            _restore(saved)

    def test_task_model_size_field_present(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", model_size="medium")
        try:
            res = client.get("/tasks")
            task = next(t for t in res.json()["tasks"] if t["task_id"] == tid)
            assert "model_size" in task
            assert task["model_size"] == "medium"
        finally:
            _restore(saved)

    def test_stats_update_after_task_added(self):
        saved = _save_and_clear()
        try:
            res1 = client.get("/tasks/stats")
            assert res1.json()["total_tasks"] == 0
            _add_task(status="done", segments=5)
            res2 = client.get("/tasks/stats")
            assert res2.json()["total_tasks"] == 1
            assert res2.json()["total_segments"] == 5
        finally:
            _restore(saved)

    def test_stats_update_after_task_deleted(self):
        saved = _save_and_clear()
        tid = _add_task(status="done", segments=10)
        try:
            res1 = client.get("/tasks/stats")
            assert res1.json()["completed"] == 1
            client.delete(f"/tasks/{tid}")
            res2 = client.get("/tasks/stats")
            assert res2.json()["completed"] == 0
        finally:
            _restore(saved)

"""Tests for Sprint 13: Queue & Batch Pipeline Optimization.

S13-1: Queue position estimation
S13-2: Queue position endpoint
S13-3: Batch progress aggregation (in task list)
S13-4: Retry failed tasks
S13-5: Task deduplication check
S13-6: Integration tests
"""

from app.main import app
from app import state
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


def _setup_test_tasks():
    """Set up test tasks for queue tests."""
    state.tasks["q-task-1"] = {"status": "transcribing", "percent": 50, "filename": "video1.mp4", "message": "Working"}
    state.tasks["q-task-2"] = {"status": "queued", "percent": 0, "filename": "video2.mp4", "message": "Waiting"}
    state.tasks["q-task-3"] = {"status": "queued", "percent": 0, "filename": "video3.mp4", "message": "Waiting"}


def _cleanup_test_tasks():
    for tid in ["q-task-1", "q-task-2", "q-task-3", "err-task", "cancel-task", "done-task", "dup-task"]:
        state.tasks.pop(tid, None)
    # Also clean up any retry tasks
    to_remove = [tid for tid in state.tasks if state.tasks[tid].get("retry_of")]
    for tid in to_remove:
        del state.tasks[tid]


# ── S13-1: Queue Position Estimation ──


class TestQueuePosition:
    def setup_method(self):
        _cleanup_test_tasks()
        _setup_test_tasks()

    def teardown_method(self):
        _cleanup_test_tasks()

    def test_queued_task_has_position(self):
        from app.routes.tasks import _estimate_queue_position

        pos = _estimate_queue_position("q-task-2")
        assert pos["position"] >= 0

    def test_non_queued_task_position_zero(self):
        from app.routes.tasks import _estimate_queue_position

        pos = _estimate_queue_position("q-task-1")  # transcribing
        assert pos["position"] == 0

    def test_unknown_task_position_negative(self):
        from app.routes.tasks import _estimate_queue_position

        pos = _estimate_queue_position("nonexistent")
        assert pos["position"] == -1

    def test_estimated_wait_positive_for_queued(self):
        from app.routes.tasks import _estimate_queue_position

        pos = _estimate_queue_position("q-task-3")
        assert pos["estimated_wait_sec"] >= 0


# ── S13-2: Queue Position Endpoint ──


class TestQueuePositionEndpoint:
    def setup_method(self):
        _cleanup_test_tasks()
        _setup_test_tasks()

    def teardown_method(self):
        _cleanup_test_tasks()

    def test_position_endpoint_exists(self):
        res = client.get("/tasks/q-task-2/position")
        assert res.status_code == 200

    def test_position_endpoint_returns_position(self):
        res = client.get("/tasks/q-task-2/position")
        data = res.json()
        assert "position" in data
        assert "estimated_wait_sec" in data

    def test_position_404_for_unknown(self):
        res = client.get("/tasks/nonexistent/position")
        assert res.status_code == 404


# ── S13-3: Tasks List with Queue Info ──


class TestTasksListQueue:
    def setup_method(self):
        _cleanup_test_tasks()
        _setup_test_tasks()

    def teardown_method(self):
        _cleanup_test_tasks()

    def test_tasks_list_includes_queue_position(self):
        res = client.get("/tasks")
        data = res.json()
        queued_tasks = [t for t in data["tasks"] if t["status"] == "queued"]
        if queued_tasks:
            assert "position" in queued_tasks[0]
            assert "estimated_wait_sec" in queued_tasks[0]

    def test_tasks_list_still_works(self):
        res = client.get("/tasks")
        assert res.status_code == 200
        assert "tasks" in res.json()


# ── S13-4: Retry Failed Tasks ──


class TestRetryTask:
    def setup_method(self):
        _cleanup_test_tasks()
        state.tasks["err-task"] = {
            "status": "error",
            "percent": 0,
            "filename": "bad_video.mp4",
            "message": "Failed",
            "language_requested": "en",
            "session_id": "test",
        }
        state.tasks["cancel-task"] = {
            "status": "cancelled",
            "percent": 0,
            "filename": "cancelled_video.mp4",
            "message": "Cancelled",
            "language_requested": "auto",
            "session_id": "test",
        }
        state.tasks["done-task"] = {
            "status": "done",
            "percent": 100,
            "filename": "good_video.mp4",
            "message": "Done",
            "session_id": "test",
        }

    def teardown_method(self):
        _cleanup_test_tasks()

    def test_retry_failed_task(self):
        res = client.post("/tasks/err-task/retry")
        assert res.status_code == 200
        data = res.json()
        assert "new_task_id" in data
        assert data["original_task_id"] == "err-task"

    def test_retry_cancelled_task(self):
        res = client.post("/tasks/cancel-task/retry")
        assert res.status_code == 200

    def test_retry_done_task_rejected(self):
        res = client.post("/tasks/done-task/retry")
        assert res.status_code == 400

    def test_retry_unknown_task(self):
        res = client.post("/tasks/nonexistent/retry")
        assert res.status_code == 404

    def test_retry_creates_new_task(self):
        res = client.post("/tasks/err-task/retry")
        new_id = res.json()["new_task_id"]
        assert new_id in state.tasks
        assert state.tasks[new_id]["retry_of"] == "err-task"

    def test_retry_preserves_filename(self):
        res = client.post("/tasks/err-task/retry")
        new_id = res.json()["new_task_id"]
        assert state.tasks[new_id]["filename"] == "bad_video.mp4"


# ── S13-5: Task Deduplication ──


class TestDeduplication:
    def setup_method(self):
        _cleanup_test_tasks()
        state.tasks["dup-task"] = {
            "status": "done",
            "filename": "lecture.mp4",
            "file_size": 50000000,
            "language": "en",
            "segments": 42,
            "model_size": "medium",
        }

    def teardown_method(self):
        _cleanup_test_tasks()

    def test_duplicates_found(self):
        res = client.get("/tasks/duplicates?filename=lecture.mp4&file_size=50000000")
        assert res.status_code == 200
        data = res.json()
        assert data["duplicates_found"] is True
        assert len(data["matches"]) >= 1

    def test_no_duplicates(self):
        res = client.get("/tasks/duplicates?filename=unique_video.mp4")
        assert res.status_code == 200
        data = res.json()
        assert data["duplicates_found"] is False

    def test_duplicates_by_name_only(self):
        res = client.get("/tasks/duplicates?filename=lecture.mp4")
        data = res.json()
        assert data["duplicates_found"] is True

    def test_duplicates_match_structure(self):
        res = client.get("/tasks/duplicates?filename=lecture.mp4")
        data = res.json()
        match = data["matches"][0]
        assert "task_id" in match
        assert "filename" in match
        assert "segments" in match


# ── S13-6: Integration ──


class TestIntegration:
    def test_tasks_endpoint_accessible(self):
        assert client.get("/tasks").status_code == 200

    def test_duplicates_requires_filename(self):
        res = client.get("/tasks/duplicates")
        assert res.status_code == 422  # missing required query param

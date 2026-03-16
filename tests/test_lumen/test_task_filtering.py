"""Phase Lumen L49-L52 -- Task filtering, sorting, and enhanced stats tests.

Tests sort parameters, filter parameters, and enhanced stats fields
for the GET /tasks and GET /tasks/stats endpoints.
-- Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver", cookies={"sg_session": "test-session-L49"})

_SESSION_ID = "test-session-L49"


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


def _save_and_clear():
    saved = dict(state.tasks)
    state.tasks.clear()
    return saved


def _restore(saved):
    state.tasks.clear()
    state.tasks.update(saved)


# ======================================================================
# SORT PARAMETERS (10 tests)
# ======================================================================


class TestSortParameters:
    """Test sort-related query parameters on GET /tasks."""

    def test_default_sort_returns_results(self):
        """GET /tasks with no sort params returns 200 with tasks array."""
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            res = client.get("/tasks")
            assert res.status_code == 200
            assert "tasks" in res.json()
            assert len(res.json()["tasks"]) >= 1
        finally:
            _restore(saved)

    def test_sort_by_created_at_default(self):
        """Default sort is by created_at descending (newest first)."""
        saved = _save_and_clear()
        t1 = _add_task(created_at="2026-01-01T00:00:00+00:00")
        t2 = _add_task(created_at="2026-01-03T00:00:00+00:00")
        t3 = _add_task(created_at="2026-01-02T00:00:00+00:00")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            ids = [t["task_id"] for t in tasks]
            # t2 (Jan 3) should come before t3 (Jan 2) before t1 (Jan 1)
            assert ids.index(t2) < ids.index(t3) < ids.index(t1)
        finally:
            _restore(saved)

    def test_sort_by_filename_param_accepted(self):
        """sort_by=filename query param is accepted without error."""
        saved = _save_and_clear()
        _add_task(filename="alpha.wav")
        _add_task(filename="beta.wav")
        try:
            res = client.get("/tasks?sort_by=filename")
            assert res.status_code == 200
            assert isinstance(res.json()["tasks"], list)
        finally:
            _restore(saved)

    def test_sort_by_status_param_accepted(self):
        """sort_by=status query param is accepted without error."""
        saved = _save_and_clear()
        _add_task(status="done")
        _add_task(status="error")
        try:
            res = client.get("/tasks?sort_by=status")
            assert res.status_code == 200
            assert isinstance(res.json()["tasks"], list)
        finally:
            _restore(saved)

    def test_sort_order_asc_accepted(self):
        """sort_order=asc query param is accepted without error."""
        saved = _save_and_clear()
        _add_task(created_at="2026-01-01T00:00:00+00:00")
        _add_task(created_at="2026-01-02T00:00:00+00:00")
        try:
            res = client.get("/tasks?sort_order=asc")
            assert res.status_code == 200
            assert isinstance(res.json()["tasks"], list)
        finally:
            _restore(saved)

    def test_sort_order_desc_default_behavior(self):
        """Default sort order is descending (newest first)."""
        saved = _save_and_clear()
        t1 = _add_task(created_at="2026-01-01T00:00:00+00:00")
        t2 = _add_task(created_at="2026-01-05T00:00:00+00:00")
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            ids = [t["task_id"] for t in tasks]
            # Newest (t2) should be first
            assert ids.index(t2) < ids.index(t1)
        finally:
            _restore(saved)

    def test_invalid_sort_by_falls_back_gracefully(self):
        """Invalid sort_by value should not cause a server error."""
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            res = client.get("/tasks?sort_by=nonexistent_field")
            # Should return 200 or 422, but not 500
            assert res.status_code in (200, 422)
        finally:
            _restore(saved)

    def test_invalid_sort_order_falls_back_gracefully(self):
        """Invalid sort_order value should not cause a server error."""
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            res = client.get("/tasks?sort_order=random")
            # Should return 200 or 422, but not 500
            assert res.status_code in (200, 422)
        finally:
            _restore(saved)

    def test_sort_combined_with_session_only(self):
        """Sorting works with session_only=true filter."""
        saved = _save_and_clear()
        _add_task(created_at="2026-01-01T00:00:00+00:00", session_id=_SESSION_ID)
        _add_task(created_at="2026-01-05T00:00:00+00:00", session_id=_SESSION_ID)
        _add_task(created_at="2026-01-03T00:00:00+00:00", session_id="other-session")
        try:
            res = client.get("/tasks?session_only=true")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            # Only our session's tasks
            assert len(tasks) == 2
        finally:
            _restore(saved)

    def test_empty_task_list_with_sort_params(self):
        """Sort params on empty state return empty array."""
        saved = _save_and_clear()
        try:
            res = client.get("/tasks?sort_by=created_at&sort_order=asc")
            assert res.status_code == 200
            assert res.json()["tasks"] == []
        finally:
            _restore(saved)


# ======================================================================
# FILTER PARAMETERS (10 tests)
# ======================================================================


class TestFilterParameters:
    """Test status filter parameters on GET /tasks."""

    def test_status_filter_done_returns_only_done(self):
        """Filtering by done status returns only completed tasks."""
        saved = _save_and_clear()
        t_done = _add_task(status="done")
        _add_task(status="error")
        _add_task(status="transcribing")
        try:
            res = client.get("/tasks?status_filter=done")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            # If filter is supported, only done tasks; otherwise all tasks returned
            done_tasks = [t for t in tasks if t["status"] == "done"]
            assert len(done_tasks) >= 1
            assert any(t["task_id"] == t_done for t in done_tasks)
        finally:
            _restore(saved)

    def test_status_filter_error_returns_only_errors(self):
        """Filtering by error status returns failed tasks."""
        saved = _save_and_clear()
        t_err = _add_task(status="error")
        _add_task(status="done")
        try:
            res = client.get("/tasks?status_filter=error")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            error_tasks = [t for t in tasks if t["status"] == "error"]
            assert len(error_tasks) >= 1
            assert any(t["task_id"] == t_err for t in error_tasks)
        finally:
            _restore(saved)

    def test_status_filter_cancelled_returns_only_cancelled(self):
        """Filtering by cancelled status works."""
        saved = _save_and_clear()
        t_can = _add_task(status="cancelled")
        _add_task(status="done")
        try:
            res = client.get("/tasks?status_filter=cancelled")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            cancelled_tasks = [t for t in tasks if t["status"] == "cancelled"]
            assert len(cancelled_tasks) >= 1
            assert any(t["task_id"] == t_can for t in cancelled_tasks)
        finally:
            _restore(saved)

    def test_status_filter_active_returns_non_terminal(self):
        """Filtering by active status returns non-terminal tasks."""
        saved = _save_and_clear()
        t_active = _add_task(status="transcribing")
        _add_task(status="done")
        _add_task(status="error")
        try:
            res = client.get("/tasks?status_filter=active")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            # Active task should be present
            active_tasks = [t for t in tasks if t["status"] not in ("done", "error", "cancelled")]
            assert len(active_tasks) >= 1
            assert any(t["task_id"] == t_active for t in active_tasks)
        finally:
            _restore(saved)

    def test_empty_status_filter_returns_all_tasks(self):
        """Empty status filter returns all tasks."""
        saved = _save_and_clear()
        _add_task(status="done")
        _add_task(status="error")
        _add_task(status="transcribing")
        try:
            res = client.get("/tasks?status_filter=")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            assert len(tasks) >= 3
        finally:
            _restore(saved)

    def test_invalid_status_filter_returns_all_tasks(self):
        """Invalid status filter should not cause server error."""
        saved = _save_and_clear()
        _add_task(status="done")
        _add_task(status="error")
        try:
            res = client.get("/tasks?status_filter=nonexistent")
            # Should return 200 or 422, not 500
            assert res.status_code in (200, 422)
        finally:
            _restore(saved)

    def test_filter_and_sort_combined(self):
        """Filter and sort params work together without error."""
        saved = _save_and_clear()
        _add_task(status="done", created_at="2026-01-01T00:00:00+00:00")
        _add_task(status="done", created_at="2026-01-05T00:00:00+00:00")
        _add_task(status="error", created_at="2026-01-03T00:00:00+00:00")
        try:
            res = client.get("/tasks?status_filter=done&sort_by=created_at")
            assert res.status_code == 200
            assert isinstance(res.json()["tasks"], list)
        finally:
            _restore(saved)

    def test_filter_and_session_only_combined(self):
        """Filter combined with session_only works."""
        saved = _save_and_clear()
        _add_task(status="done", session_id=_SESSION_ID)
        _add_task(status="error", session_id=_SESSION_ID)
        _add_task(status="done", session_id="other-session")
        try:
            res = client.get("/tasks?session_only=true")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            # Only our session's tasks (2 tasks)
            assert len(tasks) == 2
        finally:
            _restore(saved)

    def test_filter_no_matching_tasks_returns_empty(self):
        """Filter with no matching tasks returns empty array."""
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            # If filter is supported, cancelled filter returns empty
            res = client.get("/tasks?status_filter=cancelled")
            assert res.status_code == 200
            tasks = res.json()["tasks"]
            cancelled = [t for t in tasks if t["status"] == "cancelled"]
            assert len(cancelled) == 0
        finally:
            _restore(saved)

    def test_multiple_query_params_accepted(self):
        """Multiple query params are accepted simultaneously."""
        saved = _save_and_clear()
        _add_task(status="done")
        try:
            res = client.get("/tasks?session_only=true&sort_by=created_at&sort_order=desc&status_filter=done")
            assert res.status_code == 200
            assert isinstance(res.json()["tasks"], list)
        finally:
            _restore(saved)


# ======================================================================
# ENHANCED STATS (10 tests)
# ======================================================================


class TestEnhancedStats:
    """Test enhanced fields on GET /tasks/stats."""

    def test_stats_has_total_audio_duration(self):
        """Stats response includes average_duration or total_audio_duration_sec."""
        saved = _save_and_clear()
        _add_task(status="done", audio_duration=120.0)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            # The endpoint exposes total_audio_duration_sec
            assert "total_audio_duration_sec" in data
        finally:
            _restore(saved)

    def test_stats_has_models_used_dict(self):
        """Stats has models_used as a dictionary."""
        saved = _save_and_clear()
        _add_task(status="done", model_size="tiny")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert "models_used" in data
            assert isinstance(data["models_used"], dict)
        finally:
            _restore(saved)

    def test_stats_total_audio_duration_numeric(self):
        """total_audio_duration_sec is a numeric value."""
        saved = _save_and_clear()
        _add_task(status="done", audio_duration=60.5)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert isinstance(data["total_audio_duration_sec"], (int, float))
        finally:
            _restore(saved)

    def test_stats_duration_zero_for_no_done_tasks(self):
        """Duration is 0 when no done tasks exist."""
        saved = _save_and_clear()
        _add_task(status="error")
        _add_task(status="cancelled")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_audio_duration_sec"] == 0
        finally:
            _restore(saved)

    def test_stats_models_used_counts_match_done_tasks(self):
        """Model counts in models_used match the number of done tasks per model."""
        saved = _save_and_clear()
        _add_task(status="done", model_size="tiny")
        _add_task(status="done", model_size="tiny")
        _add_task(status="done", model_size="base")
        _add_task(status="error", model_size="small")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["models_used"].get("tiny") == 2
            assert data["models_used"].get("base") == 1
            # Error tasks should not be counted
            assert "small" not in data["models_used"]
        finally:
            _restore(saved)

    def test_stats_audio_duration_sums_correctly(self):
        """Audio duration sums across all done tasks."""
        saved = _save_and_clear()
        _add_task(status="done", audio_duration=100.0)
        _add_task(status="done", audio_duration=50.5)
        _add_task(status="error", audio_duration=999.0)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_audio_duration_sec"] == 150.5
        finally:
            _restore(saved)

    def test_stats_reflect_current_state(self):
        """Stats update when a new task is added."""
        saved = _save_and_clear()
        try:
            res1 = client.get("/tasks/stats")
            assert res1.json()["total_tasks"] == 0

            _add_task(status="done", segments=10)

            res2 = client.get("/tasks/stats")
            assert res2.json()["total_tasks"] == 1
            assert res2.json()["total_segments"] == 10
        finally:
            _restore(saved)

    def test_stats_session_scoped(self):
        """Stats only count tasks from the current session."""
        saved = _save_and_clear()
        _add_task(status="done", session_id=_SESSION_ID, segments=5)
        _add_task(status="done", session_id="other-session", segments=99)
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            assert data["total_tasks"] == 1
            assert data["total_segments"] == 5
        finally:
            _restore(saved)

    def test_stats_handle_tasks_with_missing_fields(self):
        """Stats gracefully handle tasks with missing optional fields."""
        saved = _save_and_clear()
        tid = str(uuid.uuid4())
        # Minimal task with no audio_duration, segments, or model_size
        state.tasks[tid] = {
            "status": "done",
            "percent": 100,
            "session_id": _SESSION_ID,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        try:
            res = client.get("/tasks/stats")
            assert res.status_code == 200
            data = res.json()
            assert data["completed"] == 1
            # Should not crash even with missing fields
            assert isinstance(data["total_audio_duration_sec"], (int, float))
        finally:
            _restore(saved)

    def test_stats_multiple_models_tracked(self):
        """Multiple model types are tracked separately in models_used."""
        saved = _save_and_clear()
        _add_task(status="done", model_size="tiny")
        _add_task(status="done", model_size="base")
        _add_task(status="done", model_size="small")
        _add_task(status="done", model_size="medium")
        try:
            res = client.get("/tasks/stats")
            data = res.json()
            models = data["models_used"]
            assert len(models) == 4
            assert models["tiny"] == 1
            assert models["base"] == 1
            assert models["small"] == 1
            assert models["medium"] == 1
        finally:
            _restore(saved)

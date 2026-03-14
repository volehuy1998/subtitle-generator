"""Tests for task control endpoints: cancel, pause, resume."""

import threading
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_task(task_id, **overrides):
    """Create a minimal task in state.tasks and return it."""
    task = {"status": "transcribing", "percent": 15, "message": "Transcribing...", **overrides}
    state.tasks[task_id] = task
    return task


def _cleanup(task_id):
    state.tasks.pop(task_id, None)


class TestCancel:
    """Tests for POST /cancel/{task_id}."""

    def test_cancel_not_found(self):
        resp = client.post("/cancel/nonexistent")
        assert resp.status_code == 404

    def test_cancel_already_finished(self):
        tid = "test-cancel-done"
        try:
            _make_task(tid, status="done")
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 400
            assert "already finished" in resp.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_cancel_already_requested(self):
        tid = "test-cancel-dup"
        try:
            _make_task(tid, cancel_requested=True)
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Cancel already requested"
        finally:
            _cleanup(tid)

    def test_cancel_success(self):
        tid = "test-cancel-ok"
        try:
            task = _make_task(tid)
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Cancel requested"
            assert task["cancel_requested"] is True
        finally:
            _cleanup(tid)

    def test_cancel_unblocks_paused_task(self):
        tid = "test-cancel-pause"
        try:
            evt = threading.Event()
            evt.clear()  # Simulates paused state
            _make_task(tid, pause_event=evt)
            assert not evt.is_set()
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 200
            assert evt.is_set(), "Cancel should unblock pause_event"
        finally:
            _cleanup(tid)

    def test_cancel_kills_subprocess(self):
        tid = "test-cancel-proc"
        try:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            _make_task(tid, _subprocess=mock_proc)
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 200
            mock_proc.kill.assert_called_once()
        finally:
            _cleanup(tid)

    def test_cancel_error_status(self):
        tid = "test-cancel-err"
        try:
            _make_task(tid, status="error")
            resp = client.post(f"/cancel/{tid}")
            assert resp.status_code == 400
        finally:
            _cleanup(tid)


class TestPause:
    """Tests for POST /pause/{task_id}."""

    def test_pause_not_found(self):
        resp = client.post("/pause/nonexistent")
        assert resp.status_code == 404

    def test_pause_wrong_status(self):
        tid = "test-pause-extract"
        try:
            _make_task(tid, status="extracting")
            resp = client.post(f"/pause/{tid}")
            assert resp.status_code == 400
            assert "transcription" in resp.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_pause_already_paused(self):
        tid = "test-pause-dup"
        try:
            _make_task(tid, status="paused")
            resp = client.post(f"/pause/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Already paused"
        finally:
            _cleanup(tid)

    def test_pause_already_pausing(self):
        tid = "test-pause-ing"
        try:
            evt = threading.Event()
            evt.clear()  # Already pausing
            _make_task(tid, pause_event=evt)
            resp = client.post(f"/pause/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Already pausing"
        finally:
            _cleanup(tid)

    def test_pause_success(self):
        tid = "test-pause-ok"
        try:
            evt = threading.Event()
            evt.set()  # Running
            _make_task(tid, pause_event=evt)
            assert evt.is_set()
            resp = client.post(f"/pause/{tid}")
            assert resp.status_code == 200
            assert "pause" in resp.json()["message"].lower()
            assert not evt.is_set(), "pause_event should be cleared"
        finally:
            _cleanup(tid)

    def test_pause_no_event_object(self):
        """Pause without pause_event still returns success."""
        tid = "test-pause-noevt"
        try:
            _make_task(tid)
            resp = client.post(f"/pause/{tid}")
            assert resp.status_code == 200
        finally:
            _cleanup(tid)


class TestResume:
    """Tests for POST /resume/{task_id}."""

    def test_resume_not_found(self):
        resp = client.post("/resume/nonexistent")
        assert resp.status_code == 404

    def test_resume_success(self):
        tid = "test-resume-ok"
        try:
            evt = threading.Event()
            evt.clear()  # Paused
            _make_task(tid, status="paused", pause_event=evt)
            assert not evt.is_set()
            resp = client.post(f"/resume/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Resumed"
            assert evt.is_set(), "pause_event should be set after resume"
        finally:
            _cleanup(tid)

    def test_resume_no_event_object(self):
        """Resume without pause_event still returns success."""
        tid = "test-resume-noevt"
        try:
            _make_task(tid, status="paused")
            resp = client.post(f"/resume/{tid}")
            assert resp.status_code == 200
            assert resp.json()["message"] == "Resumed"
        finally:
            _cleanup(tid)

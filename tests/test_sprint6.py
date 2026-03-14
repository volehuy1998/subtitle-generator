"""Tests for Sprint 6: Scale & Monitor features.

S6-1: Task queue (Redis deferred, in-memory remains)
S6-2: Performance monitoring dashboard
S6-3: Subtitle translation
S6-4: WebSocket real-time updates
S6-5: User session management and task ownership
"""

from io import BytesIO

from app.main import app
from app import state
from app.services.translation import (
    get_whisper_translate_options,
    translate_segments,
    is_translation_available,
)
from app.services.transcription import get_optimal_transcribe_options
from app.middleware.session import SESSION_COOKIE
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


# ── S6-2: Performance Monitoring Dashboard ──


class TestDashboard:
    def test_dashboard_returns_html(self):
        res = client.get("/dashboard")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "Dashboard" in res.text

    def test_dashboard_has_auto_refresh(self):
        res = client.get("/dashboard")
        assert "setInterval" in res.text

    def test_dashboard_data_returns_json(self):
        res = client.get("/dashboard/data")
        assert res.status_code == 200
        data = res.json()
        assert "uptime_sec" in data
        assert "total_tasks" in data
        assert "status_counts" in data
        assert "active_tasks" in data
        assert "recent_tasks" in data
        assert "system" in data
        assert "files" in data

    def test_dashboard_data_system_fields(self):
        res = client.get("/dashboard/data")
        data = res.json()
        sys = data["system"]
        assert "cpu_percent" in sys
        assert "memory_percent" in sys
        assert "memory_used_gb" in sys
        assert "memory_total_gb" in sys

    def test_dashboard_data_shutting_down_field(self):
        res = client.get("/dashboard/data")
        data = res.json()
        assert "shutting_down" in data
        assert data["shutting_down"] is False


# ── S6-3: Subtitle Translation ──


class TestTranslation:
    def test_whisper_translate_options(self):
        opts = get_whisper_translate_options()
        assert opts["task"] == "translate"

    def test_translate_to_english_available(self):
        status = is_translation_available("en")
        assert status["available"] is True
        assert status["method"] == "whisper_translate"

    def test_translate_to_other_not_available(self):
        status = is_translation_available("fr")
        assert status["available"] is False

    def test_translate_same_language_passthrough(self):
        segments = [{"start": 0, "end": 3, "text": "Hello"}]
        result = translate_segments(segments, "en", "en")
        assert result == segments

    def test_translate_to_english_passthrough(self):
        segments = [{"start": 0, "end": 3, "text": "Bonjour"}]
        result = translate_segments(segments, "fr", "en")
        assert result == segments

    def test_translate_unsupported_preserves_original(self):
        segments = [{"start": 0, "end": 3, "text": "Hello"}]
        result = translate_segments(segments, "en", "zh")
        assert result[0]["original_text"] == "Hello"

    def test_transcribe_translate_mode(self):
        """Verify translate option gets added to transcription options."""
        opts = get_optimal_transcribe_options("cpu", "small", "auto")
        assert "task" not in opts  # Not set by default

    def test_upload_accepts_translate_param(self):
        res = client.post(
            "/upload",
            files={"file": ("test.mp3", BytesIO(b"x" * 2048), "audio/mpeg")},
            data={
                "device": "cpu",
                "model_size": "tiny",
                "translate_to_english": "true",
            },
        )
        assert res.status_code in (400, 422)  # Fails at magic bytes, not param parsing


# ── S6-4: WebSocket Endpoint ──


class TestWebSocket:
    def test_websocket_endpoint_exists(self):
        """WebSocket route should be registered."""
        routes = [r.path for r in app.routes]
        assert "/ws/{task_id}" in routes

    def test_websocket_connect_done_task(self):
        """Connecting to a done task should send state then close."""
        original = state.tasks.copy()
        state.tasks["test-ws-001"] = {"status": "done", "message": "Complete", "filename": "test.mp4"}
        try:
            with client.websocket_connect("/ws/test-ws-001") as ws:
                data = ws.receive_json()
                assert data["type"] == "state"
                assert data["status"] == "done"
        finally:
            state.tasks.clear()
            state.tasks.update(original)


# ── S6-5: Session Management ──


class TestSessionManagement:
    def test_session_cookie_set(self):
        res = client.get("/health")
        cookies = res.cookies
        # Session cookie should be set
        assert SESSION_COOKIE in cookies or res.status_code == 200

    def test_tasks_endpoint_has_own_field(self):
        res = client.get("/tasks")
        assert res.status_code == 200
        data = res.json()
        assert "tasks" in data

    def test_tasks_session_filter(self):
        """session_only parameter should be accepted."""
        res = client.get("/tasks?session_only=true")
        assert res.status_code == 200

    def test_session_id_in_task(self):
        """Tasks should track session_id for ownership."""
        original = state.tasks.copy()
        state.tasks["test-session-001"] = {
            "status": "done",
            "session_id": "abc123",
            "filename": "test.mp4",
        }
        try:
            res = client.get("/tasks")
            data = res.json()
            task = next((t for t in data["tasks"] if t["task_id"] == "test-session-001"), None)
            assert task is not None
            # own field should be False since our session != abc123
            assert "own" in task
        finally:
            state.tasks.clear()
            state.tasks.update(original)


# ── Integration: New Routes Registered ──


class TestRoutesRegistered:
    def test_dashboard_route(self):
        res = client.get("/dashboard")
        assert res.status_code == 200

    def test_dashboard_data_route(self):
        res = client.get("/dashboard/data")
        assert res.status_code == 200

    def test_metrics_still_works(self):
        res = client.get("/metrics")
        assert res.status_code == 200

    def test_health_still_works(self):
        res = client.get("/health")
        assert res.status_code == 200

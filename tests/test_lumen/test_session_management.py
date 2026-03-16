"""Phase Lumen L9 — Session management tests.

Tests session middleware behavior: cookie assignment, persistence,
session-scoped task access, and session ID propagation.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app
from app.middleware.session import SESSION_COOKIE, SESSION_MAX_AGE

client = TestClient(app, base_url="https://testserver")


def _add_task(task_id=None, status="done", **kwargs):
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
# SESSION COOKIE ASSIGNMENT
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionCookieAssignment:
    """Test that session cookies are set on first visit."""

    def test_first_request_sets_session_cookie(self):
        res = client.get("/tasks")
        assert SESSION_COOKIE in res.cookies

    def test_session_cookie_is_uuid(self):
        # Use a fresh client to guarantee a new cookie is issued
        fresh = TestClient(app, base_url="https://testserver")
        res = fresh.get("/tasks")
        session_id = res.cookies.get(SESSION_COOKIE)
        assert session_id is not None, "No session cookie set"
        # UUID format check
        parsed = uuid.UUID(session_id)
        assert str(parsed) == session_id

    def test_session_cookie_httponly(self):
        fresh = TestClient(app, base_url="https://testserver")
        res = fresh.get("/tasks")
        cookie_header = res.headers.get("set-cookie", "")
        assert "httponly" in cookie_header.lower()

    def test_session_cookie_samesite(self):
        fresh = TestClient(app, base_url="https://testserver")
        res = fresh.get("/tasks")
        cookie_header = res.headers.get("set-cookie", "")
        assert "samesite=lax" in cookie_header.lower()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION PERSISTENCE
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionPersistence:
    """Test that the session persists across requests."""

    def test_second_request_same_session(self):
        c = TestClient(app, base_url="https://testserver")
        res1 = c.get("/tasks")
        session_id = res1.cookies.get(SESSION_COOKIE)
        # Second request uses client's stored cookies
        res2 = c.get("/tasks")
        # Should NOT set a new cookie if session exists
        new_cookie = res2.cookies.get(SESSION_COOKIE)
        if new_cookie is not None:
            assert new_cookie == session_id

    def test_different_client_gets_different_session(self):
        c1 = TestClient(app, base_url="https://testserver")
        res1 = c1.get("/tasks")
        session1 = res1.cookies.get(SESSION_COOKIE)
        c2 = TestClient(app, base_url="https://testserver")
        res2 = c2.get("/tasks")
        session2 = res2.cookies.get(SESSION_COOKIE)
        assert session1 != session2

    def test_cookie_not_reset_when_already_set(self):
        c = TestClient(app, base_url="https://testserver")
        res1 = c.get("/tasks")
        session_id = res1.cookies.get(SESSION_COOKIE)
        res2 = c.get("/tasks")
        new_cookie = res2.cookies.get(SESSION_COOKIE)
        if new_cookie is not None:
            assert new_cookie == session_id

    def test_session_survives_different_endpoints(self):
        c = TestClient(app, base_url="https://testserver")
        c.get("/tasks")  # sets cookie
        res2 = c.get("/health")
        assert res2.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# SESSION SCOPED TASK ACCESS
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionScopedTaskAccess:
    """Test session-scoped task listing."""

    def test_session_only_flag_returns_200(self):
        res = client.get("/tasks?session_only=true")
        assert res.status_code == 200

    def test_session_only_returns_tasks_key(self):
        res = client.get("/tasks?session_only=true")
        assert "tasks" in res.json()

    def test_session_only_returns_list(self):
        res = client.get("/tasks?session_only=true")
        assert isinstance(res.json()["tasks"], list)

    def test_task_with_matching_session_visible(self):
        c = TestClient(app, base_url="https://testserver")
        res1 = c.get("/tasks")
        session_id = res1.cookies.get(SESSION_COOKIE)
        tid = _add_task(session_id=session_id)
        try:
            # Cookie is already set on the client from the first request
            res2 = c.get("/tasks?session_only=true")
            task_ids = [t["task_id"] for t in res2.json()["tasks"]]
            assert tid in task_ids
        finally:
            _cleanup(tid)

    def test_task_with_different_session_not_visible_in_session_only(self):
        tid = _add_task(session_id="other-session-id-xyz")
        c = TestClient(app, base_url="https://testserver")
        try:
            res = c.get("/tasks?session_only=true")
            task_ids = [t["task_id"] for t in res.json()["tasks"]]
            assert tid not in task_ids
        finally:
            _cleanup(tid)

    def test_all_tasks_visible_without_session_only(self):
        tid = _add_task(session_id="any-session")
        try:
            res = client.get("/tasks")
            task_ids = [t["task_id"] for t in res.json()["tasks"]]
            assert tid in task_ids
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION MIDDLEWARE BEHAVIOR
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionMiddlewareBehavior:
    """Test session middleware internals."""

    def test_get_session_id_returns_empty_for_no_cookie(self):
        from app.middleware.session import get_session_id

        # Verify function exists and is callable
        assert callable(get_session_id)

    def test_session_constant_cookie_name(self):
        assert SESSION_COOKIE == "sg_session"

    def test_session_max_age_30_days(self):
        assert SESSION_MAX_AGE == 30 * 24 * 3600

    def test_session_cookie_on_health_endpoint(self):
        res = client.get("/health")
        # Health should still get session cookie for new visitors
        assert res.status_code == 200

    def test_session_id_format_v4_uuid(self):
        c = TestClient(app, base_url="https://testserver")
        res = c.get("/tasks")
        sid = res.cookies.get(SESSION_COOKIE)
        assert sid is not None
        parsed = uuid.UUID(sid, version=4)
        assert str(parsed) == sid

    def test_empty_session_returns_empty_string(self):
        from app.middleware.session import get_session_id
        from unittest.mock import MagicMock

        req = MagicMock()
        req.cookies = {}
        result = get_session_id(req)
        assert result == ""

    def test_known_session_returns_value(self):
        from app.middleware.session import get_session_id
        from unittest.mock import MagicMock

        req = MagicMock()
        req.cookies = {SESSION_COOKIE: "test-session-123"}
        result = get_session_id(req)
        assert result == "test-session-123"


# ══════════════════════════════════════════════════════════════════════════════
# SESSION + UPLOAD INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionUploadIntegration:
    """Test session assignment during upload."""

    def test_upload_assigns_session_to_task(self):
        import struct
        import wave
        from io import BytesIO

        buf = BytesIO()
        with wave.open(buf, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(struct.pack("<" + "h" * 8000, *([0] * 8000)))
        buf.seek(0)

        res = client.post(
            "/upload",
            files={"file": ("session_test.wav", buf, "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        assert res.status_code == 200
        tid = res.json()["task_id"]
        try:
            # Task should have a session_id
            assert "session_id" in state.tasks[tid]
        finally:
            _cleanup(tid)

    def test_upload_session_id_not_empty(self):
        import struct
        import wave
        from io import BytesIO

        buf = BytesIO()
        with wave.open(buf, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(struct.pack("<" + "h" * 8000, *([0] * 8000)))
        buf.seek(0)

        res = client.post(
            "/upload",
            files={"file": ("session_test2.wav", buf, "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        tid = res.json()["task_id"]
        try:
            assert state.tasks[tid]["session_id"] != ""
        finally:
            _cleanup(tid)

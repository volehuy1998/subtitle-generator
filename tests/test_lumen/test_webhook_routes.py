"""Phase Lumen L9 — Webhook route tests.

Tests webhook registration, retrieval, deletion, URL validation,
SSRF protection, and pending webhook tracking.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app
from app.routes.webhooks import _webhooks, get_pending_webhooks

client = TestClient(app, base_url="https://testserver")


def _add_task(task_id=None, status="transcribing", **kwargs):
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 0,
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
        _webhooks.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# REGISTER WEBHOOK
# ══════════════════════════════════════════════════════════════════════════════


class TestRegisterWebhook:
    """Test POST /webhooks/register."""

    def test_register_returns_200(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_register_returns_message(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.json()["message"] == "Webhook registered"
        finally:
            _cleanup(tid)

    def test_register_returns_task_id(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)

    def test_register_returns_url(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.json()["url"] == "https://example.com/callback"
        finally:
            _cleanup(tid)

    def test_register_nonexistent_task_returns_404(self):
        res = client.post(
            "/webhooks/register",
            json={
                "task_id": "nonexistent-task",
                "url": "https://example.com/callback",
            },
        )
        assert res.status_code == 404

    def test_register_done_task_returns_400(self):
        tid = _add_task(status="done")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_register_error_task_returns_400(self):
        tid = _add_task(status="error")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_register_cancelled_task_returns_400(self):
        tid = _add_task(status="cancelled")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# WEBHOOK URL VALIDATION (SSRF)
# ══════════════════════════════════════════════════════════════════════════════


class TestWebhookURLValidation:
    """Test SSRF protection on webhook URLs."""

    def test_localhost_rejected(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "http://localhost/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_loopback_ipv4_rejected(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "http://127.0.0.1/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_no_scheme_rejected(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "example.com/callback",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_ftp_scheme_rejected(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "ftp://example.com/file",
                },
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_missing_url_returns_422(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                },
            )
            assert res.status_code == 422
        finally:
            _cleanup(tid)

    def test_missing_task_id_returns_422(self):
        res = client.post(
            "/webhooks/register",
            json={
                "url": "https://example.com/callback",
            },
        )
        assert res.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET WEBHOOK
# ══════════════════════════════════════════════════════════════════════════════


class TestGetWebhook:
    """Test GET /webhooks/{task_id}."""

    def test_get_registered_webhook(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/hook",
                },
            )
            res = client.get(f"/webhooks/{tid}")
            assert res.status_code == 200
            assert res.json()["url"] == "https://example.com/hook"
        finally:
            _cleanup(tid)

    def test_get_unregistered_returns_404(self):
        res = client.get("/webhooks/nonexistent-task")
        assert res.status_code == 404

    def test_get_returns_task_id(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/hook",
                },
            )
            res = client.get(f"/webhooks/{tid}")
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# DELETE WEBHOOK
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteWebhook:
    """Test DELETE /webhooks/{task_id}."""

    def test_delete_registered_webhook(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/hook",
                },
            )
            res = client.delete(f"/webhooks/{tid}")
            assert res.status_code == 200
            assert res.json()["message"] == "Webhook removed"
        finally:
            _cleanup(tid)

    def test_delete_unregistered_returns_404(self):
        res = client.delete("/webhooks/nonexistent-task")
        assert res.status_code == 404

    def test_delete_removes_from_registry(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/hook",
                },
            )
            client.delete(f"/webhooks/{tid}")
            res = client.get(f"/webhooks/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_delete_twice_returns_404(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/hook",
                },
            )
            client.delete(f"/webhooks/{tid}")
            res = client.delete(f"/webhooks/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# PENDING WEBHOOKS
# ══════════════════════════════════════════════════════════════════════════════


class TestPendingWebhooks:
    """Test get_pending_webhooks utility."""

    def test_pending_returns_dict(self):
        result = get_pending_webhooks()
        assert isinstance(result, dict)

    def test_pending_includes_registered(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/pending",
                },
            )
            pending = get_pending_webhooks()
            assert tid in pending
        finally:
            _cleanup(tid)

    def test_pending_excludes_deleted(self):
        tid = _add_task(status="transcribing")
        try:
            client.post(
                "/webhooks/register",
                json={
                    "task_id": tid,
                    "url": "https://example.com/pending2",
                },
            )
            client.delete(f"/webhooks/{tid}")
            pending = get_pending_webhooks()
            assert tid not in pending
        finally:
            _cleanup(tid)

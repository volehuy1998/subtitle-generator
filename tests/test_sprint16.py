"""Tests for Sprint 16: Advanced Security & Audit.

S16-1: Audit logging (auth events, API key usage)
S16-2: CORS configuration
S16-3: Request body size limiting
S16-4: Brute force protection
S16-5: File quarantine
S16-6: Security audit endpoint
S16-7: Integration tests
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.audit import (
    _audit_entries,
    log_audit_event,
    get_recent_audit_events,
    get_audit_stats,
)
from app.middleware.brute_force import (
    _tracker,
    record_auth_failure,
    is_ip_blocked,
    get_brute_force_stats,
    MAX_FAILURES,
)
from app.middleware.cors import get_cors_origins
from app.services.quarantine import QUARANTINE_DIR, quarantine_file, get_quarantine_count

client = TestClient(app)


def _cleanup_audit():
    _audit_entries.clear()


def _cleanup_brute_force():
    _tracker.clear()


# ── S16-1: Audit Logging ──

class TestAuditLogging:
    def setup_method(self):
        _cleanup_audit()

    def teardown_method(self):
        _cleanup_audit()

    def test_log_audit_event_basic(self):
        log_audit_event("test_event", detail="hello")
        events = get_recent_audit_events(10)
        assert len(events) == 1
        assert events[0]["event"] == "test_event"
        assert events[0]["detail"] == "hello"

    def test_log_audit_event_timestamp(self):
        log_audit_event("test_event")
        events = get_recent_audit_events(10)
        assert "timestamp" in events[0]

    def test_audit_event_limit(self):
        for i in range(10):
            log_audit_event("bulk", idx=i)
        events = get_recent_audit_events(5)
        assert len(events) == 5
        assert events[0]["idx"] == 5  # last 5

    def test_audit_stats(self):
        log_audit_event("auth_success")
        log_audit_event("auth_success")
        log_audit_event("auth_failure")
        stats = get_audit_stats()
        assert stats["total_events"] == 3
        assert stats["event_types"]["auth_success"] == 2
        assert stats["event_types"]["auth_failure"] == 1

    def test_audit_stats_empty(self):
        stats = get_audit_stats()
        assert stats["total_events"] == 0

    def test_audit_auth_failure_logged_on_invalid_key(self):
        """Auth failure should be logged when API_KEYS is set and wrong key used."""
        _cleanup_audit()
        with patch.dict(os.environ, {"API_KEYS": "valid-key-123"}):
            # Reset cached keys
            from app.middleware import auth
            auth._api_keys = None
            try:
                res = client.get("/upload", headers={"X-API-Key": "wrong-key"})
                # Should get 403 or 405 (method not allowed if GET on POST-only route)
                events = get_recent_audit_events(100)
                auth_failures = [e for e in events if e["event"] == "auth_failure"]
                assert len(auth_failures) >= 1
            finally:
                auth._api_keys = None
                os.environ.pop("API_KEYS", None)


# ── S16-2: CORS Configuration ──

class TestCORSConfiguration:
    def test_cors_default_origins(self):
        origins = get_cors_origins()
        assert origins == ["*"]

    def test_cors_custom_origins(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com,https://app.example.com"}):
            origins = get_cors_origins()
            assert "https://example.com" in origins
            assert "https://app.example.com" in origins
            assert len(origins) == 2

    def test_cors_headers_in_response(self):
        res = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # CORS should respond (either 200 or 400, but headers should be present)
        assert res.status_code in (200, 400)

    def test_cors_allow_origin_header(self):
        res = client.get("/health", headers={"Origin": "http://localhost:3000"})
        # With allow_origins=["*"], should have access-control-allow-origin
        assert "access-control-allow-origin" in res.headers


# ── S16-3: Request Body Size Limiting ──

class TestBodySizeLimit:
    def test_normal_request_passes(self):
        res = client.get("/health")
        assert res.status_code == 200

    def test_body_limit_middleware_exists(self):
        from app.middleware.body_limit import BodyLimitMiddleware, API_BODY_LIMIT
        assert API_BODY_LIMIT == 1 * 1024 * 1024  # 1 MB

    def test_large_content_length_rejected(self):
        """Request with huge Content-Length on non-upload route should be rejected."""
        res = client.post(
            "/feedback",
            headers={"Content-Length": "999999999"},
            content="x",
        )
        assert res.status_code in (413, 422)  # 413 from middleware or 422 from validation

    def test_upload_route_has_higher_limit(self):
        from app.middleware.body_limit import _UPLOAD_PATHS
        assert "/upload" in _UPLOAD_PATHS


# ── S16-4: Brute Force Protection ──

class TestBruteForceProtection:
    def setup_method(self):
        _cleanup_brute_force()

    def teardown_method(self):
        _cleanup_brute_force()

    def test_record_auth_failure(self):
        record_auth_failure("192.168.1.1")
        assert not is_ip_blocked("192.168.1.1")

    def test_ip_blocked_after_max_failures(self):
        for _ in range(MAX_FAILURES):
            record_auth_failure("10.0.0.1")
        assert is_ip_blocked("10.0.0.1")

    def test_unblocked_ip(self):
        assert not is_ip_blocked("10.0.0.2")

    def test_brute_force_stats(self):
        for _ in range(MAX_FAILURES):
            record_auth_failure("10.0.0.3")
        stats = get_brute_force_stats()
        assert stats["currently_blocked"] >= 1
        assert stats["tracked_ips"] >= 1
        assert stats["max_failures"] == MAX_FAILURES

    def test_blocked_ip_gets_429(self):
        """A blocked IP should receive 429 from BruteForceMiddleware."""
        with patch("app.middleware.brute_force.is_ip_blocked", return_value=True):
            # The test client's IP won't match, so we patch
            res = client.get("/health")
            # With patched is_ip_blocked=True, should get 429
            assert res.status_code == 429


# ── S16-5: File Quarantine ──

class TestFileQuarantine:
    def setup_method(self):
        _cleanup_audit()

    def teardown_method(self):
        _cleanup_audit()
        # Clean up quarantine files
        if QUARANTINE_DIR.exists():
            for f in QUARANTINE_DIR.iterdir():
                if f.name.startswith("test_quarantine"):
                    f.unlink(missing_ok=True)

    def test_quarantine_file(self):
        QUARANTINE_DIR.mkdir(exist_ok=True)
        tmp = QUARANTINE_DIR.parent / "test_quarantine_file.bin"
        tmp.write_bytes(b"suspicious content")
        result = quarantine_file(tmp, reason="test")
        assert result is not None
        assert result.exists()
        assert not tmp.exists()
        # Cleanup
        result.unlink(missing_ok=True)

    def test_quarantine_audit_event(self):
        QUARANTINE_DIR.mkdir(exist_ok=True)
        tmp = QUARANTINE_DIR.parent / "test_quarantine_audit.bin"
        tmp.write_bytes(b"data")
        quarantine_file(tmp, reason="magic_bytes_mismatch")
        events = get_recent_audit_events(10)
        quarantine_events = [e for e in events if e["event"] == "file_quarantined"]
        assert len(quarantine_events) >= 1
        # Cleanup
        (QUARANTINE_DIR / "test_quarantine_audit.bin").unlink(missing_ok=True)

    def test_quarantine_count(self):
        count = get_quarantine_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_quarantine_nonexistent_file(self):
        result = quarantine_file(Path("/nonexistent/file.bin"), reason="test")
        assert result is None


# ── S16-6: Security Audit Endpoint ──

class TestSecurityAuditEndpoint:
    def setup_method(self):
        _cleanup_audit()
        _cleanup_brute_force()

    def teardown_method(self):
        _cleanup_audit()
        _cleanup_brute_force()

    def test_audit_endpoint_returns_200(self):
        res = client.get("/security/audit")
        assert res.status_code == 200

    def test_audit_endpoint_structure(self):
        res = client.get("/security/audit")
        data = res.json()
        assert "events" in data
        assert "stats" in data
        assert "brute_force" in data

    def test_audit_endpoint_with_limit(self):
        for i in range(10):
            log_audit_event("test", idx=i)
        res = client.get("/security/audit?limit=3")
        data = res.json()
        assert len(data["events"]) == 3

    def test_audit_endpoint_records_access(self):
        _cleanup_audit()
        res = client.get("/security/audit")
        events = get_recent_audit_events(10)
        access_events = [e for e in events if e["event"] == "audit_accessed"]
        assert len(access_events) >= 1

    def test_audit_endpoint_with_api_key_required(self):
        """When API keys are configured, audit endpoint requires valid key."""
        with patch.dict(os.environ, {"API_KEYS": "secret-key-abc"}):
            from app.middleware import auth
            auth._api_keys = None
            try:
                # No key - should be forbidden
                res = client.get("/security/audit")
                assert res.status_code == 403

                # Valid key - should work
                res = client.get("/security/audit", headers={"X-API-Key": "secret-key-abc"})
                assert res.status_code == 200
            finally:
                auth._api_keys = None
                os.environ.pop("API_KEYS", None)

    def test_audit_endpoint_brute_force_stats(self):
        for _ in range(MAX_FAILURES):
            record_auth_failure("10.0.0.99")
        res = client.get("/security/audit")
        data = res.json()
        assert data["brute_force"]["currently_blocked"] >= 1


# ── S16-7: Integration Tests ──

class TestSecurityIntegration:
    def test_security_route_registered(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        assert "/security/audit" in paths

    def test_cors_middleware_active(self):
        """CORS middleware should add headers on cross-origin requests."""
        res = client.get("/health", headers={"Origin": "http://example.com"})
        assert "access-control-allow-origin" in res.headers

    def test_body_limit_and_cors_coexist(self):
        """Both middleware should work together without conflicts."""
        res = client.get("/health", headers={"Origin": "http://example.com"})
        assert res.status_code == 200
        assert "access-control-allow-origin" in res.headers

    def test_audit_service_importable(self):
        from app.services.audit import log_audit_event, get_recent_audit_events, get_audit_stats
        assert callable(log_audit_event)
        assert callable(get_recent_audit_events)
        assert callable(get_audit_stats)

    def test_quarantine_service_importable(self):
        from app.services.quarantine import quarantine_file, get_quarantine_count
        assert callable(quarantine_file)
        assert callable(get_quarantine_count)

    def test_brute_force_middleware_importable(self):
        from app.middleware.brute_force import BruteForceMiddleware
        assert BruteForceMiddleware is not None

"""Phase Lumen L64 — Advanced session middleware tests.

Tests secure flag behavior and cookie re-issue prevention.
-- Shield (Security Engineer)
"""

from fastapi.testclient import TestClient

from app.main import app
from app.middleware.session import SESSION_COOKIE


# ======================================================================
# SESSION SECURE FLAG
# ======================================================================


class TestSessionSecureFlag:
    """Test Secure cookie flag based on HTTPS detection."""

    def test_https_forwarded_proto_sets_secure_flag(self):
        """HTTP client with X-Forwarded-Proto: https sets secure flag on cookie."""
        fresh = TestClient(app, base_url="http://testserver")
        res = fresh.get("/tasks", headers={"X-Forwarded-Proto": "https"})
        cookie_header = res.headers.get("set-cookie", "")
        assert SESSION_COOKIE in cookie_header
        assert "secure" in cookie_header.lower()

    def test_plain_http_no_secure_flag(self):
        """Plain HTTP client without forwarded proto lacks secure flag."""
        fresh = TestClient(app, base_url="http://testserver")
        res = fresh.get("/tasks")
        cookie_header = res.headers.get("set-cookie", "")
        assert SESSION_COOKIE in cookie_header
        # The cookie header should NOT contain "secure" (case-insensitive)
        # Split on ; and check individual directives to avoid matching the word
        # inside the cookie value itself
        parts = [p.strip().lower() for p in cookie_header.split(";")]
        assert "secure" not in parts

    def test_https_base_url_sets_secure_flag(self):
        """Direct HTTPS connection sets secure flag."""
        fresh = TestClient(app, base_url="https://testserver")
        res = fresh.get("/tasks")
        cookie_header = res.headers.get("set-cookie", "")
        assert "secure" in cookie_header.lower()


# ======================================================================
# SESSION NOT RESET
# ======================================================================


class TestSessionNotReset:
    """Test that existing sessions don't get new Set-Cookie headers."""

    def test_second_request_no_set_cookie(self):
        """Second request with existing cookie doesn't include Set-Cookie header."""
        c = TestClient(app, base_url="https://testserver")
        # First request: get the session cookie
        res1 = c.get("/tasks")
        assert SESSION_COOKIE in res1.cookies

        # Second request: cookie is sent automatically by TestClient
        res2 = c.get("/tasks")
        # The response should NOT set a new cookie (no Set-Cookie header for session)
        set_cookie = res2.headers.get("set-cookie", "")
        assert SESSION_COOKIE not in set_cookie

    def test_third_request_still_no_set_cookie(self):
        """Third request also doesn't reset the cookie."""
        c = TestClient(app, base_url="https://testserver")
        c.get("/tasks")  # first — sets cookie
        c.get("/tasks")  # second
        res3 = c.get("/tasks")  # third
        set_cookie = res3.headers.get("set-cookie", "")
        assert SESSION_COOKIE not in set_cookie

    def test_different_endpoint_no_reset(self):
        """Navigating to different endpoint doesn't reset session."""
        c = TestClient(app, base_url="https://testserver")
        c.get("/tasks")  # sets cookie
        res2 = c.get("/health")
        set_cookie = res2.headers.get("set-cookie", "")
        assert SESSION_COOKIE not in set_cookie

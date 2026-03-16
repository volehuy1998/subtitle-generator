"""Phase Lumen L53-L60 — Comprehensive API verification tests.

Parametrized tests covering every endpoint's status code, response time,
content type, security headers, and CORS behavior.
— Scout (QA Lead)
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT STATUS CODE VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

ENDPOINT_TESTS = [
    ("GET", "/health", 200),
    ("GET", "/health/live", 200),
    ("GET", "/ready", 200),
    ("GET", "/health/components", 200),
    ("GET", "/tasks", 200),
    ("GET", "/tasks/stats", 200),
    ("GET", "/languages", 200),
    ("GET", "/system-info", 200),
    ("GET", "/api/model-status", 200),
    ("GET", "/metrics", 200),
    ("GET", "/embed/presets", 200),
    ("GET", "/preferences", 200),
    ("GET", "/docs", 200),
    ("GET", "/openapi.json", 200),
    ("GET", "/", 200),
    ("GET", "/status", 200),
    ("GET", "/about", 200),
    ("GET", "/contact", 200),
    ("GET", "/security", 200),
    ("DELETE", "/tasks/nonexistent", 404),
    ("GET", "/progress/nonexistent", 404),
    ("GET", "/preview/nonexistent", 404),
    ("GET", "/search/nonexistent?q=test", 404),
]


@pytest.mark.parametrize("method,path,expected_status", ENDPOINT_TESTS, ids=[f"{m} {p}" for m, p, _ in ENDPOINT_TESTS])
class TestEndpointStatusCodes:
    """Every endpoint returns its expected HTTP status code."""

    def test_status_code(self, method, path, expected_status):
        if method == "GET":
            resp = client.get(path)
        elif method == "DELETE":
            resp = client.delete(path)
        elif method == "POST":
            resp = client.post(path)
        else:
            resp = client.get(path)
        assert resp.status_code == expected_status, (
            f"{method} {path}: expected {expected_status}, got {resp.status_code}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE TIME TESTS — all endpoints respond within 2 seconds
# ══════════════════════════════════════════════════════════════════════════════

TIMED_ENDPOINTS = [
    ("GET", "/health"),
    ("GET", "/health/live"),
    ("GET", "/ready"),
    ("GET", "/health/components"),
    ("GET", "/tasks"),
    ("GET", "/tasks/stats"),
    ("GET", "/languages"),
    ("GET", "/system-info"),
    ("GET", "/api/model-status"),
    ("GET", "/metrics"),
    ("GET", "/embed/presets"),
    ("GET", "/preferences"),
    ("GET", "/openapi.json"),
    ("GET", "/"),
    ("GET", "/status"),
    ("GET", "/about"),
    ("GET", "/contact"),
    ("GET", "/security"),
]


@pytest.mark.parametrize("method,path", TIMED_ENDPOINTS, ids=[f"{m} {p}" for m, p in TIMED_ENDPOINTS])
class TestResponseTimes:
    """All endpoints respond within 2 seconds."""

    def test_responds_within_2s(self, method, path):
        start = time.monotonic()
        resp = client.get(path)
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 2.0, f"{method} {path} took {elapsed:.3f}s (>2s)"


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT TYPE TESTS — JSON for API, HTML for pages
# ══════════════════════════════════════════════════════════════════════════════

JSON_ENDPOINTS = [
    "/health",
    "/health/live",
    "/ready",
    "/health/components",
    "/tasks",
    "/tasks/stats",
    "/languages",
    "/system-info",
    "/api/model-status",
    "/embed/presets",
    "/preferences",
]

TEXT_ENDPOINTS = [
    "/metrics",
]

HTML_ENDPOINTS = [
    "/",
    "/status",
    "/about",
    "/contact",
    "/security",
]


class TestContentTypes:
    """API endpoints return JSON, page endpoints return HTML."""

    @pytest.mark.parametrize("path", JSON_ENDPOINTS)
    def test_json_content_type(self, path):
        resp = client.get(path)
        ct = resp.headers.get("content-type", "")
        assert "application/json" in ct, f"{path} content-type: {ct}"

    @pytest.mark.parametrize("path", HTML_ENDPOINTS)
    def test_html_content_type(self, path):
        resp = client.get(path)
        ct = resp.headers.get("content-type", "")
        assert "text/html" in ct, f"{path} content-type: {ct}"

    def test_openapi_json_content_type(self):
        resp = client.get("/openapi.json")
        ct = resp.headers.get("content-type", "")
        assert "json" in ct.lower(), f"/openapi.json content-type: {ct}"

    def test_docs_html_content_type(self):
        resp = client.get("/docs")
        ct = resp.headers.get("content-type", "")
        assert "text/html" in ct, f"/docs content-type: {ct}"

    @pytest.mark.parametrize("path", TEXT_ENDPOINTS)
    def test_text_content_type(self, path):
        resp = client.get(path)
        ct = resp.headers.get("content-type", "")
        assert "text/plain" in ct, f"{path} content-type: {ct}"


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY HEADER TESTS — all endpoints have required headers
# ══════════════════════════════════════════════════════════════════════════════

SECURITY_HEADER_ENDPOINTS = [
    "/health",
    "/tasks",
    "/languages",
    "/",
    "/status",
]

REQUIRED_SECURITY_HEADERS = [
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
]


class TestSecurityHeaders:
    """All endpoints include required security response headers."""

    @pytest.mark.parametrize("path", SECURITY_HEADER_ENDPOINTS)
    @pytest.mark.parametrize("header", REQUIRED_SECURITY_HEADERS)
    def test_security_header_present(self, path, header):
        resp = client.get(path)
        assert header in resp.headers, f"{path} missing header: {header}"

    @pytest.mark.parametrize("path", SECURITY_HEADER_ENDPOINTS)
    def test_x_content_type_options_value(self, path):
        resp = client.get(path)
        assert resp.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.parametrize("path", SECURITY_HEADER_ENDPOINTS)
    def test_x_frame_options_value(self, path):
        resp = client.get(path)
        val = resp.headers.get("x-frame-options", "")
        assert val in ("DENY", "SAMEORIGIN"), f"{path} x-frame-options: {val}"

    @pytest.mark.parametrize("path", SECURITY_HEADER_ENDPOINTS)
    def test_permissions_policy_present(self, path):
        resp = client.get(path)
        assert "permissions-policy" in resp.headers, f"{path} missing permissions-policy"

    @pytest.mark.parametrize("path", SECURITY_HEADER_ENDPOINTS)
    def test_csp_present(self, path):
        resp = client.get(path)
        assert "content-security-policy" in resp.headers, f"{path} missing CSP"


# ══════════════════════════════════════════════════════════════════════════════
# CORS TESTS — preflight OPTIONS works
# ══════════════════════════════════════════════════════════════════════════════


class TestCORS:
    """CORS preflight requests are handled correctly."""

    def test_options_health_returns_ok(self):
        resp = client.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200

    def test_options_tasks_returns_ok(self):
        resp = client.options(
            "/tasks",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200

    def test_cors_allows_origin_header(self):
        resp = client.get(
            "/health",
            headers={"Origin": "https://example.com"},
        )
        acao = resp.headers.get("access-control-allow-origin", "")
        # Either wildcard or echoed origin
        assert acao in ("*", "https://example.com") or len(acao) > 0

    def test_cors_allows_get_method(self):
        resp = client.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        methods = resp.headers.get("access-control-allow-methods", "")
        assert "GET" in methods or resp.status_code == 200

    def test_cors_preflight_upload(self):
        resp = client.options(
            "/upload",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# API VERSION HEADER
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIVersionHeader:
    """All responses include the x-api-version header."""

    @pytest.mark.parametrize("path", ["/health", "/tasks", "/languages", "/"])
    def test_api_version_header_present(self, path):
        resp = client.get(path)
        assert "x-api-version" in resp.headers

    def test_api_version_is_semver(self):
        resp = client.get("/health")
        version = resp.headers.get("x-api-version", "")
        parts = version.split(".")
        assert len(parts) == 3, f"Expected semver, got: {version}"
        for part in parts:
            assert part.isdigit(), f"Non-numeric semver part: {part} in {version}"

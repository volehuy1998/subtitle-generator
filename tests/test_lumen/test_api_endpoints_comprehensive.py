"""Phase Lumen L20 — Comprehensive API endpoint tests.

Tests every API endpoint exists and returns expected status codes,
validates response times, content types, and error response structure.
— Scout (QA Lead)
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT STATUS CODE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

ENDPOINTS = [
    ("GET", "/", 200),
    ("GET", "/health", 200),
    ("GET", "/health/live", 200),
    ("GET", "/ready", 200),
    ("GET", "/metrics", 200),
    ("GET", "/system-info", 200),
    ("GET", "/api/model-status", 200),
    ("GET", "/languages", 200),
    ("GET", "/tasks", 200),
    ("GET", "/tasks/stats", 200),
    ("GET", "/docs", 200),
    ("GET", "/redoc", 200),
    ("GET", "/openapi.json", 200),
    ("GET", "/status", 200),
    ("GET", "/about", 200),
    ("GET", "/security", 200),
    ("GET", "/contact", 200),
    ("GET", "/embed/presets", 200),
    ("GET", "/progress/nonexistent", 404),
    ("POST", "/cancel/nonexistent", 404),
    ("DELETE", "/tasks/nonexistent", 404),
    ("GET", "/preview/nonexistent", 404),
    ("GET", "/download/nonexistent/all", 404),
]


class TestEndpointStatusCodes:
    """Every API endpoint returns the expected HTTP status code."""

    @pytest.mark.parametrize("method,path,expected", ENDPOINTS, ids=[f"{m} {p}" for m, p, _ in ENDPOINTS])
    def test_endpoint_status_code(self, method, path, expected):
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path)
        elif method == "DELETE":
            res = client.delete(path)
        else:
            pytest.fail(f"Unsupported method: {method}")
        assert res.status_code == expected, f"{method} {path} returned {res.status_code}, expected {expected}"


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE TIME VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

TIMEOUT_ENDPOINTS = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/health/live"),
    ("GET", "/ready"),
    ("GET", "/metrics"),
    ("GET", "/system-info"),
    ("GET", "/languages"),
    ("GET", "/tasks"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/embed/presets"),
]


class TestEndpointResponseTime:
    """All endpoints respond within 5 seconds (no hangs)."""

    @pytest.mark.parametrize("method,path", TIMEOUT_ENDPOINTS, ids=[f"{m} {p}" for m, p in TIMEOUT_ENDPOINTS])
    def test_endpoint_responds_within_5_seconds(self, method, path):
        start = time.monotonic()
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path)
        else:
            pytest.fail(f"Unsupported method: {method}")
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"{method} {path} took {elapsed:.2f}s (> 5s limit)"
        assert res.status_code in (200, 201, 301, 302, 307, 308, 404)


# ══════════════════════════════════════════════════════════════════════════════
# JSON CONTENT-TYPE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

JSON_ENDPOINTS = [
    "/health",
    "/health/live",
    "/ready",
    "/system-info",
    "/api/model-status",
    "/languages",
    "/tasks",
    "/tasks/stats",
    "/openapi.json",
    "/embed/presets",
]


class TestJSONContentType:
    """JSON endpoints return proper Content-Type header."""

    @pytest.mark.parametrize("path", JSON_ENDPOINTS)
    def test_json_content_type(self, path):
        res = client.get(path)
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct, f"GET {path} Content-Type is '{ct}', expected application/json"


# ══════════════════════════════════════════════════════════════════════════════
# ERROR RESPONSE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

ERROR_ENDPOINTS = [
    ("GET", "/progress/nonexistent", 404),
    ("POST", "/cancel/nonexistent", 404),
    ("DELETE", "/tasks/nonexistent", 404),
    ("GET", "/preview/nonexistent", 404),
    ("GET", "/download/nonexistent/all", 404),
]


class TestErrorResponseStructure:
    """Error responses include a 'detail' key in JSON body."""

    @pytest.mark.parametrize("method,path,expected", ERROR_ENDPOINTS, ids=[f"{m} {p}" for m, p, _ in ERROR_ENDPOINTS])
    def test_error_has_detail_key(self, method, path, expected):
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path)
        elif method == "DELETE":
            res = client.delete(path)
        else:
            pytest.fail(f"Unsupported method: {method}")
        assert res.status_code == expected
        body = res.json()
        assert "detail" in body, f"{method} {path} error response missing 'detail' key: {body}"


# ══════════════════════════════════════════════════════════════════════════════
# HTML CONTENT-TYPE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

HTML_ENDPOINTS = ["/", "/status", "/about", "/security", "/contact"]


class TestHTMLContentType:
    """HTML page endpoints return text/html Content-Type."""

    @pytest.mark.parametrize("path", HTML_ENDPOINTS)
    def test_html_content_type(self, path):
        res = client.get(path)
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct, f"GET {path} Content-Type is '{ct}', expected text/html"


# ══════════════════════════════════════════════════════════════════════════════
# OPENAPI SCHEMA VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestOpenAPISchema:
    """OpenAPI schema endpoint returns valid schema structure."""

    def test_openapi_has_info(self):
        res = client.get("/openapi.json")
        schema = res.json()
        assert "info" in schema

    def test_openapi_has_paths(self):
        res = client.get("/openapi.json")
        schema = res.json()
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_openapi_version_present(self):
        res = client.get("/openapi.json")
        schema = res.json()
        assert "openapi" in schema
        assert schema["openapi"].startswith("3.")

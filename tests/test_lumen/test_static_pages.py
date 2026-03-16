"""Phase Lumen L18 — Static page and public endpoint tests.

Validates all static page endpoints return correct status codes, content types,
and security headers. Tests API documentation, health, metrics, system info,
and language endpoints.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# HTML PAGE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestHTMLPages:
    """Test all static HTML page endpoints return 200."""

    def test_home_page_returns_200(self):
        res = client.get("/")
        assert res.status_code == 200

    def test_status_page_returns_200(self):
        res = client.get("/status")
        assert res.status_code == 200

    def test_about_page_returns_200(self):
        res = client.get("/about")
        assert res.status_code == 200

    def test_security_page_returns_200(self):
        res = client.get("/security")
        assert res.status_code == 200

    def test_contact_page_returns_200(self):
        res = client.get("/contact")
        assert res.status_code == 200

    def test_home_page_content_type_html(self):
        res = client.get("/")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct

    def test_status_page_content_type_html(self):
        res = client.get("/status")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct

    def test_about_page_content_type_html(self):
        res = client.get("/about")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct

    def test_security_page_content_type_html(self):
        res = client.get("/security")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct

    def test_contact_page_content_type_html(self):
        res = client.get("/contact")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct


# ══════════════════════════════════════════════════════════════════════════════
# API DOCUMENTATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIDocEndpoints:
    """Test OpenAPI docs, Swagger UI, and ReDoc."""

    def test_docs_returns_200(self):
        res = client.get("/docs")
        assert res.status_code == 200

    def test_redoc_returns_200(self):
        res = client.get("/redoc")
        assert res.status_code == 200

    def test_openapi_json_returns_200(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200

    def test_openapi_json_is_valid_json(self):
        res = client.get("/openapi.json")
        data = res.json()
        assert isinstance(data, dict)
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_openapi_json_content_type(self):
        res = client.get("/openapi.json")
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH & READINESS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestHealthEndpoints:
    """Test health, readiness, and health stream endpoints."""

    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_has_status_key(self):
        res = client.get("/health")
        data = res.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_has_uptime(self):
        res = client.get("/health")
        data = res.json()
        assert "uptime_sec" in data
        assert isinstance(data["uptime_sec"], (int, float))

    def test_health_returns_json(self):
        res = client.get("/health")
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct

    def test_health_stream_content_type(self):
        """Health stream endpoint should be registered and return SSE media type."""
        # Verify the route exists in the OpenAPI spec
        # (Direct streaming tests hang with sync TestClient, so we verify registration)
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        assert "/health/stream" in paths
        stream_spec = paths["/health/stream"]["get"]
        assert stream_spec is not None

    def test_health_live_returns_200(self):
        res = client.get("/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM & METRICS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSystemEndpoints:
    """Test metrics, system-info, model-status, and languages endpoints."""

    def test_metrics_returns_200(self):
        res = client.get("/metrics")
        assert res.status_code == 200

    def test_metrics_content_type_text(self):
        res = client.get("/metrics")
        ct = res.headers.get("content-type", "")
        assert "text/plain" in ct

    def test_system_info_returns_200(self):
        res = client.get("/system-info")
        assert res.status_code == 200

    def test_system_info_has_expected_keys(self):
        res = client.get("/system-info")
        data = res.json()
        assert "cuda_available" in data
        assert "auto_model" in data

    def test_model_status_returns_200(self):
        res = client.get("/api/model-status")
        assert res.status_code == 200

    def test_model_status_has_models_key(self):
        res = client.get("/api/model-status")
        data = res.json()
        assert "models" in data
        assert "preload" in data

    def test_languages_returns_200(self):
        res = client.get("/languages")
        assert res.status_code == 200

    def test_languages_has_languages_key(self):
        res = client.get("/languages")
        data = res.json()
        assert "languages" in data
        assert len(data["languages"]) > 0

    def test_languages_includes_english(self):
        res = client.get("/languages")
        data = res.json()
        langs = data["languages"]
        # Languages may be a dict (code->name) or a list
        if isinstance(langs, dict):
            assert "en" in langs
        else:
            assert "en" in langs


# ══════════════════════════════════════════════════════════════════════════════
# 404 HANDLING
# ══════════════════════════════════════════════════════════════════════════════


class TestNotFound:
    """Test 404 handling for nonexistent routes."""

    def test_nonexistent_route_returns_404(self):
        res = client.get("/nonexistent-page-xyz")
        assert res.status_code == 404

    def test_nonexistent_api_route_returns_404(self):
        res = client.get("/api/nonexistent-endpoint-xyz")
        assert res.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY HEADERS ON PAGES
# ══════════════════════════════════════════════════════════════════════════════


class TestPageSecurityHeaders:
    """Verify security headers are present on HTML page responses."""

    def test_home_has_csp_header(self):
        res = client.get("/")
        assert "content-security-policy" in {k.lower() for k in res.headers.keys()}

    def test_home_has_x_frame_options(self):
        res = client.get("/")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_about_has_csp_header(self):
        res = client.get("/about")
        assert "content-security-policy" in {k.lower() for k in res.headers.keys()}

    def test_health_has_x_content_type_options(self):
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"

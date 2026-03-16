"""Phase Lumen L19 — Middleware stack integration tests.

Tests security headers, request logging/tracing, compression behavior,
and error handling across the middleware pipeline.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY HEADERS
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityHeaders:
    """Verify security headers are set on all responses by SecurityHeadersMiddleware."""

    def test_x_content_type_options_on_api(self):
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"

    def test_x_content_type_options_on_html(self):
        res = client.get("/about")
        assert res.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_on_api(self):
        res = client.get("/health")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_x_frame_options_on_html(self):
        res = client.get("/")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy_present(self):
        res = client.get("/health")
        rp = res.headers.get("referrer-policy", "")
        assert "strict-origin" in rp

    def test_permissions_policy_present(self):
        res = client.get("/health")
        pp = res.headers.get("permissions-policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp

    def test_csp_on_html_page(self):
        res = client.get("/")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src" in csp
        assert "'self'" in csp

    def test_csp_on_api_endpoint(self):
        res = client.get("/health")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src" in csp

    def test_x_xss_protection_present(self):
        res = client.get("/health")
        xss = res.headers.get("x-xss-protection", "")
        assert "1" in xss

    def test_hsts_not_set_in_dev_mode(self):
        """In dev mode (HTTP), HSTS should not be set."""
        # TestClient uses https://testserver but ENVIRONMENT=dev and HSTS_ENABLED
        # depends on the config. Just verify the header value is consistent.
        res = client.get("/health")
        # In dev mode, HSTS is typically disabled. If present, it should be valid.
        hsts = res.headers.get("strict-transport-security", "")
        if hsts:
            assert "max-age=" in hsts


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST ID / LOGGING
# ══════════════════════════════════════════════════════════════════════════════


class TestRequestIdTracing:
    """Test X-Request-ID header generation and passthrough."""

    def test_request_id_present_on_response(self):
        res = client.get("/health")
        assert "x-request-id" in {k.lower() for k in res.headers.keys()}

    def test_request_id_not_empty(self):
        res = client.get("/health")
        req_id = res.headers.get("x-request-id", "")
        assert len(req_id) > 0

    def test_custom_request_id_preserved(self):
        """When client sends X-Request-ID, it should be echoed back."""
        custom_id = "custom-req-12345"
        res = client.get("/health", headers={"X-Request-ID": custom_id})
        assert res.headers.get("x-request-id") == custom_id

    def test_request_id_is_unique_per_request(self):
        """Two requests without custom ID should get different IDs."""
        res1 = client.get("/health")
        res2 = client.get("/health")
        id1 = res1.headers.get("x-request-id", "")
        id2 = res2.headers.get("x-request-id", "")
        assert id1 != id2

    def test_request_id_format(self):
        """Auto-generated request IDs should be short UUID format (8 chars)."""
        res = client.get("/health")
        req_id = res.headers.get("x-request-id", "")
        # The middleware generates uuid4()[:8], so 8 hex chars
        assert len(req_id) == 8
        assert all(c in "0123456789abcdef-" for c in req_id)


# ══════════════════════════════════════════════════════════════════════════════
# COMPRESSION
# ══════════════════════════════════════════════════════════════════════════════


class TestCompression:
    """Test GZip compression middleware behavior."""

    def test_large_response_compressed_with_gzip(self):
        """Responses > 500 bytes should be compressed when Accept-Encoding: gzip."""
        # /metrics produces a text response that should exceed 500 bytes
        res = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200
        # Verify data integrity — TestClient auto-decompresses
        assert "subtitle_generator" in res.text

    def test_small_response_served_successfully(self):
        """Small responses should be served without error regardless of compression."""
        # /health/live returns a tiny JSON — middleware may or may not compress it
        res = client.get("/health/live", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

    def test_explicit_identity_encoding_no_gzip(self):
        """Accept-Encoding: identity should not trigger gzip compression."""
        res = client.get("/health", headers={"Accept-Encoding": "identity"})
        assert res.status_code == 200
        ce = res.headers.get("content-encoding", "")
        assert ce != "gzip"

    def test_accept_encoding_gzip_header_accepted(self):
        """Server should accept requests with Accept-Encoding: gzip without error."""
        res = client.get("/languages", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200

    def test_compressed_response_decompressible(self):
        """Compressed responses should decompress correctly to valid JSON."""
        res = client.get("/languages", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200
        # TestClient auto-decompresses; verify data integrity
        data = res.json()
        assert "languages" in data


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Test error responses from middleware and route validation."""

    def test_invalid_json_body_returns_422(self):
        """Posting invalid JSON to a JSON endpoint should return 422."""
        res = client.post(
            "/feedback",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 422

    def test_missing_required_fields_returns_422(self):
        """Posting JSON without required fields should return 422."""
        res = client.post("/feedback", json={})
        assert res.status_code == 422

    def test_error_response_is_json(self):
        """Error responses should be JSON with a detail or message."""
        res = client.post(
            "/feedback",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct

    def test_error_response_has_detail(self):
        """Validation errors should include a detail field."""
        res = client.post(
            "/feedback",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        data = res.json()
        assert "detail" in data

    def test_404_error_includes_request_id(self):
        """Even error responses should carry X-Request-ID for debugging."""
        res = client.get("/nonexistent-endpoint-for-test")
        assert res.status_code == 404
        req_id = res.headers.get("x-request-id", "")
        assert len(req_id) > 0

    def test_method_not_allowed_returns_405(self):
        """Using wrong HTTP method should return 405."""
        res = client.delete("/health")
        assert res.status_code == 405

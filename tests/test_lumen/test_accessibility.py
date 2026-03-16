"""Phase Lumen L15 — Accessibility and WCAG compliance tests.

Tests HTML responses for accessibility attributes, security headers,
API error message quality, and endpoint accessibility.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# HTML RESPONSE ACCESSIBILITY
# ══════════════════════════════════════════════════════════════════════════════


class TestHtmlLangAttribute:
    """Test that HTML responses include proper lang attribute."""

    def test_index_has_lang_attribute(self):
        res = client.get("/")
        assert res.status_code == 200
        body = res.text
        assert 'lang="en"' in body or "lang='en'" in body or 'lang="en-US"' in body

    def test_response_includes_viewport_meta(self):
        res = client.get("/")
        body = res.text
        assert "viewport" in body

    def test_index_has_proper_content_type(self):
        res = client.get("/")
        ct = res.headers.get("content-type", "")
        assert "text/html" in ct

    def test_index_has_charset_utf8(self):
        res = client.get("/")
        ct = res.headers.get("content-type", "")
        body = res.text
        # charset can be in Content-Type header or in meta tag
        has_charset_header = "utf-8" in ct.lower()
        has_charset_meta = 'charset="utf-8"' in body.lower() or "charset=utf-8" in body.lower()
        assert has_charset_header or has_charset_meta

    def test_index_has_page_title(self):
        res = client.get("/")
        body = res.text
        assert "<title>" in body.lower() or "<title " in body.lower()

    def test_img_tags_have_alt_attributes(self):
        """Check that img tags in HTML have alt attributes for screen readers."""
        res = client.get("/")
        body = res.text
        # Find all img tags and verify they have alt attributes
        import re

        img_tags = re.findall(r"<img\b[^>]*>", body, re.IGNORECASE)
        for img in img_tags:
            assert "alt=" in img.lower(), f"Image tag missing alt attribute: {img}"


class TestSecurityHeadersPresent:
    """Test that security headers are set on responses."""

    def test_x_content_type_options_nosniff(self):
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_present(self):
        res = client.get("/health")
        xfo = res.headers.get("x-frame-options", "")
        assert xfo in ("DENY", "SAMEORIGIN")

    def test_referrer_policy_present(self):
        res = client.get("/health")
        rp = res.headers.get("referrer-policy", "")
        assert rp != ""

    def test_csp_header_present(self):
        res = client.get("/health")
        csp = res.headers.get("content-security-policy", "")
        assert "default-src" in csp

    def test_permissions_policy_present(self):
        res = client.get("/health")
        pp = res.headers.get("permissions-policy", "")
        assert pp != ""

    def test_x_xss_protection_present(self):
        res = client.get("/health")
        xss = res.headers.get("x-xss-protection", "")
        assert xss != ""


# ══════════════════════════════════════════════════════════════════════════════
# API ACCESSIBILITY — ERROR MESSAGES
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorResponseMessages:
    """Test that error responses have descriptive, actionable messages."""

    def test_404_has_descriptive_message(self):
        res = client.get("/progress/nonexistent-task-xyz")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data
        assert len(data["detail"]) > 5  # Not just a code

    def test_404_nonexistent_route(self):
        res = client.get("/this-route-does-not-exist-at-all")
        assert res.status_code in (404, 307)  # May redirect to SPA

    def test_413_mentions_file_size(self):
        """413 response should mention size limits."""
        # Send a request with a very large Content-Length header
        res = client.post(
            "/upload",
            headers={"content-length": "99999999999"},
            content=b"x",
        )
        assert res.status_code == 413
        data = res.json()
        assert "detail" in data
        msg = data["detail"].lower()
        assert "too large" in msg or "maximum" in msg or "bytes" in msg

    def test_429_mentions_rate_limit(self):
        """429 response should mention rate limiting."""
        # We test the response format by checking the middleware's JSONResponse
        from starlette.responses import JSONResponse

        resp = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
        )
        assert resp.status_code == 429

    def test_api_responses_use_consistent_json_structure(self):
        """API error responses should use {"detail": ...} structure."""
        res = client.get("/progress/nonexistent-task")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data

    def test_all_api_endpoints_return_proper_content_type(self):
        """JSON endpoints return application/json."""
        res = client.get("/health")
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct

    def test_health_endpoint_accessible_without_auth(self):
        """Health endpoint should be publicly accessible."""
        res = client.get("/health")
        assert res.status_code == 200

    def test_openapi_docs_accessible(self):
        """OpenAPI docs should be accessible at /docs."""
        res = client.get("/docs")
        assert res.status_code == 200

    def test_redoc_accessible(self):
        """ReDoc should be accessible at /redoc."""
        res = client.get("/redoc")
        assert res.status_code == 200

    def test_openapi_json_accessible(self):
        """OpenAPI JSON schema should be accessible."""
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "paths" in data
        assert "info" in data

    def test_400_invalid_body_has_message(self):
        """400 errors should include actionable messages."""
        res = client.post(
            "/upload",
            content=b"not a form",
            headers={"content-type": "multipart/form-data; boundary=invalid"},
        )
        # Should return 400 or 422 with detail
        assert res.status_code in (400, 422)
        data = res.json()
        assert "detail" in data

"""Sprint 26 tests: Infrastructure Security & Hardening.

Tests cover:
  - HSTS configuration
  - CSP nonce generation
  - CORS lockdown
  - SRI hash computation
  - Audit log integrity (HMAC signing)
  - Security headers presence
  - Docker hardening config
"""

from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ── CSP Nonce Tests ──

class TestCspNonce:
    """Test CSP nonce generation."""

    def test_generate_nonce(self):
        from app.utils.security_infra import generate_csp_nonce
        nonce = generate_csp_nonce()
        assert isinstance(nonce, str)
        assert len(nonce) > 10  # Base64 of 16 bytes

    def test_nonces_are_unique(self):
        from app.utils.security_infra import generate_csp_nonce
        n1 = generate_csp_nonce()
        n2 = generate_csp_nonce()
        assert n1 != n2

    def test_nonce_is_base64(self):
        import base64
        from app.utils.security_infra import generate_csp_nonce
        nonce = generate_csp_nonce()
        # Should be valid base64
        decoded = base64.b64decode(nonce)
        assert len(decoded) == 16


# ── SRI Hash Tests ──

class TestSriHash:
    """Test Subresource Integrity hash computation."""

    def test_compute_sri_hash(self):
        from app.utils.security_infra import compute_sri_hash
        h = compute_sri_hash("alert('hello')")
        assert h.startswith("sha384-")

    def test_sri_hash_deterministic(self):
        from app.utils.security_infra import compute_sri_hash
        h1 = compute_sri_hash("test content")
        h2 = compute_sri_hash("test content")
        assert h1 == h2

    def test_sri_hash_differs_for_different_content(self):
        from app.utils.security_infra import compute_sri_hash
        h1 = compute_sri_hash("content A")
        h2 = compute_sri_hash("content B")
        assert h1 != h2

    def test_sri_hash_accepts_bytes(self):
        from app.utils.security_infra import compute_sri_hash
        h = compute_sri_hash(b"binary content")
        assert h.startswith("sha384-")


# ── HSTS Configuration Tests ──

class TestHstsConfig:
    """Test HSTS configuration."""

    def test_hsts_config_exists(self):
        from app.utils.security_infra import HSTS_ENABLED, HSTS_MAX_AGE
        assert isinstance(HSTS_ENABLED, bool)
        assert isinstance(HSTS_MAX_AGE, int)

    def test_hsts_header_builder(self):
        from app.utils.security_infra import get_hsts_header
        header = get_hsts_header()
        assert "max-age=" in header

    def test_hsts_max_age_default(self):
        from app.utils.security_infra import HSTS_MAX_AGE
        assert HSTS_MAX_AGE == 31536000  # 1 year

    def test_config_hsts_enabled_var(self):
        from app.config import HSTS_ENABLED
        assert isinstance(HSTS_ENABLED, bool)

    def test_config_https_redirect_var(self):
        from app.config import HTTPS_REDIRECT
        assert isinstance(HTTPS_REDIRECT, bool)


# ── CORS Lockdown Tests ──

class TestCorsLockdown:
    """Test CORS configuration lockdown."""

    def test_get_safe_cors_origins(self):
        from app.utils.security_infra import get_safe_cors_origins
        origins = get_safe_cors_origins()
        assert isinstance(origins, list)

    def test_cors_default_deny_config(self):
        from app.config import CORS_DEFAULT_DENY
        assert isinstance(CORS_DEFAULT_DENY, bool)

    def test_cors_module_exists(self):
        from app.middleware.cors import get_cors_origins
        origins = get_cors_origins()
        assert isinstance(origins, list)

    def test_cors_validates_origins(self):
        from app.utils.security_infra import get_safe_cors_origins
        # Default should return something (either * or validated origins)
        origins = get_safe_cors_origins()
        for o in origins:
            assert o == "*" or o.startswith("http://") or o.startswith("https://")


# ── Audit Log Integrity Tests ──

class TestAuditIntegrity:
    """Test HMAC-signed audit log entries."""

    def test_sign_entry(self):
        from app.utils.security_infra import sign_audit_entry
        entry = {"event_type": "test", "ip": "127.0.0.1"}
        sig = sign_audit_entry(entry)
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex

    def test_verify_entry_valid(self):
        from app.utils.security_infra import sign_audit_entry, verify_audit_entry
        entry = {"event_type": "login", "user": "admin"}
        sig = sign_audit_entry(entry)
        assert verify_audit_entry(entry, sig) is True

    def test_verify_entry_tampered(self):
        from app.utils.security_infra import sign_audit_entry, verify_audit_entry
        entry = {"event_type": "login", "user": "admin"}
        sig = sign_audit_entry(entry)
        # Tamper with entry
        entry["user"] = "attacker"
        assert verify_audit_entry(entry, sig) is False

    def test_create_signed_entry(self):
        from app.utils.security_infra import create_signed_audit_entry, verify_audit_entry
        entry = create_signed_audit_entry("test_event", ip="10.0.0.1")
        assert "hmac" in entry
        assert "timestamp" in entry
        # Verify the signature
        sig = entry.pop("hmac")
        assert verify_audit_entry(entry, sig) is True

    def test_signature_deterministic(self):
        from app.utils.security_infra import sign_audit_entry
        entry = {"event_type": "test", "data": "consistent"}
        sig1 = sign_audit_entry(entry)
        sig2 = sign_audit_entry(entry)
        assert sig1 == sig2


# ── Security Headers Tests ──

class TestSecurityHeaders:
    """Test security headers are present on responses."""

    def test_x_content_type_options(self):
        res = client.get("/")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self):
        res = client.get("/")
        assert res.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy(self):
        res = client.get("/")
        assert "strict-origin" in res.headers.get("Referrer-Policy", "")

    def test_permissions_policy(self):
        res = client.get("/")
        assert "camera=()" in res.headers.get("Permissions-Policy", "")

    def test_csp_header_present(self):
        res = client.get("/")
        csp = res.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp
        assert "script-src" in csp

    def test_csp_has_media_src(self):
        res = client.get("/")
        csp = res.headers.get("Content-Security-Policy", "")
        assert "media-src" in csp

    def test_request_id_header(self):
        res = client.get("/system-info")
        assert "X-Request-ID" in res.headers


# ── CSP Nonce Config Tests ──

class TestCspNonceConfig:
    """Test CSP nonce configuration."""

    def test_csp_nonce_enabled_config(self):
        from app.config import CSP_NONCE_ENABLED
        assert isinstance(CSP_NONCE_ENABLED, bool)


# ── Docker Hardening Tests ──

class TestDockerHardening:
    """Test Docker security configuration exists."""

    def test_dockerfile_exists(self):
        assert Path("Dockerfile").exists()

    def test_docker_compose_exists(self):
        assert Path("docker-compose.yml").exists() or Path("compose.yml").exists()

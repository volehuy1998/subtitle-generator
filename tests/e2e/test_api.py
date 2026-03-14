"""E2E tests: API endpoints via HTTP (no browser needed)."""

import ssl
import json
import urllib.request

BASE_URL = "https://openlabs.club"
CTX = ssl.create_default_context()


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}", context=CTX, timeout=10) as r:
        return json.loads(r.read())


def test_health_endpoint():
    d = _get("/health")
    assert "status" in d
    assert d["uptime_sec"] > 0


def test_health_live():
    d = _get("/health/live")
    assert "status" in d


def test_system_status():
    d = _get("/api/status")
    assert "status" in d
    assert "db_ok" in d
    assert d["db_ok"] is True, "Database should be connected"


def test_status_page_api():
    d = _get("/api/status/page")
    assert "components" in d or "status" in d


def test_analytics_summary():
    d = _get("/analytics/summary")
    assert isinstance(d, dict)


def test_system_info():
    d = _get("/system-info")
    assert "cuda_available" in d


def test_openapi_spec():
    d = _get("/openapi.json")
    assert d.get("openapi", "").startswith("3.")
    assert "paths" in d


def test_http_to_https_redirect():
    import http.client

    conn = http.client.HTTPConnection("openlabs.club", 80, timeout=10)
    conn.request("GET", "/", headers={"Host": "openlabs.club"})
    r = conn.getresponse()
    assert r.status in (301, 302, 307, 308), f"Expected redirect, got {r.status}"
    location = r.getheader("location", "")
    assert location.startswith("https://"), f"Expected https redirect, got: {location}"
    conn.close()


def test_tls_certificate():
    import socket

    ctx = ssl.create_default_context()
    with socket.create_connection(("openlabs.club", 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname="openlabs.club") as ssock:
            cert = ssock.getpeercert()
            issuer = dict(x[0] for x in cert.get("issuer", []))
            assert "Let's Encrypt" in issuer.get("organizationName", ""), "Expected Let's Encrypt cert"

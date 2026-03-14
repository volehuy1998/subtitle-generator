#!/usr/bin/env python3
"""Automated interface check using Playwright headless browser."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://openlabs.club"
results = []


def log(msg):
    print(msg, flush=True)


def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed, detail))
    mark = "[OK]" if passed else "[!!]"
    log(f"  {mark} {name}: {status}" + (f" -- {detail}" if detail else ""))


log("=" * 62)
log("  SUBTITLE GENERATOR - AUTOMATED INTERFACE CHECK")
log(f"  Target: {BASE_URL}")
log("=" * 62)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    log("ERROR: playwright not installed. Run: pip install playwright")
    sys.exit(1)

with sync_playwright() as pw:
    log("\n[1] Browser launch...")
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    context = browser.new_context(ignore_https_errors=False)
    page = context.new_page()
    js_errors = []
    page.on("pageerror", lambda err: js_errors.append(str(err)))

    # --- Homepage ---
    log("\n[2] Homepage check...")
    try:
        resp = page.goto(BASE_URL, timeout=15000, wait_until="domcontentloaded")
        record("Homepage loads", resp and resp.ok, f"HTTP {resp.status if resp else 'no response'}")
    except Exception as e:
        record("Homepage loads", False, str(e))

    # React root mounted
    try:
        root_html = page.inner_html("#root")
        record("React root mounted", len(root_html) > 50, f"{len(root_html)} chars")
    except Exception as e:
        record("React root mounted", False, str(e))

    # Key UI elements
    ui_checks = [
        ("Transcribe tab", "button:has-text('Transcribe')"),
        ("Embed Subtitles tab", "button:has-text('Embed Subtitles')"),
        ("Upload area", "input[type='file'], [data-testid='upload'], label[for]"),
        ("App header/nav", "header, nav, [role='banner']"),
    ]
    log("\n[3] UI elements...")
    for label, selector in ui_checks:
        try:
            el = page.query_selector(selector)
            record(label, el is not None)
        except Exception as e:
            record(label, False, str(e))

    # JS errors on homepage
    log("\n[4] JavaScript errors...")
    record(
        "No JS errors (homepage)",
        len(js_errors) == 0,
        f"{len(js_errors)} errors: {js_errors[:2]}" if js_errors else "clean",
    )
    js_errors.clear()

    # Static assets
    log("\n[5] Static assets...")
    try:
        import ssl
        import urllib.request

        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        req = urllib.request.Request(BASE_URL, headers={"User-Agent": "check/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            html = r.read().decode()
        import re

        js_src = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
        css_src = re.findall(r'href=["\']([^"\']*\.css[^"\']*)["\']', html)
        record("JS assets referenced", len(js_src) > 0, f"{len(js_src)} JS file(s)")
        record("CSS assets referenced", len(css_src) > 0, f"{len(css_src)} CSS file(s)")
    except Exception as e:
        record("Static assets check", False, str(e))

    # /status page
    log("\n[6] Status page check...")
    js_errors.clear()
    try:
        resp2 = page.goto(f"{BASE_URL}/status", timeout=15000, wait_until="domcontentloaded")
        record("/status page loads", resp2 and resp2.ok, f"HTTP {resp2.status if resp2 else 'no response'}")
        title = page.title()
        record("Status page title present", bool(title), title)
        root2 = page.inner_html("#root")
        record("Status React root mounted", len(root2) > 50)
    except Exception as e:
        record("/status page", False, str(e))
    record("No JS errors (/status)", len(js_errors) == 0, f"{len(js_errors)} errors" if js_errors else "clean")

    # API endpoints
    log("\n[7] API endpoints...")
    import json

    api_endpoints = [
        ("GET /health", "GET", "/health", 200),
        ("GET /health/live", "GET", "/health/live", 200),
        ("GET /api/status/page", "GET", "/api/status/page", 200),
        ("GET /api/status/commits", "GET", "/api/status/commits", 200),
        ("GET /analytics/summary", "GET", "/analytics/summary", 200),
        ("GET /system-info", "GET", "/system-info", 200),
        ("GET /docs", "GET", "/docs", 200),
        ("GET /openapi.json", "GET", "/openapi.json", 200),
    ]
    for label, method, path, expected in api_endpoints:
        try:
            r = context.request.get(f"{BASE_URL}{path}", timeout=10000)
            record(label, r.status == expected, f"HTTP {r.status}")
        except Exception as e:
            record(label, False, str(e))

    # HTTP -> HTTPS redirect
    log("\n[8] HTTP redirect check...")
    try:
        import http.client
        import socket

        conn = http.client.HTTPConnection("openlabs.club", 80, timeout=10)
        conn.request("GET", "/", headers={"Host": "openlabs.club", "User-Agent": "check/1.0"})
        r = conn.getresponse()
        location = r.getheader("location", "")
        is_redirect = r.status in (301, 302, 307, 308)
        goes_https = location.startswith("https://")
        record("HTTP->HTTPS redirect", is_redirect and goes_https, f"HTTP {r.status}, Location: {location}")
        conn.close()
    except Exception as e:
        record("HTTP->HTTPS redirect", False, str(e))

    # TLS certificate
    log("\n[9] TLS certificate...")
    try:
        import socket
        import ssl

        ctx2 = ssl.create_default_context()
        ctx2.minimum_version = ssl.TLSVersion.TLSv1_2
        with socket.create_connection(("openlabs.club", 443), timeout=10) as sock:
            with ctx2.wrap_socket(sock, server_hostname="openlabs.club") as ssock:
                cert = ssock.getpeercert()
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                not_after = cert.get("notAfter", "?")
                record(
                    "TLS cert valid (no errors)",
                    True,
                    f"Issuer: {issuer.get('organizationName', '?')}, Expires: {not_after}",
                )
    except ssl.SSLCertVerificationError as e:
        record("TLS cert valid", False, str(e))
    except Exception as e:
        record("TLS cert check", False, str(e))

    browser.close()

# Upload flow test
log("\n[10] Upload flow test...")
try:
    import io as _io
    import struct

    # Create minimal valid WAV: 44100Hz, 16-bit, mono, 2 seconds of silence
    sr, dur = 16000, 2
    samples = bytes(sr * dur * 2)  # 16-bit = 2 bytes/sample
    buf = _io.BytesIO()
    data_size = len(samples)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(samples)
    wav_data = buf.getvalue()

    boundary = b"TestBoundary7f3a"
    body = (
        b"--"
        + boundary
        + b'\r\nContent-Disposition: form-data; name="file"; filename="smoke_test.wav"\r\nContent-Type: audio/wav\r\n\r\n'
        + wav_data
        + b"\r\n--"
        + boundary
        + b'\r\nContent-Disposition: form-data; name="model_size"\r\n\r\ntiny\r\n'
        + b"--"
        + boundary
        + b"--\r\n"
    )

    import urllib.request as _req

    req = _req.Request(
        f"{BASE_URL}/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"},
        method="POST",
    )
    upload_ctx = ssl.create_default_context()
    upload_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    with _req.urlopen(req, context=upload_ctx, timeout=15) as r:
        result = json.loads(r.read())
    task_id = result.get("task_id")
    record("Upload accepted", bool(task_id), f"task_id={task_id}")

    if task_id:
        # Poll up to 15s
        import time as _time

        poll_ctx = ssl.create_default_context()
        poll_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        final_status = None
        for _ in range(15):
            _time.sleep(1)
            with _req.urlopen(f"{BASE_URL}/progress/{task_id}", context=poll_ctx, timeout=5) as r:
                p = json.loads(r.read())
                if p["status"] in ("done", "error", "cancelled"):
                    final_status = p["status"]
                    break
        record("Task completes (done or error)", final_status in ("done", "error"), f"status={final_status}")
except Exception as e:
    record("Upload flow", False, str(e))

# Summary
log("\n" + "=" * 62)
log("  SUMMARY")
log("=" * 62)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
total = len(results)
log(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
log("=" * 62)
if failed:
    log("\n  FAILURES:")
    for name, ok, detail in results:
        if not ok:
            log(f"    [!!] {name}: {detail}")
log("")
sys.exit(0 if failed == 0 else 1)

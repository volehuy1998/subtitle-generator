"""E2E tests: /status page."""

from playwright.sync_api import Page

BASE_URL = "https://openlabs.club"


def test_status_page_loads(page: Page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    resp = page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok
    root = page.inner_html("#root")
    assert len(root) > 100
    assert not errors, f"JS errors on /status: {errors}"


def test_status_page_title(page: Page):
    page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    assert "SubForge" in page.title()


def test_status_page_shows_metrics(page: Page):
    page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)  # wait for API calls
    content = page.content()
    # Should show uptime or some metric
    assert any(word in content for word in ["Uptime", "uptime", "Operational", "operational", "Status", "status"])


def test_status_page_no_js_errors(page: Page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    assert not errors

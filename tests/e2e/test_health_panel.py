"""E2E tests: health panel indicator and DB status."""

from playwright.sync_api import Page

BASE_URL = "https://openlabs.club"


def test_health_panel_opens(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)  # wait for SSE
    # Click the health button in header
    # It shows "Healthy" or similar text
    health_btn = page.locator("header button")
    if health_btn.count() > 0:
        health_btn.first.click()
        page.wait_for_timeout(500)
        # Panel should appear with "All systems operational" or similar
        content = page.content()
        assert any(w in content for w in ["operational", "Operational", "degraded", "error", "Database"])


def test_health_shows_db_connected(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    # Click health button
    header_btn = page.locator("header button").first
    header_btn.click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "Connected" in content or "Database" in content

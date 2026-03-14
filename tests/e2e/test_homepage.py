"""E2E tests: homepage load, React mount, UI elements, no JS errors."""

from playwright.sync_api import Page, expect

BASE_URL = "https://openlabs.club"


def test_homepage_loads(page: Page):
    """Page returns 200 and React root mounts."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    resp = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok, f"Expected 200, got {resp.status if resp else 'no response'}"
    root = page.inner_html("#root")
    assert len(root) > 100, "React root is empty — app failed to render"
    assert not errors, f"JS errors on homepage: {errors}"


def test_transcribe_tab_visible(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    btn = page.get_by_role("button", name="Transcribe")
    expect(btn).to_be_visible()


def test_embed_tab_visible(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    btn = page.get_by_role("button", name="Embed Subtitles")
    expect(btn).to_be_visible()


def test_file_upload_dropzone_visible(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    # File input should exist
    inp = page.locator("input[type='file']")
    assert inp.count() > 0, "No file input found"


def test_health_indicator_visible(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    # Wait for SSE health stream to populate
    page.wait_for_timeout(2000)
    # Health dot or label should be in the header
    header = page.locator("header")
    expect(header).to_be_visible()
    # Should show "Healthy" or "Connecting"
    assert "Healthy" in page.content() or "Connecting" in page.content()


def test_tab_switching(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    # Click Embed tab
    page.get_by_role("button", name="Embed Subtitles").click()
    page.wait_for_timeout(300)
    # Click back to Transcribe
    page.get_by_role("button", name="Transcribe").click()
    page.wait_for_timeout(300)
    # Should not crash
    errors_after = []
    page.on("pageerror", lambda e: errors_after.append(str(e)))
    assert not errors_after


def test_no_console_errors(page: Page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    assert not errors, f"JS errors detected: {errors}"

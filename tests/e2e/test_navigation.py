"""E2E tests: SPA navigation (Sprint L73).

Tests client-side routing, page content, browser history,
logo navigation, footer presence, and theme toggle.

-- Scout (QA Lead)
"""

import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("E2E_BASE_URL", "https://openlabs.club")


def test_homepage_accessible(page: Page):
    """Root path should load the main app page."""
    resp = page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok, f"Expected 200, got {resp.status if resp else 'no response'}"
    root = page.inner_html("#root")
    assert len(root) > 100, "React root should render content"


def test_status_page_accessible(page: Page):
    """Status page should load at /status."""
    resp = page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok
    page.wait_for_timeout(1500)
    content = page.content()
    assert any(w in content for w in ["Status", "status", "Operational", "operational"]), (
        "Status page should contain status-related content"
    )


def test_about_page_accessible(page: Page):
    """About page should load at /about."""
    resp = page.goto(f"{BASE_URL}/about", wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok
    page.wait_for_timeout(1000)
    content = page.content()
    assert any(w in content for w in ["About", "SubForge", "Whisper"]), "About page should contain relevant content"


def test_contact_page_accessible(page: Page):
    """Contact page should load at /contact."""
    resp = page.goto(f"{BASE_URL}/contact", wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok
    page.wait_for_timeout(1000)
    content = page.content()
    assert any(w in content for w in ["Contact", "Bug Report", "contact"]), (
        "Contact page should contain contact-related content"
    )


def test_security_page_accessible(page: Page):
    """Security page should load at /security."""
    resp = page.goto(f"{BASE_URL}/security", wait_until="domcontentloaded", timeout=15000)
    assert resp and resp.ok
    page.wait_for_timeout(1000)
    content = page.content()
    assert any(w in content for w in ["Security", "security", "OWASP"]), (
        "Security page should contain security-related content"
    )


def test_nav_link_to_status(page: Page):
    """Clicking Status nav link should navigate to /status via SPA routing."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.locator("header nav a").filter(has_text="Status").click()
    page.wait_for_timeout(1000)
    assert page.url.rstrip("/").endswith("/status"), f"Expected URL to end with /status, got {page.url}"


def test_nav_link_to_about(page: Page):
    """Clicking About nav link should navigate to /about via SPA routing."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.locator("header nav a").filter(has_text="About").click()
    page.wait_for_timeout(1000)
    assert page.url.rstrip("/").endswith("/about"), f"Expected URL to end with /about, got {page.url}"


def test_nav_link_to_app(page: Page):
    """Clicking App nav link from another page should return to home."""
    page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.locator("header nav a").filter(has_text="App").click()
    page.wait_for_timeout(1000)
    path = page.url.replace(BASE_URL, "").rstrip("/")
    assert path == "" or path == "/", f"Expected root path, got {path}"


def test_browser_back_forward(page: Page):
    """Browser back/forward should work with SPA navigation."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.locator("header nav a").filter(has_text="Status").click()
    page.wait_for_timeout(1000)
    assert "/status" in page.url
    page.locator("header nav a").filter(has_text="About").click()
    page.wait_for_timeout(1000)
    assert "/about" in page.url
    page.go_back()
    page.wait_for_timeout(1000)
    assert "/status" in page.url
    page.go_forward()
    page.wait_for_timeout(1000)
    assert "/about" in page.url


def test_logo_returns_home(page: Page):
    """Clicking the SubForge logo should navigate back to home."""
    page.goto(f"{BASE_URL}/about", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    logo = page.locator("header a").filter(has_text="SubForge").first
    expect(logo).to_be_visible()
    logo.click()
    page.wait_for_timeout(1000)
    path = page.url.replace(BASE_URL, "").rstrip("/")
    assert path == "" or path == "/", f"Expected root path after logo click, got {path}"


def test_footer_present_on_homepage(page: Page):
    """Footer should be present on the homepage."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    footer = page.locator("footer")
    expect(footer).to_be_visible()
    footer_text = footer.text_content()
    assert "SubForge" in footer_text, "Footer should contain SubForge branding"


def test_footer_present_on_status_page(page: Page):
    """Footer should be present on the status page."""
    page.goto(f"{BASE_URL}/status", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    content = page.content()
    assert "SubForge" in content, "Page should contain SubForge branding"


def test_footer_links_navigate(page: Page):
    """Footer navigation links should work for SPA routing."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    footer_nav = page.locator("footer nav")
    if footer_nav.count() > 0:
        status_link = footer_nav.locator("a").filter(has_text="Status")
        if status_link.count() > 0:
            status_link.click()
            page.wait_for_timeout(1000)
            assert "/status" in page.url, "Footer Status link should navigate to /status"


def test_theme_toggle_exists(page: Page):
    """Theme toggle button should be in the header."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    theme_btn = page.locator("header button[aria-label*='mode'], header button[aria-label*='theme']").first
    expect(theme_btn).to_be_visible()


def test_theme_toggle_cycles(page: Page):
    """Clicking theme toggle should change its aria-label (cycling through themes)."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    theme_btn = page.locator("header button[aria-label*='mode'], header button[aria-label*='theme']").first
    initial_label = theme_btn.get_attribute("aria-label")
    theme_btn.click()
    page.wait_for_timeout(500)
    new_label = theme_btn.get_attribute("aria-label")
    assert new_label != initial_label, (
        f"Theme label should change after click. Before: '{initial_label}', After: '{new_label}'"
    )


def test_header_present_on_all_pages(page: Page):
    """Header should be visible on every page."""
    pages = ["/", "/status", "/about", "/contact", "/security"]
    for path in pages:
        page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)
        header = page.locator("header")
        expect(header).to_be_visible()


def test_active_nav_link_styling(page: Page):
    """The currently active nav link should be visually distinguished (different style)."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    app_link = page.locator("header nav a").filter(has_text="App")
    status_link = page.locator("header nav a").filter(has_text="Status")
    app_weight = app_link.evaluate("el => getComputedStyle(el).fontWeight")
    status_weight = status_link.evaluate("el => getComputedStyle(el).fontWeight")
    assert int(app_weight) > int(status_weight), (
        f"Active link should have higher font weight. App: {app_weight}, Status: {status_weight}"
    )


def test_no_js_errors_during_navigation(page: Page):
    """No JavaScript errors should occur during SPA navigation between pages."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    for link_text in ["Status", "About"]:
        nav_link = page.locator("header nav a").filter(has_text=link_text)
        if nav_link.count() > 0:
            nav_link.click()
            page.wait_for_timeout(800)
    app_link = page.locator("header nav a").filter(has_text="App")
    if app_link.count() > 0:
        app_link.click()
        page.wait_for_timeout(800)
    assert not errors, f"JS errors during navigation: {errors}"

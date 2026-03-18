"""
Static page tests — /status, /about, /security, /contact, navigation, footer.
"""

import pytest
from playwright.sync_api import Page, expect

STATIC_ROUTES = ["/status", "/about", "/security", "/contact"]


@pytest.mark.nav
@pytest.mark.parametrize("route", STATIC_ROUTES)
def test_static_page_loads(page: Page, base_url: str, route: str):
    """Each static route returns 200, React mounts, header and footer render."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    response = page.goto(f"{base_url}{route}")
    assert response.status == 200, f"Expected 200 for {route}, got {response.status}"
    root = page.locator("#root")
    expect(root).not_to_be_empty()
    expect(page.locator('[data-testid="app-header"]')).to_be_visible()
    expect(page.locator('[data-testid="footer"]')).to_be_visible()
    assert not errors, f"JS errors on {route}: {errors}"


@pytest.mark.nav
def test_nav_to_about(page: Page, base_url: str):
    page.goto(base_url)
    page.locator('[data-testid="app-header"]').get_by_role("button", name="About").click()
    page.wait_for_url("**/about**", timeout=5000)
    assert page.url.endswith("/about"), f"Expected /about, got: {page.url}"


@pytest.mark.nav
def test_nav_to_status(page: Page, base_url: str):
    page.goto(base_url)
    page.locator('[data-testid="app-header"]').get_by_role("button", name="Status").click()
    page.wait_for_url("**/status**", timeout=5000)
    assert page.url.endswith("/status"), f"Expected /status, got: {page.url}"


@pytest.mark.nav
def test_browser_back_forward(page: Page, base_url: str):
    page.goto(base_url)
    page.locator('[data-testid="app-header"]').get_by_role("button", name="Status").click()
    page.wait_for_url("**/status**", timeout=5000)
    page.go_back()
    page.wait_for_url(base_url.rstrip("/") + "/", timeout=5000)
    assert page.url.rstrip("/") == base_url.rstrip("/"), f"Expected /, got: {page.url}"
    page.go_forward()
    page.wait_for_url("**/status**", timeout=5000)
    assert page.url.endswith("/status"), f"Expected /status, got: {page.url}"


@pytest.mark.nav
@pytest.mark.parametrize(
    "label,route",
    [
        ("About", "/about"),
        ("Status", "/status"),
        ("Security", "/security"),
        ("Contact", "/contact"),
    ],
)
def test_footer_links(page: Page, base_url: str, label: str, route: str):
    page.goto(base_url)
    footer = page.locator('[data-testid="footer"]')
    expect(footer).to_be_visible()
    footer.get_by_role("button", name=label).click()
    page.wait_for_url(f"**{route}**", timeout=5000)
    assert page.url.endswith(route), f"Expected {route}, got: {page.url}"

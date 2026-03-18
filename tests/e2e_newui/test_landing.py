"""
Landing page smoke tests — no file upload.
Verifies UploadZone, ProjectGrid, Header render correctly with no JS errors.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.smoke
def test_landing_page_loads(page: Page, base_url: str):
    """Page responds 200 and React mounts."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    response = page.goto(base_url)
    assert response.status == 200, f"Expected 200, got {response.status}"
    root = page.locator("#root")
    expect(root).not_to_be_empty()
    assert not errors, f"JS errors on page load: {errors}"


@pytest.mark.smoke
def test_upload_zone_present(page: Page, base_url: str):
    page.goto(base_url)
    zone = page.locator('[data-testid="upload-zone"]')
    expect(zone).to_be_visible()


@pytest.mark.smoke
def test_upload_zone_text(page: Page, base_url: str):
    page.goto(base_url)
    zone = page.locator('[data-testid="upload-zone"]')
    expect(zone).to_contain_text("Drop your file here")
    expect(zone).to_contain_text("or click to browse")


@pytest.mark.smoke
def test_format_hint_visible(page: Page, base_url: str):
    page.goto(base_url)
    hint = page.locator('[data-testid="format-hint"]')
    expect(hint).to_be_visible()
    expect(hint).to_contain_text("MP4")
    expect(hint).to_contain_text("WAV")


@pytest.mark.smoke
def test_size_hint_visible(page: Page, base_url: str):
    page.goto(base_url)
    hint = page.locator('[data-testid="size-hint"]')
    expect(hint).to_be_visible()
    expect(hint).to_contain_text("2GB")


@pytest.mark.smoke
def test_file_input_present(page: Page, base_url: str):
    page.goto(base_url)
    file_input = page.locator('input[type="file"]')
    assert file_input.count() > 0, "No file input found"


@pytest.mark.smoke
def test_project_grid_present(page: Page, base_url: str):
    page.goto(base_url)
    grid = page.locator('[data-testid="project-grid"]')
    expect(grid).to_be_visible()


@pytest.mark.smoke
def test_header_present(page: Page, base_url: str):
    page.goto(base_url)
    header = page.locator('[data-testid="app-header"]')
    expect(header).to_be_visible()
    expect(header.get_by_role("button", name="Status")).to_be_visible()
    expect(header.get_by_role("button", name="About")).to_be_visible()


@pytest.mark.smoke
def test_no_js_errors_on_landing(page: Page, base_url: str):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url)
    page.wait_for_timeout(1000)
    assert not errors, f"JS errors: {errors}"

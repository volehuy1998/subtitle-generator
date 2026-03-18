"""
Upload flow tests — happy path, duplicate detection, edge cases.
"""

import re
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


def _set_file_input(page: Page, file_path: Path):
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(str(file_path))


@pytest.mark.upload
def test_happy_path_upload(page: Page, base_url: str, unique_audio_file: Path):
    """Upload unique file → progress shows → navigate to /editor/{uuid}."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url)
    _set_file_input(page, unique_audio_file)
    progress = page.locator('[data-testid="upload-progress"]')
    expect(progress).to_be_visible(timeout=5000)
    page.wait_for_url("**/editor/**", timeout=60_000)
    assert re.search(r"/editor/[0-9a-f-]+", page.url), f"Unexpected URL: {page.url}"
    assert not errors, f"JS errors during upload: {errors}"


@pytest.mark.upload
def test_duplicate_detection_cancel(page: Page, base_url: str, test_audio_file: Path):
    """Upload same file twice; cancel from duplicate dialog returns to /."""
    page.goto(base_url)
    _set_file_input(page, test_audio_file)
    page.wait_for_url("**/editor/**", timeout=60_000)
    page.goto(base_url)
    _set_file_input(page, test_audio_file)
    dialog = page.locator('text="Duplicate detected"')
    expect(dialog).to_be_visible(timeout=5000)
    cancel_btn = page.get_by_role("button", name="Cancel")
    expect(cancel_btn).to_be_visible()
    cancel_btn.click()
    page.wait_for_timeout(500)
    assert "/editor/" not in page.url, f"Expected to stay on /, got: {page.url}"
    expect(page.locator('[data-testid="upload-zone"]')).to_be_visible()


@pytest.mark.upload
def test_duplicate_detection_upload_anyway(page: Page, base_url: str, test_audio_file: Path):
    """Upload same file twice; click 'Upload anyway' → proceeds to editor."""
    page.goto(base_url)
    _set_file_input(page, test_audio_file)
    page.wait_for_url("**/editor/**", timeout=60_000)
    page.goto(base_url)
    _set_file_input(page, test_audio_file)
    dialog = page.locator('text="Duplicate detected"')
    expect(dialog).to_be_visible(timeout=5000)
    upload_anyway = page.get_by_role("button", name="Upload anyway")
    expect(upload_anyway).to_be_visible()
    upload_anyway.click()
    page.wait_for_url("**/editor/**", timeout=60_000)
    assert "/editor/" in page.url


@pytest.mark.upload
def test_invalid_extension_shows_error(page: Page, base_url: str):
    """Uploading a .exe file triggers an error toast; URL stays at /."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url)
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
        f.write(b"MZ" + b"\x00" * 100)
        bad_file = f.name
    _set_file_input(page, Path(bad_file))
    toast_container = page.locator('[data-testid="toast-container"]')
    expect(toast_container).to_be_visible(timeout=3000)
    page.wait_for_timeout(500)
    assert "/editor/" not in page.url
    assert not errors, f"JS errors: {errors}"


@pytest.mark.upload
def test_undersized_file_shows_error(page: Page, base_url: str):
    """Uploading a .wav file under 1KB triggers an error toast."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"RIFF" + b"\x00" * 100)
        tiny_file = f.name
    _set_file_input(page, Path(tiny_file))
    toast_container = page.locator('[data-testid="toast-container"]')
    expect(toast_container).to_be_visible(timeout=3000)
    # Error message should mention size or range
    toast_text = toast_container.text_content() or ""
    assert re.search(r"size|range", toast_text, re.IGNORECASE), (
        f"Expected 'size' or 'range' in toast message, got: {toast_text!r}"
    )
    page.wait_for_timeout(500)
    assert "/editor/" not in page.url
    assert not errors, f"JS errors: {errors}"

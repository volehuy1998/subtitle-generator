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
    page.wait_for_url("**/editor/**", timeout=60_000, wait_until="commit")
    assert re.search(r"/editor/[0-9a-f-]+", page.url), f"Unexpected URL: {page.url}"
    assert not errors, f"JS errors during upload: {errors}"


@pytest.mark.upload
def test_duplicate_detection_cancel(page: Page, base_url: str, duplicate_test_audio_file: Path):
    """Upload same file twice; cancel from duplicate dialog returns to /."""
    page.goto(base_url)
    _set_file_input(page, duplicate_test_audio_file)
    page.wait_for_url("**/editor/**", timeout=60_000, wait_until="commit")
    # Wait for transcription to complete — duplicate check only matches status=done tasks
    page.wait_for_timeout(8000)
    page.goto(base_url)
    _set_file_input(page, duplicate_test_audio_file)
    dialog = page.locator('text="Duplicate detected"')
    expect(dialog).to_be_visible(timeout=5000)
    cancel_btn = page.get_by_role("button", name="Cancel")
    expect(cancel_btn).to_be_visible()
    cancel_btn.click()
    page.wait_for_timeout(500)
    assert "/editor/" not in page.url, f"Expected to stay on /, got: {page.url}"
    expect(page.locator('[data-testid="upload-zone"]')).to_be_visible()


@pytest.mark.upload
def test_duplicate_detection_upload_anyway(page: Page, base_url: str, duplicate_test_audio_file: Path):
    """Upload same file twice; click 'Upload anyway' → proceeds to editor."""
    page.goto(base_url)
    _set_file_input(page, duplicate_test_audio_file)
    # First upload may show duplicate dialog if test_duplicate_detection_cancel ran first.
    # Wait up to 5s for the dialog; if it appears, click through.
    dialog = page.locator('text="Duplicate detected"')
    try:
        expect(dialog).to_be_visible(timeout=5000)
        page.get_by_role("button", name="Upload anyway").click()
    except Exception:
        pass  # No dialog — first upload for this file in the session
    page.wait_for_url("**/editor/**", timeout=60_000, wait_until="commit")
    # Wait for transcription to complete — duplicate check only matches status=done tasks
    page.wait_for_timeout(8000)
    page.goto(base_url)
    _set_file_input(page, duplicate_test_audio_file)
    dialog = page.locator('text="Duplicate detected"')
    expect(dialog).to_be_visible(timeout=5000)
    upload_anyway = page.get_by_role("button", name="Upload anyway")
    expect(upload_anyway).to_be_visible()
    upload_anyway.click()
    page.wait_for_url("**/editor/**", timeout=60_000, wait_until="commit")
    assert "/editor/" in page.url


@pytest.mark.upload
def test_upload_full_transcription_flow(page: Page, base_url: str, unique_audio_file: Path):
    """Upload file → progress shows → transcription completes → editor loads with NO error boundary.

    This test specifically guards against the bug where useSSE treated the done-event
    'segments' field (a count integer) as an array, crashing SegmentList.
    """
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url)
    _set_file_input(page, unique_audio_file)

    # Wait for navigation to editor
    page.wait_for_url("**/editor/**", timeout=60_000, wait_until="commit")
    assert re.search(r"/editor/[0-9a-f-]+", page.url), f"Unexpected URL: {page.url}"

    # Progress view may still be visible while transcription runs — that's fine

    # Wait for transcription to finish: upload-progress disappears and editor renders
    # The done SSE event triggers setComplete — either segment-list or empty-state appears.
    # Use a broad locator that matches EITHER outcome (segments present OR empty audio).
    # The critical thing is that the ErrorBoundary "Something went wrong" is NOT shown.
    page.wait_for_function(
        """() => {
            const errBoundary = document.body.innerText.includes('An unexpected error occurred')
            const progressGone = !document.querySelector('[data-testid="upload-progress"]')
            const editorPresent = document.querySelector('[data-testid="segment-list"]')
                || document.body.innerText.includes('No subtitles yet')
                || document.body.innerText.includes('Download')
            return errBoundary || (progressGone && editorPresent)
        }""",
        timeout=120_000,
    )

    # Fail if the error boundary appeared
    assert not page.locator('text="An unexpected error occurred"').is_visible(), (
        "ErrorBoundary fired after transcription completed — likely a type mismatch in useSSE done handler"
    )
    assert not errors, f"JS errors during full transcription flow: {errors}"


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

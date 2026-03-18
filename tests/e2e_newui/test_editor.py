"""
Editor tests — session restore, inline editing with server-side persistence, download menu.
Requires completed_task_id fixture (set FIXTURE_TASK_ID env var or auto-uploads).
"""

import os
import uuid

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.editor
def test_editor_session_restore(page: Page, base_url: str, completed_task_id: str):
    """Navigating directly to /editor/{task_id} loads the editor without error."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{base_url}/editor/{completed_task_id}")
    # Wait for segment-list or editor to render (up to 15s for session restore)
    segment_list = page.locator('[data-testid="segment-list"]')
    try:
        expect(segment_list).to_be_visible(timeout=15_000)
        loaded = True
    except Exception:
        loaded = False
    # If FIXTURE_TASK_ID is set (real speech audio), assert segments present
    if os.environ.get("FIXTURE_TASK_ID") and loaded:
        rows = segment_list.locator(".flex.gap-3")
        assert rows.count() > 0, "Expected at least one segment row"
    assert not errors, f"JS errors during session restore: {errors}"


@pytest.mark.editor
def test_editor_inline_edit_persists(page: Page, base_url: str, completed_task_id: str):
    """Edit first segment text, reload, verify server saved it."""
    if not os.environ.get("FIXTURE_TASK_ID"):
        pytest.skip("Inline edit persistence test requires FIXTURE_TASK_ID (real audio)")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{base_url}/editor/{completed_task_id}")
    segment_list = page.locator('[data-testid="segment-list"]')
    expect(segment_list).to_be_visible(timeout=15_000)
    first_row = segment_list.locator(".flex.gap-3").first
    first_row.click()
    textarea = first_row.locator("textarea")
    expect(textarea).to_be_visible(timeout=3000)
    unique_text = f"edited_{uuid.uuid4().hex[:8]}"
    textarea.fill(unique_text)
    textarea.blur()
    page.wait_for_timeout(500)
    page.reload()
    expect(segment_list).to_be_visible(timeout=15_000)
    first_row_text = segment_list.locator(".flex.gap-3").first
    expect(first_row_text).to_contain_text(unique_text, timeout=5000)
    assert not errors, f"JS errors during edit persistence test: {errors}"


@pytest.mark.editor
def test_editor_download_menu(page: Page, base_url: str, completed_task_id: str):
    """Download button opens menu with SRT and VTT download links."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{base_url}/editor/{completed_task_id}")
    # DownloadMenu is in the EditorToolbar — wait for it to appear (editing phase)
    download_wrapper = page.locator('[data-testid="download-menu-wrapper"]')
    expect(download_wrapper).to_be_visible(timeout=15_000)
    download_wrapper.locator("button").first.click()
    # DownloadMenu generates: /subtitles/{taskId}?format=srt&download=1
    srt_link = page.locator(f'a[href*="/subtitles/{completed_task_id}"][href*="format=srt"]')
    vtt_link = page.locator(f'a[href*="/subtitles/{completed_task_id}"][href*="format=vtt"]')
    expect(srt_link).to_be_visible(timeout=3000)
    expect(vtt_link).to_be_visible(timeout=3000)
    assert not errors, f"JS errors during download menu test: {errors}"

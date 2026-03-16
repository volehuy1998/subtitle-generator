"""E2E tests: Upload -> transcription -> download flow (Sprint L71).

Tests the core transcription workflow: form elements, model selector,
language dropdown, format selector, drop zone, and confirmation dialog.

-- Scout (QA Lead)
"""

import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("E2E_BASE_URL", "https://openlabs.club")


def test_transcription_form_visible(page: Page):
    """Transcription form should be visible on page load with Transcribe tab active."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    transcribe_tab = page.get_by_role("tab", name="Transcribe")
    expect(transcribe_tab).to_be_visible()
    expect(transcribe_tab).to_have_attribute("aria-selected", "true")


def test_drop_zone_present(page: Page):
    """File drop zone should be present and interactive."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    dropzone = page.locator("[aria-label='Upload media file']")
    expect(dropzone).to_be_visible()
    content = dropzone.text_content()
    assert "drop" in content.lower() or "browse" in content.lower(), "Drop zone should contain upload instructions"


def test_file_input_exists(page: Page):
    """A file input element should exist in the transcription form."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    file_input = page.locator("input[type='file']")
    assert file_input.count() > 0, "Expected at least one file input element"


def test_model_selector_shows_five_options(page: Page):
    """Model selector should display 5 model options: tiny, base, small, medium, large."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    model_group = page.locator("[aria-label='Select transcription model']")
    expect(model_group).to_be_visible()
    model_buttons = model_group.get_by_role("radio")
    assert model_buttons.count() == 5, f"Expected 5 model options, found {model_buttons.count()}"


def test_model_names_present(page: Page):
    """All 5 model names should appear: Tiny, Base, Small, Medium, Large."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    model_group = page.locator("[aria-label='Select transcription model']")
    content = model_group.text_content()
    for name in ["Tiny", "Base", "Small", "Medium", "Large"]:
        assert name in content, f"Model '{name}' not found in model selector"


def test_model_selection_changes(page: Page):
    """Clicking a model option should select it (aria-checked=true)."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    model_group = page.locator("[aria-label='Select transcription model']")
    radios = model_group.get_by_role("radio")
    radios.last.click()
    page.wait_for_timeout(300)
    expect(radios.last).to_have_attribute("aria-checked", "true")


def test_language_dropdown_populated(page: Page):
    """Language dropdown should be populated with Auto-detect and multiple languages."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    lang_select = page.locator("#language-select")
    expect(lang_select).to_be_visible()
    options = lang_select.locator("option")
    count = options.count()
    assert count >= 10, f"Expected at least 10 language options, found {count}"
    first_text = options.first.text_content()
    assert "Auto-detect" in first_text, "First language option should be Auto-detect"


def test_format_selector_srt_vtt(page: Page):
    """Format selector should show SRT and VTT options."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    format_group = page.locator("[aria-label='Select output format']")
    expect(format_group).to_be_visible()
    format_buttons = format_group.get_by_role("radio")
    assert format_buttons.count() == 2, f"Expected 2 format options, found {format_buttons.count()}"
    texts = [format_buttons.nth(i).text_content() for i in range(2)]
    assert "SRT" in texts, "SRT format option not found"
    assert "VTT" in texts, "VTT format option not found"


def test_format_selector_toggles(page: Page):
    """Clicking VTT should select it, then clicking SRT should switch back."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    format_group = page.locator("[aria-label='Select output format']")
    srt_btn = format_group.get_by_role("radio").filter(has_text="SRT")
    vtt_btn = format_group.get_by_role("radio").filter(has_text="VTT")
    vtt_btn.click()
    page.wait_for_timeout(300)
    expect(vtt_btn).to_have_attribute("aria-checked", "true")
    expect(srt_btn).to_have_attribute("aria-checked", "false")
    srt_btn.click()
    page.wait_for_timeout(300)
    expect(srt_btn).to_have_attribute("aria-checked", "true")
    expect(vtt_btn).to_have_attribute("aria-checked", "false")


def test_device_selector_visible(page: Page):
    """Device selector (CPU, optionally GPU) should be visible."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    device_group = page.locator("[aria-label='Select device']")
    expect(device_group).to_be_visible()
    radios = device_group.get_by_role("radio")
    assert radios.count() >= 1, "Expected at least 1 device option (CPU)"
    content = device_group.text_content()
    assert "CPU" in content, "CPU device option should be present"


def test_translate_dropdown_present(page: Page):
    """Translate To dropdown should be present with 'No translation' default."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    translate_select = page.locator("#translate-select")
    expect(translate_select).to_be_visible()
    first_option = translate_select.locator("option").first
    assert "No translation" in first_option.text_content()


def test_drop_zone_shows_file_formats(page: Page):
    """Drop zone should display supported file format hints."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    dropzone = page.locator("[aria-label='Upload media file']")
    content = dropzone.text_content()
    assert "MP4" in content or "mp4" in content, "Drop zone should mention MP4"
    assert "500 MB" in content or "500MB" in content, "Drop zone should mention size limit"


def test_no_js_errors_during_form_interaction(page: Page):
    """No JavaScript errors should occur during normal form interaction."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)
    model_group = page.locator("[aria-label='Select transcription model']")
    if model_group.count() > 0:
        radios = model_group.get_by_role("radio")
        if radios.count() >= 3:
            radios.nth(2).click()
            page.wait_for_timeout(300)
    format_group = page.locator("[aria-label='Select output format']")
    if format_group.count() > 0:
        vtt = format_group.get_by_role("radio").filter(has_text="VTT")
        if vtt.count() > 0:
            vtt.click()
            page.wait_for_timeout(300)
    assert not errors, f"JS errors during form interaction: {errors}"

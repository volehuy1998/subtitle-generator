"""E2E tests: Embed subtitle workflow (Sprint L72).

Tests the embed tab: tab switching, mode selector (Soft Mux / Hard Burn),
style options for hard burn, and file picker elements.

-- Scout (QA Lead)
"""

import os

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("E2E_BASE_URL", "https://openlabs.club")


def test_embed_tab_accessible(page: Page):
    """Embed Subtitles tab should be clickable and switch to embed view."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    embed_tab = page.get_by_role("tab", name="Embed Subtitles")
    expect(embed_tab).to_be_visible()
    embed_tab.click()
    page.wait_for_timeout(500)
    expect(embed_tab).to_have_attribute("aria-selected", "true")


def test_embed_tab_shows_embed_content(page: Page):
    """Switching to Embed tab should show the embed subtitle panel content."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "Embed Subtitles" in content, "Embed panel header should be visible"
    assert "Upload a video and subtitle file" in content or "SOURCE FILES" in content, (
        "Embed panel should show source files section"
    )


def test_embed_mode_selector_visible(page: Page):
    """Soft Mux / Hard Burn mode selector should be visible in embed tab."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "Soft Mux" in content, "Soft Mux mode option should be visible"
    assert "Hard Burn" in content, "Hard Burn mode option should be visible"


def test_soft_mux_selected_by_default(page: Page):
    """Soft Mux should be the default embed mode."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "Subtitles as selectable track" in content, "Soft Mux description should be visible"


def test_hard_burn_mode_selection(page: Page):
    """Clicking Hard Burn should select it and show style options."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    hard_burn_btn = page.locator("button").filter(has_text="Hard Burn")
    hard_burn_btn.click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "SUBTITLE STYLE" in content, "Subtitle style options should appear when Hard Burn is selected"


def test_style_options_for_hard_burn(page: Page):
    """Hard Burn mode should show color and font size controls."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    hard_burn_btn = page.locator("button").filter(has_text="Hard Burn")
    hard_burn_btn.click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "Text Color" in content, "Text Color option should be visible for hard burn"
    assert "Font Size" in content or "size" in content.lower(), "Font size option should be visible for hard burn"


def test_soft_mux_hides_style_options(page: Page):
    """Switching back to Soft Mux should hide style options."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    page.locator("button").filter(has_text="Hard Burn").click()
    page.wait_for_timeout(500)
    assert "SUBTITLE STYLE" in page.content()
    page.locator("button").filter(has_text="Soft Mux").click()
    page.wait_for_timeout(500)
    assert "SUBTITLE STYLE" not in page.content(), "Style options should be hidden when Soft Mux is selected"


def test_embed_video_file_picker_present(page: Page):
    """Video file picker should be present in embed tab."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    video_picker = page.locator("[aria-label='Select video file']")
    expect(video_picker).to_be_visible()


def test_embed_subtitle_file_picker_present(page: Page):
    """Subtitle file picker should be present in embed tab."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    subtitle_picker = page.locator("[aria-label='Select subtitle file']")
    expect(subtitle_picker).to_be_visible()


def test_embed_button_disabled_without_files(page: Page):
    """Embed button should be disabled when no files are selected."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    embed_btn = page.locator("button").filter(has_text="Embed Subtitles").last
    expect(embed_btn).to_be_visible()
    expect(embed_btn).to_be_disabled()


def test_embed_translate_dropdown_present(page: Page):
    """Embed tab should have its own translation dropdown."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "TRANSLATE SUBTITLES" in content, "Translation section should be visible in embed tab"
    translate_select = page.locator("[aria-label='Select translation language']")
    expect(translate_select).to_be_visible()


def test_embed_mode_section_labeled(page: Page):
    """Embed mode section should have EMBED MODE label."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    content = page.content()
    assert "EMBED MODE" in content, "EMBED MODE section label should be present"


def test_no_js_errors_on_embed_tab(page: Page):
    """No JavaScript errors should occur when interacting with embed tab."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    page.get_by_role("tab", name="Embed Subtitles").click()
    page.wait_for_timeout(500)
    page.locator("button").filter(has_text="Hard Burn").click()
    page.wait_for_timeout(300)
    page.locator("button").filter(has_text="Soft Mux").click()
    page.wait_for_timeout(300)
    assert not errors, f"JS errors on embed tab: {errors}"

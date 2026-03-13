"""E2E tests: Pause/Cancel button visibility and Auto-detect dropdown fix."""
from playwright.sync_api import Page

BASE_URL = "https://openlabs.club"


def test_no_pause_button_on_homepage(page: Page):
    """Pause button should not appear without an active transcription task."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    pause_btns = page.get_by_role("button", name="Pause")
    assert pause_btns.count() == 0, "Pause button should not appear on homepage without active task"


def test_no_cancel_button_on_homepage(page: Page):
    """Cancel button should not appear without an active transcription task."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    cancel_btns = page.get_by_role("button", name="Cancel")
    assert cancel_btns.count() == 0, "Cancel button should not appear on homepage without active task"


def test_language_dropdown_no_duplicate_autodetect(page: Page):
    """Language dropdown should have exactly one Auto-detect option."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)

    # Find the language select (contains Auto-detect)
    lang_select = page.locator("select").filter(has_text="Auto-detect").first
    options = lang_select.locator("option")

    # Count how many options have text "Auto-detect"
    auto_count = 0
    for i in range(options.count()):
        text = options.nth(i).text_content()
        if text and "Auto-detect" in text:
            auto_count += 1

    assert auto_count == 1, f"Expected exactly 1 Auto-detect option, found {auto_count}"


def test_language_dropdown_has_languages(page: Page):
    """Language dropdown should have multiple language options loaded from API."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)

    lang_select = page.locator("select").filter(has_text="Auto-detect").first
    options = lang_select.locator("option")
    count = options.count()
    # Auto-detect + at least English, Chinese, German, etc.
    assert count >= 10, f"Expected at least 10 language options, found {count}"


def test_try_again_button_not_visible_on_homepage(page: Page):
    """Try Again button should not appear without a cancelled task."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(1500)
    try_again = page.get_by_role("button", name="Try Again")
    assert try_again.count() == 0, "Try Again button should not appear on homepage"

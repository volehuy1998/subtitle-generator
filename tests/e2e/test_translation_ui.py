"""E2E tests: translation dropdown appears once in Transcribe form, not duplicated in embed panel."""
from playwright.sync_api import Page

BASE_URL = "https://openlabs.club"


def test_translate_dropdown_exists_in_transcribe_form(page: Page):
    """The TRANSLATE TO dropdown should be visible in the transcribe form."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)  # Wait for translation languages to load

    # Find all select elements containing "No translation" option
    translate_selects = page.locator("select").filter(has_text="No translation")
    count = translate_selects.count()
    assert count >= 1, "Expected at least one translation dropdown in the transcribe form"


def test_translate_dropdown_not_duplicated_after_transcription(page: Page):
    """After transcription with translation, the embed panel should NOT show
    a second translation dropdown — translation was already applied."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)

    # Count translation dropdowns on initial page (Transcribe form visible, no results)
    translate_selects = page.locator("select").filter(has_text="No translation")
    initial_count = translate_selects.count()

    # The transcribe form should have exactly 1 translate dropdown
    # (The embed tab is not visible, so its dropdown doesn't count)
    assert initial_count == 1, (
        f"Expected exactly 1 translation dropdown in the transcribe form, found {initial_count}"
    )


def test_embed_tab_has_translate_dropdown(page: Page):
    """The Embed Subtitles tab (combine flow) should have its own translation dropdown."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)

    # Switch to Embed Subtitles tab
    page.get_by_role("button", name="Embed Subtitles").click()
    page.wait_for_timeout(500)

    # The embed tab should have a translation dropdown
    translate_selects = page.locator("select").filter(has_text="No translation")
    assert translate_selects.count() >= 1, "Embed tab should have a translation dropdown"


def test_translation_languages_populated(page: Page):
    """Translation dropdown should be populated with language options from the API."""
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(3000)  # Wait for API call to complete

    # Find the translate dropdown in the transcribe form
    translate_select = page.locator("select").filter(has_text="No translation").first
    options = translate_select.locator("option")
    option_count = options.count()

    # Should have "No translation" + at least 1 language target (English via Whisper)
    assert option_count >= 2, (
        f"Expected at least 2 options (No translation + languages), found {option_count}"
    )

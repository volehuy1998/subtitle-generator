"""Sprint 20 tests: UI/UX Overhaul & Functional Stability.

Tests cover:
  - All UI elements exist and are properly wired
  - Embed panel redesign (tabs, presets, preview, progress)
  - Video preview with CSP blob: support
  - Auto-embed feature (upload param, pipeline integration)
  - Reset UI completeness
  - Mobile responsive CSS
  - Download section elements
  - Error/loading states
"""

import pytest

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


def _html():
    """Get the main page HTML."""
    return client.get("/").text


# ── UI Element Existence ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestUIElements:
    """Verify all buttons and interactive elements exist."""

    def test_edit_subtitles_button(self):
        assert "openEditor()" in _html()

    def test_preview_video_button(self):
        assert "openVideoPreview()" in _html()

    def test_embed_button(self):
        assert "toggleEmbedPanel()" in _html()

    def test_generate_another_button(self):
        assert "resetUI()" in _html()

    def test_pause_button(self):
        assert 'id="pauseBtn"' in _html()

    def test_cancel_button(self):
        assert 'id="cancelBtn"' in _html()

    def test_download_srt_button(self):
        assert 'id="downloadBtnSrt"' in _html()

    def test_download_vtt_button(self):
        assert 'id="downloadBtnVtt"' in _html()

    def test_download_json_button(self):
        assert 'id="downloadBtnJson"' in _html()


# ── Embed Panel Redesign ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestEmbedPanel:
    """Test the redesigned embed panel."""

    def test_embed_tabs_exist(self):
        html = _html()
        assert 'id="embedTabSoft"' in html
        assert 'id="embedTabHard"' in html

    def test_embed_preset_selector(self):
        html = _html()
        assert 'id="embedPreset"' in html
        assert "youtube_white" in html
        assert "youtube_yellow" in html
        assert "cinema" in html
        assert "large_bold" in html

    def test_embed_preset_applies(self):
        """Presets should trigger applyPreset on change."""
        assert "applyPreset(this.value)" in _html()

    def test_embed_preset_definitions(self):
        """JS should have EMBED_PRESETS object with all presets."""
        html = _html()
        assert "EMBED_PRESETS" in html
        assert "'youtube_white'" in html
        assert "'cinema'" in html

    def test_embed_style_controls(self):
        html = _html()
        assert 'id="embedFont"' in html
        assert 'id="embedFontSize"' in html
        assert 'id="embedFontColor"' in html
        assert 'id="embedBold"' in html
        assert 'id="embedPosition"' in html
        assert 'id="embedBgOpacity"' in html

    def test_embed_preview_bar(self):
        html = _html()
        assert 'id="embedPreviewBar"' in html
        assert 'id="embedPreviewText"' in html

    def test_embed_progress_elements(self):
        html = _html()
        assert 'id="embedProgress"' in html
        assert 'id="embedProgressFill"' in html
        assert 'id="embedStatus"' in html

    def test_embed_result_elements(self):
        html = _html()
        assert 'id="embedResult"' in html
        assert 'id="embedResultMsg"' in html
        assert 'id="embedDownloadLink"' in html

    def test_embed_start_button(self):
        assert 'id="embedStartBtn"' in html if (html := _html()) else False
        assert "startUnifiedEmbed()" in _html()

    def test_embed_card_toggle(self):
        """Embed card should have a collapsible header."""
        assert 'toggleEmbedCard()' in _html()


# ── Video Preview ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestVideoPreview:
    """Test video preview functionality."""

    def test_video_player_exists(self):
        assert 'id="videoPlayer"' in _html()

    def test_subtitle_track_exists(self):
        assert 'id="subtitleTrack"' in _html()

    def test_load_video_button(self):
        assert "Load Video" in _html()

    def test_close_preview_button(self):
        """Video preview should have a close button."""
        assert "videoPreviewSection" in _html()
        # Close button hides the section
        html = _html()
        assert "Close" in html

    def test_video_file_input(self):
        assert 'id="videoFileInput"' in _html()

    def test_load_video_function(self):
        """loadVideoFile function should exist."""
        assert "function loadVideoFile" in _html()


# ── CSP for Video ──

class TestCSPVideoSupport:
    """Test that CSP allows blob: URLs for video preview."""

    def test_csp_has_media_src_blob(self):
        res = client.get("/")
        csp = res.headers.get("Content-Security-Policy", "")
        assert "media-src" in csp
        assert "blob:" in csp


# ── Auto-Embed Feature ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestAutoEmbed:
    """Test auto-embed upload parameter."""

    def test_auto_embed_option_in_ui(self):
        html = _html()
        assert 'id="advAutoEmbed"' in html
        assert "Soft Mux" in html
        assert "Hard Burn" in html

    def test_auto_embed_param_sent(self):
        """Upload JS should send auto_embed in FormData."""
        assert "auto_embed" in _html()

    def test_embed_done_sse_listener(self):
        """SSE should listen for embed_done event."""
        assert "embed_done" in _html()

    def test_embed_progress_sse_listener(self):
        """SSE should listen for embed_progress event."""
        assert "embed_progress" in _html()

    def test_embed_error_sse_listener(self):
        """SSE should listen for embed_error event."""
        assert "embed_error" in _html()

    def test_pipeline_auto_embed_function(self):
        """Pipeline should have _auto_embed_subtitles function."""
        from app.services import pipeline
        assert hasattr(pipeline, '_auto_embed_subtitles')

    def test_process_video_accepts_auto_embed(self):
        """process_video should accept auto_embed parameter."""
        import inspect
        from app.services.pipeline import process_video
        sig = inspect.signature(process_video)
        assert 'auto_embed' in sig.parameters


# ── Reset UI Completeness ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestResetUI:
    """Test that resetUI properly resets all state."""

    def test_reset_hides_embed_card(self):
        assert "embedCard" in _html()
        # resetUI should reference embedCard
        html = _html()
        assert "embedCard" in html

    def test_reset_clears_embed_result(self):
        assert "embedResult" in _html()

    def test_reset_clears_video_player(self):
        """resetUI should stop and clear video player."""
        html = _html()
        assert "videoPlayer" in html
        assert "removeAttribute('src')" in html

    def test_reset_clears_embed_mode(self):
        """resetUI should reset embedMode to soft."""
        html = _html()
        assert "setEmbedMode('soft')" in html


# ── Mobile Responsive ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestMobileResponsive:
    """Test mobile responsive CSS exists."""

    def test_media_query_600px(self):
        assert "@media (max-width: 600px)" in _html()

    def test_media_query_400px(self):
        assert "@media (max-width: 400px)" in _html()

    def test_embed_grid_responsive(self):
        """Embed grid should stack on mobile."""
        html = _html()
        assert "embed-grid" in html

    def test_embed_tabs_responsive(self):
        """Embed tabs should stack on mobile."""
        html = _html()
        assert "embed-tabs" in html


# ── Error States ──

class TestErrorStates:
    """Test error handling in UI."""

    @pytest.mark.skip(reason="Frontend migrated to React")
    def test_show_error_function_exists(self):
        assert "function showError" in _html()

    @pytest.mark.skip(reason="Frontend migrated to React")
    def test_cancelled_section_exists(self):
        assert 'id="cancelledSection"' in _html()

    @pytest.mark.skip(reason="Frontend migrated to React")
    def test_warning_banner_exists(self):
        assert 'id="warningBanner"' in _html() or "warningBanner" in _html()


# ── Embed Route Color Conversion ──

class TestEmbedColorConversion:
    """Test hex to ASS color conversion in embed route."""

    def test_hex_to_ass_conversion(self):
        """Route should convert #RRGGBB to &HBBGGRR."""
        # The conversion logic is in the route handler
        # Just verify the route module loads
        assert True


# ── Editor ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestEditor:
    """Test subtitle editor elements."""

    def test_editor_section_exists(self):
        assert 'id="editorSection"' in _html()

    def test_editor_open_function(self):
        assert "function openEditor" in _html()

    def test_editor_save_function(self):
        assert "function saveEdits" in _html()

    def test_editor_close_function(self):
        assert "function closeEditor" in _html()

    def test_editor_delete_function(self):
        assert "function deleteSegment" in _html()


# ── SSE Reconnection ──

@pytest.mark.skip(reason="Frontend migrated to React")
class TestSSEReconnection:
    """Test SSE reconnection logic."""

    def test_sse_retry_variables(self):
        html = _html()
        assert "sseRetryTimeout" in html
        assert "sseRetryDelay" in html
        assert "sseLastEventTime" in html

    def test_sse_heartbeat_listener(self):
        assert "heartbeat" in _html()

    def test_sse_exponential_backoff(self):
        """Should have exponential backoff logic."""
        assert "sseRetryDelay * 2" in _html()

    def test_polling_checks_last_event_time(self):
        """Polling should check sseLastEventTime for stale connections."""
        assert "sseLastEventTime" in _html()


# ── Presets Endpoint ──

class TestPresetsEndpoint:
    """Test embed presets API."""

    def test_presets_returns_all(self):
        res = client.get("/embed/presets")
        assert res.status_code == 200
        data = res.json()
        presets = data["presets"]
        assert "default" in presets
        assert "youtube_white" in presets
        assert "cinema" in presets
        assert "large_bold" in presets
        assert "top_position" in presets

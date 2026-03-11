"""Tests for Sprint 10: Frontend Modernization.

S10-1: Upload form: word timestamps, diarize, translate options
S10-2: Upload form: custom vocabulary text field
S10-3: Upload form: max chars/line slider
S10-4: Download section: JSON format button
S10-5: Subtitle embedding UI
S10-6: Speaker labels in segment preview
S10-7: Word-level timestamp support in editor
S10-8: Integration tests
"""

from pathlib import Path

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

PROJECT_ROOT = Path(__file__).parent.parent


def _read_html():
    return (PROJECT_ROOT / "templates" / "index.html").read_text()


# ── S10-1: Advanced Upload Options in UI ──

class TestUploadAdvancedOptions:
    def test_word_timestamps_checkbox(self):
        assert 'id="advWordTimestamps"' in _read_html()

    def test_diarize_checkbox(self):
        assert 'id="advDiarize"' in _read_html()

    def test_translate_checkbox(self):
        assert 'id="advTranslate"' in _read_html()

    def test_advanced_toggle_button(self):
        assert "toggleAdvanced" in _read_html()

    def test_advanced_panel_hidden_by_default(self):
        html = _read_html()
        assert 'class="advanced-panel"' in html  # no 'show' class by default


# ── S10-2: Custom Vocabulary ──

class TestCustomVocabulary:
    def test_vocabulary_input_exists(self):
        assert 'id="advVocabulary"' in _read_html()

    def test_vocabulary_placeholder(self):
        assert "Domain-specific terms" in _read_html()

    def test_vocabulary_sent_as_initial_prompt(self):
        assert "initial_prompt" in _read_html()


# ── S10-3: Max Chars Per Line ──

class TestMaxCharsSlider:
    def test_slider_exists(self):
        assert 'id="advMaxChars"' in _read_html()

    def test_slider_range(self):
        html = _read_html()
        assert 'min="20"' in html
        assert 'max="80"' in html

    def test_slider_default_value(self):
        assert 'value="42"' in _read_html()

    def test_slider_value_display(self):
        assert 'id="advMaxCharsValue"' in _read_html()


# ── S10-4: JSON Download Button ──

class TestJsonDownload:
    def test_json_download_button_exists(self):
        assert 'id="downloadBtnJson"' in _read_html()

    def test_json_button_hidden_by_default(self):
        assert 'display:none' in _read_html().split('downloadBtnJson')[1][:50]

    def test_json_button_shown_for_word_timestamps(self):
        html = _read_html()
        assert "advWordTimestamps" in html
        assert "format=json" in html


# ── S10-5: Subtitle Embedding UI ──

class TestEmbedUI:
    def test_embed_card_exists(self):
        assert 'id="embedCard"' in _read_html()

    def test_embed_toggle_exists(self):
        assert "toggleEmbedCard" in _read_html()

    def test_embed_mode_selector(self):
        html = _read_html()
        assert 'id="embedTabSoft"' in html
        assert "Soft Mux" in html
        assert "Hard Burn" in html

    def test_embed_preset_selector(self):
        html = _read_html()
        assert 'id="embedPreset"' in html
        assert "youtube_white" in html
        assert "cinema" in html

    def test_embed_start_button(self):
        assert "startUnifiedEmbed" in _read_html()

    def test_embed_presets_endpoint(self):
        res = client.get("/embed/presets")
        assert res.status_code == 200
        data = res.json()
        assert "presets" in data
        assert "default" in data["presets"]
        assert "youtube_white" in data["presets"]


# ── S10-6: Speaker Labels ──

class TestSpeakerLabels:
    def test_speaker_label_css(self):
        html = _read_html()
        assert "speaker-label" in html
        assert "speaker-0" in html

    def test_speaker_colors_defined(self):
        html = _read_html()
        assert "speakerColors" in html

    def test_speaker_label_rendering_logic(self):
        html = _read_html()
        assert "seg.speaker" in html
        assert "addSegmentWithSpeaker" in html


# ── S10-7: Upload Sends Advanced Params ──

class TestUploadParamWiring:
    def test_upload_sends_word_timestamps(self):
        html = _read_html()
        assert "fd.append('word_timestamps'" in html

    def test_upload_sends_diarize(self):
        html = _read_html()
        assert "fd.append('diarize'" in html

    def test_upload_sends_translate(self):
        html = _read_html()
        assert "fd.append('translate_to_english'" in html

    def test_upload_sends_max_line_chars(self):
        html = _read_html()
        assert "fd.append('max_line_chars'" in html


# ── S10-8: Integration ──

class TestIntegration:
    def test_main_page_loads(self):
        res = client.get("/")
        assert res.status_code == 200

    def test_embed_presets_accessible(self):
        assert client.get("/embed/presets").status_code == 200

    def test_analytics_link_not_broken(self):
        assert client.get("/analytics").status_code == 200

    def test_dashboard_link_not_broken(self):
        assert client.get("/dashboard").status_code == 200

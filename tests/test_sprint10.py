"""Tests for Sprint 10: Frontend Modernization.

S10-4: Download section: JSON format button
S10-5: Subtitle embedding UI
S10-8: Integration tests
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")

PROJECT_ROOT = Path(__file__).parent.parent


def _read_html():
    return (PROJECT_ROOT / "templates" / "index.html").read_text()


# ── S10-4: JSON Download Button ──


class TestJsonDownload:
    def test_json_download_button_exists(self):
        assert 'id="downloadBtnJson"' in _read_html()

    def test_json_button_hidden_by_default(self):
        assert "display:none" in _read_html().split("downloadBtnJson")[1][:50]


# ── S10-5: Subtitle Embedding UI ──


class TestEmbedUI:
    def test_embed_mode_selector(self):
        html = _read_html()
        assert 'id="embedTabSoft"' in html
        assert "Soft Mux" in html
        assert "Hard Burn" in html

    def test_embed_presets_endpoint(self):
        res = client.get("/embed/presets")
        assert res.status_code == 200
        data = res.json()
        assert "presets" in data
        assert "default" in data["presets"]
        assert "youtube_white" in data["presets"]


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

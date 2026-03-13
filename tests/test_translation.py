"""Tests for translation service, SRT parsing, and translation API routes."""

from fastapi.testclient import TestClient


class TestSRTParsing:
    """Tests for SRT/VTT parsing utilities."""

    def test_parse_srt_basic(self):
        from app.utils.srt import parse_srt, segments_to_srt
        segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello world"},
            {"start": 3.0, "end": 5.5, "text": "Second line"},
        ]
        srt = segments_to_srt(segments, include_speakers=False)
        parsed = parse_srt(srt)
        assert len(parsed) == 2
        assert parsed[0]["text"] == "Hello world"
        assert parsed[1]["text"] == "Second line"
        assert abs(parsed[0]["start"] - 0.0) < 0.01
        assert abs(parsed[0]["end"] - 2.5) < 0.01
        assert abs(parsed[1]["start"] - 3.0) < 0.01
        assert abs(parsed[1]["end"] - 5.5) < 0.01

    def test_parse_srt_roundtrip(self):
        """Generate SRT, parse it, verify segments match."""
        from app.utils.srt import parse_srt, segments_to_srt
        original = [
            {"start": 10.5, "end": 15.123, "text": "Test segment one"},
            {"start": 20.0, "end": 25.999, "text": "Test segment two"},
            {"start": 3661.0, "end": 3665.5, "text": "Over an hour in"},
        ]
        srt = segments_to_srt(original, include_speakers=False)
        parsed = parse_srt(srt)
        assert len(parsed) == len(original)
        for orig, p in zip(original, parsed):
            assert abs(orig["start"] - p["start"]) < 0.01
            assert abs(orig["end"] - p["end"]) < 0.01
            assert orig["text"] == p["text"]

    def test_parse_srt_multiline(self):
        """Handle multi-line subtitle text."""
        from app.utils.srt import parse_srt
        srt = "1\n00:00:01,000 --> 00:00:03,000\nLine one\nLine two\n\n"
        parsed = parse_srt(srt)
        assert len(parsed) == 1
        assert "Line one\nLine two" == parsed[0]["text"]

    def test_parse_srt_empty(self):
        from app.utils.srt import parse_srt
        assert parse_srt("") == []
        assert parse_srt("   ") == []

    def test_parse_vtt_basic(self):
        from app.utils.srt import parse_vtt, segments_to_vtt
        segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello VTT"},
            {"start": 3.0, "end": 5.5, "text": "Second cue"},
        ]
        vtt = segments_to_vtt(segments, include_speakers=False)
        parsed = parse_vtt(vtt)
        assert len(parsed) == 2
        assert parsed[0]["text"] == "Hello VTT"
        assert parsed[1]["text"] == "Second cue"

    def test_parse_vtt_empty(self):
        from app.utils.srt import parse_vtt
        assert parse_vtt("WEBVTT\n\n") == []


class TestTranslationService:
    """Tests for the translation service."""

    def test_translate_same_lang_noop(self):
        from app.services.translation import translate_segments
        segments = [{"start": 0, "end": 1, "text": "Hello"}]
        result = translate_segments(segments, "en", "en", "test1234")
        assert result == segments

    def test_translate_to_english_passthrough(self):
        """English target defers to Whisper — returns segments unchanged."""
        from app.services.translation import translate_segments
        segments = [{"start": 0, "end": 1, "text": "Bonjour"}]
        result = translate_segments(segments, "fr", "en", "test1234")
        assert result == segments

    def test_translate_preserves_timing(self):
        """Timing should be unchanged after translation."""
        from app.services.translation import translate_segments
        segments = [
            {"start": 1.5, "end": 3.0, "text": "Hello"},
            {"start": 4.0, "end": 6.0, "text": "World"},
        ]
        # Without argos model, segments come back with original text
        result = translate_segments(segments, "en", "fr", "test1234")
        assert len(result) == 2
        assert result[0]["start"] == 1.5
        assert result[0]["end"] == 3.0
        assert result[1]["start"] == 4.0
        assert result[1]["end"] == 6.0

    def test_translate_preserves_original_text(self):
        """When no model available, original_text field should be preserved."""
        from app.services.translation import translate_segments
        segments = [{"start": 0, "end": 1, "text": "Hello"}]
        result = translate_segments(segments, "en", "fr", "test1234")
        assert result[0]["original_text"] == "Hello"

    def test_is_translation_available_english(self):
        from app.services.translation import is_translation_available
        result = is_translation_available("en")
        assert result["available"] is True
        assert result["method"] == "whisper_translate"

    def test_is_translation_available_other(self):
        """Non-English targets check argos availability."""
        from app.services.translation import is_translation_available
        result = is_translation_available("fr")
        # With mock returning empty packages, it won't find the pair
        assert isinstance(result, dict)
        assert "available" in result

    def test_get_whisper_translate_options(self):
        from app.services.translation import get_whisper_translate_options
        opts = get_whisper_translate_options()
        assert opts == {"task": "translate"}

    def test_get_available_languages(self):
        from app.services.translation import get_available_languages
        result = get_available_languages()
        assert isinstance(result, list)
        # Should always include English via Whisper
        en_targets = [p for p in result if p["target"] == "en"]
        assert len(en_targets) >= 1


class TestTranslationAPI:
    """Tests for translation API endpoints."""

    def setup_method(self):
        from app.main import app
        self.client = TestClient(app, base_url="https://testserver")

    def test_translation_languages_endpoint(self):
        resp = self.client.get("/translation/languages")
        assert resp.status_code == 200
        data = resp.json()
        assert "pairs" in data
        assert "count" in data
        assert isinstance(data["pairs"], list)

    def test_translation_status_english(self):
        resp = self.client.get("/translation/status/en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["method"] == "whisper_translate"

    def test_translation_status_other(self):
        resp = self.client.get("/translation/status/fr")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data

    def test_install_english_noop(self):
        resp = self.client.post("/translation/install?source=en&target=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["installed"] is True

    def test_install_missing_target(self):
        resp = self.client.post("/translation/install")
        assert resp.status_code == 400


class TestUploadTranslateParam:
    """Tests that upload route accepts translate_to parameter."""

    def setup_method(self):
        from app.main import app
        self.client = TestClient(app, base_url="https://testserver")

    def test_upload_accepts_translate_to(self):
        """Upload should accept translate_to as a form field (even if file is invalid)."""
        import io
        resp = self.client.post("/upload", data={
            "device": "cpu",
            "model_size": "tiny",
            "language": "auto",
            "translate_to": "fr",
        }, files={
            "file": ("test.mp4", io.BytesIO(b"not a real video"), "video/mp4"),
        })
        # Will fail validation (too small / bad magic bytes), but not because of translate_to
        assert resp.status_code in (400, 413)


class TestEmbedTranslateParam:
    """Tests that embed routes accept translate_to parameter."""

    def setup_method(self):
        from app.main import app
        self.client = TestClient(app, base_url="https://testserver")

    def test_embed_accepts_translate_to(self):
        """Quick embed should accept translate_to form field."""
        resp = self.client.post("/embed/nonexistent-task/quick", data={
            "mode": "soft",
            "translate_to": "es",
        })
        # Should fail with 404 (task not found), not 422 (validation error)
        assert resp.status_code == 404

    def test_combine_accepts_translate_to(self):
        """Combine should accept translate_to form field."""
        import io
        resp = self.client.post("/combine", data={
            "mode": "soft",
            "translate_to": "de",
        }, files={
            "video": ("test.mp4", io.BytesIO(b"x" * 2000), "video/mp4"),
            "subtitle": ("test.srt", io.BytesIO(b"1\n00:00:01,000 --> 00:00:02,000\nHello\n\n"), "text/plain"),
        })
        # Will fail validation (bad magic bytes), but not because of translate_to
        assert resp.status_code in (400, 413)

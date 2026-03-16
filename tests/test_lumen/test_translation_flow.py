"""Phase Lumen L8 — Translation flow tests.

Tests translation endpoints, language listing, parameter validation,
Whisper translate mode, Argos availability, and edge cases.
— Scout (QA Lead)
"""

import struct
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.translation import (
    get_whisper_translate_options,
    is_translation_available,
    translate_segments,
)

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGES ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestLanguagesEndpoint:
    """Test GET /languages."""

    def test_languages_returns_200(self):
        res = client.get("/languages")
        assert res.status_code == 200

    def test_languages_has_languages_key(self):
        data = client.get("/languages").json()
        assert "languages" in data

    def test_languages_is_dict(self):
        data = client.get("/languages").json()
        assert isinstance(data["languages"], dict)

    def test_languages_has_english(self):
        data = client.get("/languages").json()
        assert "en" in data["languages"]
        assert data["languages"]["en"] == "English"

    def test_languages_has_auto(self):
        data = client.get("/languages").json()
        assert "auto" in data["languages"]

    def test_languages_has_chinese(self):
        data = client.get("/languages").json()
        assert "zh" in data["languages"]

    def test_languages_has_spanish(self):
        data = client.get("/languages").json()
        assert "es" in data["languages"]

    def test_languages_has_french(self):
        data = client.get("/languages").json()
        assert "fr" in data["languages"]

    def test_languages_has_japanese(self):
        data = client.get("/languages").json()
        assert "ja" in data["languages"]

    def test_languages_has_arabic(self):
        data = client.get("/languages").json()
        assert "ar" in data["languages"]

    def test_languages_count_over_90(self):
        data = client.get("/languages").json()
        assert len(data["languages"]) > 90


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATION LANGUAGES ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestTranslationLanguages:
    """Test GET /translation/languages."""

    def test_translation_languages_returns_200(self):
        res = client.get("/translation/languages")
        assert res.status_code == 200

    def test_translation_languages_has_pairs(self):
        data = client.get("/translation/languages").json()
        assert "pairs" in data

    def test_translation_languages_has_count(self):
        data = client.get("/translation/languages").json()
        assert "count" in data

    def test_translation_languages_is_list(self):
        data = client.get("/translation/languages").json()
        assert isinstance(data["pairs"], list)

    def test_translation_english_always_available(self):
        data = client.get("/translation/languages").json()
        targets = [p["target"] for p in data["pairs"]]
        assert "en" in targets


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATION STATUS
# ══════════════════════════════════════════════════════════════════════════════


class TestTranslationStatus:
    """Test GET /translation/status/{target}."""

    def test_english_target_available(self):
        res = client.get("/translation/status/en")
        assert res.status_code == 200
        data = res.json()
        assert data["available"] is True
        assert data["method"] == "whisper_translate"

    def test_unknown_language_status(self):
        res = client.get("/translation/status/xx")
        assert res.status_code == 200
        data = res.json()
        assert "available" in data


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATION INSTALL
# ══════════════════════════════════════════════════════════════════════════════


class TestTranslationInstall:
    """Test POST /translation/install."""

    def test_install_english_no_download(self):
        res = client.post("/translation/install?source=en&target=en")
        assert res.status_code == 200
        assert res.json()["installed"] is True

    def test_install_missing_target(self):
        res = client.post("/translation/install?source=en")
        assert res.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# WHISPER TRANSLATE OPTIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestWhisperTranslate:
    """Test Whisper translate mode (any -> English)."""

    def test_whisper_translate_options(self):
        opts = get_whisper_translate_options()
        assert opts == {"task": "translate"}

    def test_is_translation_available_english(self):
        result = is_translation_available("en")
        assert result["available"] is True
        assert result["method"] == "whisper_translate"

    def test_is_translation_available_unknown(self):
        result = is_translation_available("zz")
        assert "available" in result


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATE SEGMENTS
# ══════════════════════════════════════════════════════════════════════════════


class TestTranslateSegments:
    """Test translate_segments function."""

    def test_same_language_returns_unchanged(self):
        segs = [{"start": 0, "end": 1, "text": "Hello"}]
        result = translate_segments(segs, "en", "en")
        assert result[0]["text"] == "Hello"

    def test_same_language_no_original_text(self):
        segs = [{"start": 0, "end": 1, "text": "Hello"}]
        result = translate_segments(segs, "en", "en")
        # same lang = passthrough, no original_text
        assert "original_text" not in result[0]

    def test_to_english_passthrough(self):
        segs = [{"start": 0, "end": 1, "text": "Bonjour"}]
        result = translate_segments(segs, "fr", "en")
        # Whisper translate mode — returns segments unchanged
        assert result[0]["text"] == "Bonjour"

    def test_empty_segments(self):
        result = translate_segments([], "en", "fr")
        assert result == []

    def test_unsupported_pair_preserves_text(self):
        segs = [{"start": 0, "end": 1, "text": "Hello"}]
        result = translate_segments(segs, "en", "zz", task_id="test-123")
        assert result[0]["text"] == "Hello"
        assert result[0].get("original_text") == "Hello"

    def test_multiple_segments(self):
        segs = [
            {"start": 0, "end": 1, "text": "First"},
            {"start": 1, "end": 2, "text": "Second"},
            {"start": 2, "end": 3, "text": "Third"},
        ]
        result = translate_segments(segs, "en", "zz", task_id="test-multi")
        assert len(result) == 3

    def test_preserves_timing(self):
        segs = [{"start": 5.5, "end": 10.2, "text": "Test"}]
        result = translate_segments(segs, "en", "zz", task_id="test-timing")
        assert result[0]["start"] == 5.5
        assert result[0]["end"] == 10.2


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD WITH TRANSLATION PARAMS
# ══════════════════════════════════════════════════════════════════════════════


class TestUploadTranslationParams:
    """Test upload endpoint translation parameters."""

    def test_upload_with_translate_to_english(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt", "translate_to_english": "true"},
        )
        assert res.status_code == 200

    def test_upload_with_translate_to(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt", "translate_to": "es"},
        )
        assert res.status_code == 200

    def test_upload_with_invalid_translate_to(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt", "translate_to": "zzzzz"},
        )
        # Invalid language should be silently ignored
        assert res.status_code == 200

    def test_upload_with_language_param(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt", "language": "fr"},
        )
        assert res.status_code == 200
        assert res.json()["language"] == "fr"

    def test_upload_auto_language(self):
        wav = _make_wav_bytes()
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt", "language": "auto"},
        )
        assert res.status_code == 200
        assert res.json()["language"] == "auto"


# ══════════════════════════════════════════════════════════════════════════════
# ARGOS LANGUAGE MAPPING
# ══════════════════════════════════════════════════════════════════════════════


class TestArgosLanguageMapping:
    """Test language code mapping for Argos translate."""

    def test_argos_lang_map_javanese(self):
        from app.services.translation import _to_argos_code

        assert _to_argos_code("jw") == "jv"

    def test_argos_lang_map_standard(self):
        from app.services.translation import _to_argos_code

        assert _to_argos_code("en") == "en"
        assert _to_argos_code("fr") == "fr"
        assert _to_argos_code("de") == "de"

    def test_argos_lang_map_chinese(self):
        from app.services.translation import _to_argos_code

        assert _to_argos_code("zh") == "zh"

    def test_argos_lang_map_hebrew(self):
        from app.services.translation import _to_argos_code

        assert _to_argos_code("he") == "he"

    def test_argos_unknown_passthrough(self):
        from app.services.translation import _to_argos_code

        assert _to_argos_code("xx") == "xx"

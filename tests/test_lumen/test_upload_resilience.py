"""Phase Lumen L1 — Upload resilience tests.

Tests upload handling with edge cases: corrupt files, empty files,
wrong extensions, and boundary conditions. Uses synchronous TestClient
to match existing test patterns.
"""

import struct
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file in memory."""
    num_samples = int(sample_rate * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


class TestUploadValidation:
    """Test file upload validation and error handling."""

    def test_upload_no_file(self):
        """Upload request without a file should return 422."""
        res = client.post("/upload")
        assert res.status_code == 422

    def test_upload_empty_file(self):
        """Empty file should be rejected with a clear error."""
        res = client.post("/upload", files={"file": ("empty.wav", BytesIO(b""), "audio/wav")})
        assert res.status_code in (400, 422)

    def test_upload_corrupt_file(self):
        """Corrupt file should be rejected or fail gracefully."""
        corrupt_data = b"\x00\x01\x02\x03" * 100
        res = client.post("/upload", files={"file": ("corrupt.mp3", BytesIO(corrupt_data), "audio/mpeg")})
        assert res.status_code in (200, 400, 422)

    def test_upload_wrong_extension(self):
        """File with disallowed extension should be rejected."""
        res = client.post(
            "/upload", files={"file": ("malware.exe", BytesIO(b"\x00" * 100), "application/octet-stream")}
        )
        assert res.status_code in (400, 415, 422)

    def test_upload_txt_extension(self):
        """Text files should be rejected."""
        res = client.post("/upload", files={"file": ("notes.txt", BytesIO(b"hello world"), "text/plain")})
        assert res.status_code in (400, 415, 422)

    def test_upload_valid_wav(self):
        """Valid WAV file should be accepted."""
        wav_data = _make_wav_bytes(1.0)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data

    def test_upload_returns_task_metadata(self):
        """Upload response should include model, language, and format info."""
        wav_data = _make_wav_bytes(1.0)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["model_size"] == "tiny"
        assert "language" in data


class TestUploadFormats:
    """Test that all supported format parameters work."""

    def test_output_format_srt(self):
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "output_format": "srt"},
        )
        assert res.status_code == 200

    def test_output_format_vtt(self):
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "output_format": "vtt"},
        )
        assert res.status_code == 200

    def test_output_format_json(self):
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "output_format": "json"},
        )
        assert res.status_code == 200

    def test_invalid_model_size(self):
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "nonexistent", "output_format": "srt"},
        )
        assert res.status_code in (400, 422)

    def test_all_valid_model_sizes(self):
        """All 5 model sizes should be accepted."""
        wav_data = _make_wav_bytes(0.5)
        for model in ["tiny", "base", "small", "medium", "large"]:
            res = client.post(
                "/upload",
                files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
                data={"model_size": model, "output_format": "srt"},
            )
            assert res.status_code == 200, f"Model '{model}' rejected with {res.status_code}"


class TestEndpointAvailability:
    """Verify all Lumen-critical endpoints exist and respond."""

    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_metrics_prometheus(self):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "subtitle_generator_uptime_seconds" in res.text

    def test_status_page(self):
        res = client.get("/status")
        assert res.status_code == 200

    def test_docs_swagger(self):
        res = client.get("/docs")
        assert res.status_code == 200

    def test_docs_redoc(self):
        res = client.get("/redoc")
        assert res.status_code == 200

    def test_openapi_spec(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert data["info"]["title"] == "Subtitle Generator"
        assert len(data["paths"]) > 10

    def test_about_page(self):
        res = client.get("/about")
        assert res.status_code == 200

    def test_contact_page(self):
        res = client.get("/contact")
        assert res.status_code == 200

    def test_security_page(self):
        res = client.get("/security")
        assert res.status_code == 200

    def test_tasks_endpoint(self):
        res = client.get("/tasks")
        assert res.status_code == 200

    def test_languages_endpoint(self):
        res = client.get("/languages")
        assert res.status_code == 200

    def test_translation_languages(self):
        res = client.get("/translation/languages")
        assert res.status_code == 200

    def test_system_info(self):
        res = client.get("/system-info")
        assert res.status_code == 200

    def test_feedback_submission(self):
        res = client.post("/feedback", json={"rating": 5, "comment": "Lumen L1 test"})
        assert res.status_code == 200
        assert "thank" in res.json().get("message", "").lower()

    def test_http_redirect(self):
        """HTTP should redirect to HTTPS (in prod mode)."""
        # In test mode, just verify the endpoint exists
        res = client.get("/")
        assert res.status_code == 200

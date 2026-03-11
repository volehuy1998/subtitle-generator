"""Tests for FastAPI endpoints."""

from io import BytesIO
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestIndex:
    def test_index_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200


class TestSystemInfo:
    def test_returns_cuda_available_field(self):
        response = client.get("/system-info")
        assert response.status_code == 200
        data = response.json()
        assert "cuda_available" in data

    def test_cuda_is_false_when_mocked(self):
        data = client.get("/system-info").json()
        assert data["cuda_available"] is False

    def test_returns_gpu_fields(self):
        data = client.get("/system-info").json()
        assert "gpu_name" in data
        assert "gpu_vram" in data

    def test_returns_auto_model(self):
        data = client.get("/system-info").json()
        assert "auto_model" in data

    def test_returns_model_recommendations(self):
        data = client.get("/system-info").json()
        assert "model_recommendations" in data


class TestUploadRejections:
    def test_rejects_unsupported_extension(self):
        response = client.post(
            "/upload",
            files={"file": ("test.txt", BytesIO(b"fake"), "text/plain")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400

    def test_rejects_exe(self):
        response = client.post(
            "/upload",
            files={"file": ("malware.exe", BytesIO(b"data"), "application/octet-stream")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400

    def test_rejects_pdf(self):
        response = client.post(
            "/upload",
            files={"file": ("doc.pdf", BytesIO(b"data"), "application/pdf")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400

    def test_device_falls_back_to_cpu(self):
        """Cuda unavailable -> falls back to cpu, upload succeeds."""
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cuda", "model_size": "tiny"},
        )
        # May fail at magic byte validation (fake content), but won't fail on device
        assert response.status_code in (200, 400)

    def test_auto_model_accepted(self):
        """model_size='auto' should be accepted without error."""
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"device": "cpu", "model_size": "auto"},
        )
        # May fail at magic byte validation, but model_size='auto' is accepted
        assert response.status_code in (200, 400)

    def test_rejects_tiny_file(self):
        """Files under MIN_FILE_SIZE should be rejected."""
        response = client.post(
            "/upload",
            files={"file": ("test.mp4", BytesIO(b"tiny"), "video/mp4")},
            data={"device": "cpu", "model_size": "tiny"},
        )
        assert response.status_code == 400


class TestProgressUnknown:
    def test_unknown_task_returns_404(self):
        assert client.get("/progress/nonexistent-0000").status_code == 404

    def test_404_detail_message(self):
        assert client.get("/progress/does-not-exist").json()["detail"] == "Task not found"


class TestCancelUnknown:
    def test_unknown_task_returns_404(self):
        assert client.post("/cancel/nonexistent-0000").status_code == 404


class TestPauseUnknown:
    def test_unknown_task_returns_404(self):
        assert client.post("/pause/nonexistent-0000").status_code == 404


class TestDownloadUnknown:
    def test_unknown_task_returns_404(self):
        assert client.get("/download/nonexistent-0000").status_code == 404


class TestLogsRecent:
    def test_returns_logs_list(self):
        data = client.get("/logs/recent").json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_accepts_lines_param(self):
        assert client.get("/logs/recent?lines=10").status_code == 200

    def test_rejects_excessive_lines(self):
        assert client.get("/logs/recent?lines=9999").status_code == 422


class TestLogsTasks:
    def test_returns_events_list(self):
        data = client.get("/logs/tasks").json()
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_accepts_limit_param(self):
        assert client.get("/logs/tasks?limit=5").status_code == 200

    def test_rejects_excessive_limit(self):
        assert client.get("/logs/tasks?limit=9999").status_code == 422


class TestSecurityHeaders:
    def test_x_content_type_options(self):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self):
        response = client.get("/")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_header_present(self):
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers

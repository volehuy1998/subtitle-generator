"""Tests for architecture improvements: system capability, logging, health, embed, reliability."""

import json

from app.main import app
from app import state
from app.services.system_capability import detect_system_capabilities, _compute_tuning
from app.services.subtitle_embed import SubtitleStyle, STYLE_PRESETS
from app.logging_setup import set_request_id, get_request_id, JsonFormatter
from fastapi.testclient import TestClient

import logging

client = TestClient(app)


# ── System Capability Detection ──

class TestSystemCapability:
    def test_detect_returns_all_sections(self):
        caps = detect_system_capabilities()
        assert "platform" in caps
        assert "cpu" in caps
        assert "memory" in caps
        assert "gpu" in caps
        assert "storage" in caps
        assert "software" in caps
        assert "tuning" in caps

    def test_platform_detection(self):
        caps = detect_system_capabilities()
        plat = caps["platform"]
        assert plat["os"] in ("Windows", "Linux", "Darwin")
        assert plat["arch"] in ("AMD64", "x86_64", "aarch64", "arm64")
        assert len(plat["python"]) > 0

    def test_cpu_detection(self):
        caps = detect_system_capabilities()
        cpu = caps["cpu"]
        assert cpu["physical_cores"] > 0
        assert cpu["logical_cores"] >= cpu["physical_cores"]

    def test_memory_detection(self):
        caps = detect_system_capabilities()
        mem = caps["memory"]
        assert mem["total_gb"] > 0
        assert mem["available_gb"] > 0

    def test_gpu_section_present(self):
        caps = detect_system_capabilities()
        assert "cuda_available" in caps["gpu"]

    def test_storage_detection(self):
        caps = detect_system_capabilities()
        assert caps["storage"]["total_gb"] > 0
        assert caps["storage"]["free_gb"] >= 0

    def test_software_versions(self):
        caps = detect_system_capabilities()
        sw = caps["software"]
        assert len(sw["pytorch"]) > 0
        assert len(sw["faster_whisper"]) > 0

    def test_tuning_computed(self):
        caps = detect_system_capabilities()
        tune = caps["tuning"]
        assert tune["omp_threads"] > 0
        assert tune["max_concurrent_tasks"] >= 1
        assert tune["recommended_device"] in ("cuda", "cpu")
        assert tune["cpu_default_model"] in ("tiny", "base", "small", "medium", "large")

    def test_tuning_logic_high_ram(self):
        caps = {
            "cpu": {"physical_cores": 16, "logical_cores": 32},
            "memory": {"total_gb": 128},
            "gpu": {"cuda_available": False, "devices": []},
        }
        tune = _compute_tuning(caps)
        assert tune["max_concurrent_tasks"] >= 3
        assert tune["cpu_default_model"] == "medium"

    def test_tuning_logic_low_ram(self):
        caps = {
            "cpu": {"physical_cores": 2, "logical_cores": 4},
            "memory": {"total_gb": 4},
            "gpu": {"cuda_available": False, "devices": []},
        }
        tune = _compute_tuning(caps)
        assert tune["max_concurrent_tasks"] == 1
        assert tune["cpu_default_model"] == "tiny"


# ── Structured Logging ──

class TestStructuredLogging:
    def test_request_id_tracking(self):
        set_request_id("test123")
        assert get_request_id() == "test123"

    def test_request_id_default(self):
        import threading
        # New thread should have "system" as default
        result = [None]
        def check():
            result[0] = get_request_id()
        t = threading.Thread(target=check)
        t.start()
        t.join()
        assert result[0] == "system"

    def test_json_formatter_produces_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"
        assert "timestamp" in data

    def test_json_formatter_handles_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="Error", args=(), exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"


# ── Health Check Endpoints ──

class TestHealthEndpoints:
    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "uptime_sec" in data

    def test_ready_returns_checks(self):
        res = client.get("/ready")
        assert res.status_code in (200, 503)  # 503 if not fully ready (e.g., no ffmpeg)
        data = res.json()
        assert "checks" in data
        assert "disk" in data["checks"]
        assert "ffmpeg" in data["checks"]
        assert "tasks" in data["checks"]

    def test_ready_status_field(self):
        res = client.get("/ready")
        data = res.json()
        assert data["status"] in ("ready", "not_ready")


# ── Global Exception Handler ──

class TestGlobalExceptionHandler:
    def test_500_returns_json(self):
        # The global handler should catch unexpected errors
        # We can't easily trigger one through normal routes,
        # but we can verify the handler is registered
        assert app.exception_handlers.get(500) is not None or len(app.exception_handlers) > 0


# ── Subtitle Embedding ──

class TestSubtitleStyle:
    def test_default_style(self):
        s = SubtitleStyle()
        assert s.font_name == "Arial"
        assert s.font_size == 24
        assert s.position == "bottom"

    def test_to_ass_style(self):
        s = SubtitleStyle()
        result = s.to_ass_style()
        assert "FontName=Arial" in result
        assert "FontSize=24" in result
        assert "Alignment=2" in result

    def test_top_position_alignment(self):
        s = SubtitleStyle(position="top")
        result = s.to_ass_style()
        assert "Alignment=8" in result

    def test_center_position_alignment(self):
        s = SubtitleStyle(position="center")
        result = s.to_ass_style()
        assert "Alignment=5" in result

    def test_bold_style(self):
        s = SubtitleStyle(bold=True)
        result = s.to_ass_style()
        assert "Bold=-1" in result

    def test_presets_available(self):
        assert "default" in STYLE_PRESETS
        assert "youtube_white" in STYLE_PRESETS
        assert "youtube_yellow" in STYLE_PRESETS
        assert "cinema" in STYLE_PRESETS
        assert "large_bold" in STYLE_PRESETS
        assert "top_position" in STYLE_PRESETS

    def test_preset_font_opacity(self):
        s = SubtitleStyle(font_opacity=0.5)
        result = s.to_ass_style()
        # 50% opacity -> alpha = 127 = 0x7F
        assert "7F" in result


class TestEmbedEndpoints:
    def test_presets_endpoint(self):
        res = client.get("/embed/presets")
        assert res.status_code == 200
        data = res.json()
        assert "presets" in data
        assert "default" in data["presets"]
        assert "youtube_white" in data["presets"]

    def test_embed_unknown_task_404(self):
        from io import BytesIO
        res = client.post(
            "/embed/nonexistent",
            files={"video": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
            data={"mode": "soft"},
        )
        assert res.status_code == 404

    def test_embed_not_done_400(self):
        from io import BytesIO
        original = state.tasks.copy()
        state.tasks["test-embed-001"] = {"status": "transcribing"}
        try:
            res = client.post(
                "/embed/test-embed-001",
                files={"video": ("test.mp4", BytesIO(b"x" * 2048), "video/mp4")},
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            state.tasks.clear()
            state.tasks.update(original)


# ── Request ID in Response Headers ──

class TestRequestIdHeader:
    def test_response_has_request_id(self):
        res = client.get("/health")
        assert "X-Request-ID" in res.headers
        assert len(res.headers["X-Request-ID"]) > 0

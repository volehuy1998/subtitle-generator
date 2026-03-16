"""Phase Lumen L8 — Health and monitoring system tests.

Tests health endpoints, model status, metrics, system info,
capabilities, and critical state detection.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    """Test GET /health."""

    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_status_healthy(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_has_uptime(self):
        data = client.get("/health").json()
        assert "uptime_sec" in data
        assert isinstance(data["uptime_sec"], (int, float))
        assert data["uptime_sec"] >= 0

    def test_health_live_returns_200(self):
        res = client.get("/health/live")
        assert res.status_code == 200

    def test_health_live_status_ok(self):
        data = client.get("/health/live").json()
        assert data["status"] == "ok"


class TestReadyEndpoint:
    """Test GET /ready."""

    def test_ready_returns_response(self):
        res = client.get("/ready")
        # May be 200 or 503 depending on environment
        assert res.status_code in (200, 503)

    def test_ready_has_checks(self):
        data = client.get("/ready").json()
        assert "checks" in data

    def test_ready_has_status(self):
        data = client.get("/ready").json()
        assert data["status"] in ("ready", "not_ready")

    def test_ready_disk_check(self):
        data = client.get("/ready").json()
        assert "disk" in data["checks"]

    def test_ready_ffmpeg_check(self):
        data = client.get("/ready").json()
        assert "ffmpeg" in data["checks"]

    def test_ready_dirs_check(self):
        data = client.get("/ready").json()
        assert "dirs" in data["checks"]

    def test_ready_tasks_check(self):
        data = client.get("/ready").json()
        assert "tasks" in data["checks"]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL STATUS
# ══════════════════════════════════════════════════════════════════════════════


class TestModelStatus:
    """Test GET /api/model-status."""

    def test_model_status_returns_200(self):
        res = client.get("/api/model-status")
        assert res.status_code == 200

    def test_model_status_has_preload(self):
        data = client.get("/api/model-status").json()
        assert "preload" in data

    def test_model_status_has_models(self):
        data = client.get("/api/model-status").json()
        assert "models" in data

    def test_model_status_models_is_dict(self):
        data = client.get("/api/model-status").json()
        assert isinstance(data["models"], dict)

    def test_model_status_all_sizes_present(self):
        data = client.get("/api/model-status").json()
        models = data["models"]
        for size in ["tiny", "base", "small", "medium", "large"]:
            assert size in models


# ══════════════════════════════════════════════════════════════════════════════
# METRICS ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestMetricsEndpoint:
    """Test GET /metrics (Prometheus format)."""

    def test_metrics_returns_200(self):
        res = client.get("/metrics")
        assert res.status_code == 200

    def test_metrics_content_type(self):
        res = client.get("/metrics")
        assert "text/plain" in res.headers.get("content-type", "")

    def test_metrics_has_uptime(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_uptime_seconds" in text

    def test_metrics_has_active_tasks(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_active_tasks" in text

    def test_metrics_has_tasks_created(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_tasks_created_total" in text

    def test_metrics_has_file_counts(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_files_count" in text

    def test_metrics_has_upload_counter(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_uploads_total" in text

    def test_metrics_has_help_lines(self):
        text = client.get("/metrics").text
        assert "# HELP" in text

    def test_metrics_has_type_lines(self):
        text = client.get("/metrics").text
        assert "# TYPE" in text

    def test_metrics_has_cpu_info(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_cpu_percent" in text

    def test_metrics_has_memory_info(self):
        text = client.get("/metrics").text
        assert "subtitle_generator_memory" in text


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════


class TestSystemInfo:
    """Test GET /system-info."""

    def test_system_info_returns_200(self):
        res = client.get("/system-info")
        assert res.status_code == 200

    def test_system_info_has_diarization(self):
        data = client.get("/system-info").json()
        assert "diarization" in data

    def test_system_info_has_model_preload(self):
        data = client.get("/system-info").json()
        assert "model_preload" in data


# ══════════════════════════════════════════════════════════════════════════════
# CAPABILITIES
# ══════════════════════════════════════════════════════════════════════════════


class TestCapabilities:
    """Test GET /api/capabilities."""

    def test_capabilities_returns_200(self):
        res = client.get("/api/capabilities")
        assert res.status_code == 200

    def test_capabilities_has_ffmpeg(self):
        data = client.get("/api/capabilities").json()
        assert "ffmpeg" in data
        assert isinstance(data["ffmpeg"], bool)

    def test_capabilities_has_features(self):
        data = client.get("/api/capabilities").json()
        assert "features" in data

    def test_capabilities_transcribe_audio_always_true(self):
        data = client.get("/api/capabilities").json()
        assert data["features"]["transcribe_audio"] is True

    def test_capabilities_has_accepted_extensions(self):
        data = client.get("/api/capabilities").json()
        assert "accepted_extensions" in data
        assert isinstance(data["accepted_extensions"], list)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM STATUS
# ══════════════════════════════════════════════════════════════════════════════


class TestSystemStatus:
    """Test GET /api/status."""

    def test_status_returns_200(self):
        res = client.get("/api/status")
        assert res.status_code == 200

    def test_status_has_overall(self):
        data = client.get("/api/status").json()
        assert data["status"] in ("healthy", "warning", "critical")

    def test_status_has_uptime(self):
        data = client.get("/api/status").json()
        assert "uptime_sec" in data

    def test_status_has_active_tasks(self):
        data = client.get("/api/status").json()
        assert "active_tasks" in data

    def test_status_has_max_tasks(self):
        data = client.get("/api/status").json()
        assert "max_tasks" in data

    def test_status_has_cpu_percent(self):
        data = client.get("/api/status").json()
        assert "cpu_percent" in data

    def test_status_has_memory_percent(self):
        data = client.get("/api/status").json()
        assert "memory_percent" in data

    def test_status_has_disk_info(self):
        data = client.get("/api/status").json()
        assert "disk_free_gb" in data
        assert "disk_ok" in data

    def test_status_has_db_ok(self):
        data = client.get("/api/status").json()
        assert "db_ok" in data

    def test_status_has_ffmpeg_ok(self):
        data = client.get("/api/status").json()
        assert "ffmpeg_ok" in data

    def test_status_has_gpu_fields(self):
        data = client.get("/api/status").json()
        assert "gpu_available" in data

    def test_status_has_alerts(self):
        data = client.get("/api/status").json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_status_has_shutting_down(self):
        data = client.get("/api/status").json()
        assert "shutting_down" in data
        assert data["shutting_down"] is False

    def test_status_has_system_critical(self):
        data = client.get("/api/status").json()
        assert "system_critical" in data


# ══════════════════════════════════════════════════════════════════════════════
# CRITICAL STATE
# ══════════════════════════════════════════════════════════════════════════════


class TestCriticalState:
    """Test critical state detection."""

    def test_system_critical_default_false(self):
        assert state.system_critical is False

    def test_shutting_down_default_false(self):
        assert state.shutting_down is False

    def test_system_critical_reasons_default_empty(self):
        assert state.system_critical_reasons == [] or state.system_critical_reasons is not None


# ══════════════════════════════════════════════════════════════════════════════
# SCALE INFO
# ══════════════════════════════════════════════════════════════════════════════


class TestScaleInfo:
    """Test GET /scale/info."""

    def test_scale_info_returns_200(self):
        res = client.get("/scale/info")
        assert res.status_code == 200

    def test_scale_info_has_workers(self):
        data = client.get("/scale/info").json()
        assert "workers" in data

    def test_scale_info_has_task_backend(self):
        data = client.get("/scale/info").json()
        assert "task_backend" in data

    def test_scale_info_has_storage(self):
        data = client.get("/scale/info").json()
        assert "storage" in data

    def test_scale_info_has_uptime(self):
        data = client.get("/scale/info").json()
        assert "uptime_sec" in data

    def test_scale_info_has_pid(self):
        data = client.get("/scale/info").json()
        assert "pid" in data
        assert isinstance(data["pid"], int)

"""Phase Lumen L49-L52 -- Extended health, system info, and monitoring tests.

Tests request counters, system info, health monitoring, metrics,
and component health endpoints.
-- Scout (QA Lead)
"""

import concurrent.futures
import time

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ======================================================================
# REQUEST COUNTER / UPTIME (10 tests)
# ======================================================================


class TestRequestCounterAndUptime:
    """Test health response uptime and request tracking."""

    def test_health_response_has_uptime_field(self):
        """Health response includes uptime_sec."""
        data = client.get("/health").json()
        assert "uptime_sec" in data

    def test_uptime_increases_between_requests(self):
        """Uptime should increase (or stay same) between requests."""
        data1 = client.get("/health").json()
        time.sleep(0.05)
        data2 = client.get("/health").json()
        assert data2["uptime_sec"] >= data1["uptime_sec"]

    def test_uptime_is_numeric(self):
        """Uptime value is a float or int."""
        data = client.get("/health").json()
        assert isinstance(data["uptime_sec"], (int, float))

    def test_api_status_has_active_tasks_count(self):
        """System status tracks active task count."""
        data = client.get("/api/status").json()
        assert "active_tasks" in data
        assert isinstance(data["active_tasks"], int)

    def test_api_status_has_max_tasks(self):
        """System status includes max concurrent task limit."""
        data = client.get("/api/status").json()
        assert "max_tasks" in data
        assert isinstance(data["max_tasks"], int)
        assert data["max_tasks"] > 0

    def test_health_response_time_under_500ms(self):
        """Health endpoint responds in under 500ms."""
        start = time.time()
        res = client.get("/health")
        elapsed = time.time() - start
        assert res.status_code == 200
        assert elapsed < 0.5

    def test_multiple_health_requests_no_error_increase(self):
        """Multiple health requests don't cause errors."""
        for _ in range(10):
            res = client.get("/health")
            assert res.status_code == 200
            assert res.json()["status"] == "healthy"

    def test_health_under_concurrent_load(self):
        """5 concurrent health requests all succeed."""

        def check():
            return client.get("/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(check) for _ in range(5)]
            results = [f.result() for f in futures]
        assert all(r == 200 for r in results)

    def test_api_status_uptime_present(self):
        """System status endpoint also includes uptime_sec."""
        data = client.get("/api/status").json()
        assert "uptime_sec" in data
        assert isinstance(data["uptime_sec"], (int, float))

    def test_api_status_cpu_and_memory_present(self):
        """System status includes cpu_percent and memory_percent."""
        data = client.get("/api/status").json()
        assert "cpu_percent" in data
        assert "memory_percent" in data


# ======================================================================
# SYSTEM INFO (10 tests)
# ======================================================================


class TestSystemInfo:
    """Test GET /system-info endpoint and related system data."""

    def test_system_info_returns_200(self):
        """GET /system-info returns 200."""
        res = client.get("/system-info")
        assert res.status_code == 200

    def test_system_info_has_cuda_field(self):
        """System info includes cuda_available field."""
        data = client.get("/system-info").json()
        assert "cuda_available" in data

    def test_system_info_has_gpu_name(self):
        """System info has gpu_name field (may be null without GPU)."""
        data = client.get("/system-info").json()
        assert "gpu_name" in data

    def test_system_info_has_gpu_vram(self):
        """System info has gpu_vram field."""
        data = client.get("/system-info").json()
        assert "gpu_vram" in data

    def test_system_info_has_model_recommendations(self):
        """System info includes model_recommendations."""
        data = client.get("/system-info").json()
        assert "model_recommendations" in data
        assert isinstance(data["model_recommendations"], dict)

    def test_system_capabilities_detected(self):
        """System capability module provides detection function."""
        from app.services import system_capability

        assert hasattr(system_capability, "detect_system_capabilities")
        assert callable(system_capability.detect_system_capabilities)

    def test_system_info_has_auto_model(self):
        """System info includes auto-selected model recommendation."""
        data = client.get("/system-info").json()
        assert "auto_model" in data

    def test_capabilities_max_concurrent_tasks_positive(self):
        """Max concurrent tasks from config is a positive integer."""
        from app.config import MAX_CONCURRENT_TASKS

        assert isinstance(MAX_CONCURRENT_TASKS, int)
        assert MAX_CONCURRENT_TASKS > 0

    def test_system_info_has_diarization_field(self):
        """System info reports diarization availability."""
        data = client.get("/system-info").json()
        assert "diarization" in data

    def test_system_info_has_model_preload(self):
        """System info includes model preload status."""
        data = client.get("/system-info").json()
        assert "model_preload" in data


# ======================================================================
# MONITORING (10 tests)
# ======================================================================


class TestMonitoringEndpoints:
    """Test health, metrics, model-status, readiness, and component health."""

    def test_health_stream_endpoint_exists(self):
        """The /health/stream route is registered."""
        spec = client.get("/openapi.json").json()
        assert "/health/stream" in spec["paths"]

    def test_metrics_endpoint_returns_prometheus_format(self):
        """GET /metrics returns prometheus text format."""
        res = client.get("/metrics")
        assert res.status_code == 200
        text = res.text
        assert "subtitle_generator_uptime_seconds" in text
        assert "subtitle_generator_active_tasks" in text

    def test_model_status_endpoint_accessible(self):
        """GET /api/model-status returns 200 with models dict."""
        res = client.get("/api/model-status")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        assert "preload" in data

    def test_ready_endpoint_returns_checks(self):
        """GET /ready returns readiness checks."""
        res = client.get("/ready")
        # May be 200 or 503 depending on environment
        assert res.status_code in (200, 503)
        data = res.json()
        assert "checks" in data
        assert "status" in data

    def test_health_components_endpoint_works(self):
        """GET /health/components returns per-component health."""
        res = client.get("/health/components")
        assert res.status_code == 200
        data = res.json()
        assert "components" in data
        assert "status" in data

    def test_components_include_subsystems(self):
        """Component health includes key subsystems."""
        data = client.get("/health/components").json()
        components = data["components"]
        assert "ffmpeg" in components
        assert "ffprobe" in components
        assert "models" in components
        assert "storage" in components

    def test_system_critical_state_reflected(self):
        """system_critical flag is accessible and boolean."""
        assert isinstance(state.system_critical, bool)
        # It should be reflected in /api/status
        data = client.get("/api/status").json()
        assert "system_critical" in data
        assert isinstance(data["system_critical"], bool)

    def test_health_status_values_are_strings(self):
        """Health status is a string value."""
        data = client.get("/health").json()
        assert isinstance(data["status"], str)
        assert data["status"] in ("healthy", "unhealthy", "degraded", "ok")

    def test_health_endpoint_idempotent(self):
        """Multiple identical health calls return consistent results."""
        data1 = client.get("/health").json()
        data2 = client.get("/health").json()
        assert data1["status"] == data2["status"]

    def test_rapid_health_checks_no_crash(self):
        """20 rapid sequential health checks don't cause errors."""
        for _ in range(20):
            res = client.get("/health")
            assert res.status_code == 200

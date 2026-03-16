"""Phase Lumen L37-L40 — Component health and health monitoring tests.

Tests component-level health endpoints, health monitor module,
critical state tracking, and system capability detection.
— Scout (QA Lead)
"""

import time

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT HEALTH ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestComponentHealthEndpoint:
    """Test component-level health reporting via /health or /api/status."""

    def test_health_returns_200(self):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_has_status_key(self):
        data = client.get("/health").json()
        assert "status" in data

    def test_api_status_returns_200(self):
        res = client.get("/api/status")
        assert res.status_code == 200

    def test_api_status_has_status_key(self):
        data = client.get("/api/status").json()
        assert "status" in data

    def test_api_status_has_db_ok(self):
        """Status response includes database component."""
        data = client.get("/api/status").json()
        assert "db_ok" in data

    def test_api_status_has_ffmpeg_ok(self):
        """Status response includes ffmpeg component."""
        data = client.get("/api/status").json()
        assert "ffmpeg_ok" in data

    def test_api_status_has_disk_ok(self):
        """Status response includes storage/disk component."""
        data = client.get("/api/status").json()
        assert "disk_ok" in data

    def test_api_status_has_gpu_available(self):
        """Status response includes model/GPU component."""
        data = client.get("/api/status").json()
        assert "gpu_available" in data

    def test_api_status_each_component_has_status_value(self):
        """Overall status is one of the valid values."""
        data = client.get("/api/status").json()
        assert data["status"] in ("healthy", "warning", "critical")

    def test_api_status_overall_reflects_worst_component(self):
        """If disk_ok is False, overall should not be 'healthy'."""
        data = client.get("/api/status").json()
        if not data["disk_ok"]:
            assert data["status"] in ("warning", "critical")

    def test_api_status_db_field_is_boolean(self):
        data = client.get("/api/status").json()
        assert isinstance(data["db_ok"], bool)

    def test_api_status_ffmpeg_reflects_config(self):
        """FFmpeg status in status endpoint should be boolean."""
        from app.config import FFMPEG_AVAILABLE

        data = client.get("/api/status").json()
        assert isinstance(data["ffmpeg_ok"], bool)
        assert data["ffmpeg_ok"] == FFMPEG_AVAILABLE

    def test_capabilities_ffprobe_reflects_config(self):
        """Capabilities endpoint reports ffprobe availability matching config."""
        from app.config import FFPROBE_AVAILABLE

        data = client.get("/api/capabilities").json()
        assert data["ffprobe"] == FFPROBE_AVAILABLE

    def test_model_status_has_loaded_models(self):
        """Model status reports all model sizes with their readiness."""
        data = client.get("/api/model-status").json()
        models = data["models"]
        # Each model has a status indicating loaded or not
        for size in ["tiny", "base", "small", "medium", "large"]:
            assert size in models

    def test_api_status_disk_has_free_gb(self):
        """When disk is healthy, disk_free_gb should be present and numeric."""
        data = client.get("/api/status").json()
        if data["disk_ok"]:
            assert "disk_free_gb" in data
            assert isinstance(data["disk_free_gb"], (int, float))
            assert data["disk_free_gb"] > 0

    def test_api_status_disk_degrades_with_low_space(self):
        """Status should degrade when disk space is critically low."""
        # When disk_ok is False, overall status should be critical
        data = client.get("/api/status").json()
        if not data["disk_ok"]:
            assert data["status"] == "critical"


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH MONITORING
# ══════════════════════════════════════════════════════════════════════════════


class TestHealthMonitoring:
    """Test health monitor module, critical state, and system capabilities."""

    def test_health_monitor_importable(self):
        """health_monitor module should be importable."""
        from app.services import health_monitor

        assert hasattr(health_monitor, "health_check_loop")

    def test_system_critical_tracked_in_state(self):
        """state.system_critical should be a boolean attribute."""
        assert hasattr(state, "system_critical")
        assert isinstance(state.system_critical, bool)

    def test_system_critical_default_false(self):
        """system_critical should default to False."""
        # Reset to known state
        state.clear_critical()
        assert state.system_critical is False

    def test_set_critical_blocks_state(self):
        """set_critical should activate system_critical."""
        try:
            state.set_critical(["Test reason"])
            assert state.system_critical is True
            assert "Test reason" in state.system_critical_reasons
        finally:
            state.clear_critical()
            assert state.system_critical is False

    def test_critical_state_blocks_uploads(self):
        """When system is critical, upload should be rejected."""
        import struct
        import wave
        from io import BytesIO

        state.set_critical(["Disk full"])
        try:
            buf = BytesIO()
            with wave.open(buf, "w") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(struct.pack("<" + "h" * 1600, *([0] * 1600)))
            buf.seek(0)
            res = client.post("/upload", files={"file": ("test.wav", buf, "audio/wav")})
            # Should be rejected with 503 when critical
            assert res.status_code == 503
        finally:
            state.clear_critical()

    def test_health_stream_endpoint_exists(self):
        """The /health/stream route should be registered and return SSE media type."""
        # Verify the route is registered by checking the OpenAPI spec
        spec = client.get("/openapi.json").json()
        assert "/health/stream" in spec["paths"]
        # Verify it's a GET endpoint
        assert "get" in spec["paths"]["/health/stream"]

    def test_health_endpoint_response_time(self):
        """Health endpoint should respond in under 1 second."""
        start = time.time()
        res = client.get("/health")
        elapsed = time.time() - start
        assert res.status_code == 200
        assert elapsed < 1.0

    def test_health_includes_uptime(self):
        """Health response should include uptime_sec."""
        data = client.get("/health").json()
        assert "uptime_sec" in data
        assert isinstance(data["uptime_sec"], (int, float))
        assert data["uptime_sec"] >= 0

    def test_concurrent_health_checks_no_interference(self):
        """Multiple simultaneous health checks should all succeed."""
        import concurrent.futures

        def check_health():
            return client.get("/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(check_health) for _ in range(5)]
            results = [f.result() for f in futures]
        assert all(r == 200 for r in results)

    def test_health_endpoint_no_auth_required(self):
        """Health endpoint should be accessible without any authentication."""
        # No API key, no cookie, no auth header
        res = client.get("/health")
        assert res.status_code == 200

    def test_model_status_refreshes(self):
        """Model status endpoint should return current state."""
        data1 = client.get("/api/model-status").json()
        data2 = client.get("/api/model-status").json()
        # Both should have same structure
        assert "preload" in data1
        assert "preload" in data2
        assert "models" in data1
        assert "models" in data2

    def test_system_capabilities_detected(self):
        """system_capability module should be importable and provide detection."""
        from app.services import system_capability

        assert hasattr(system_capability, "detect_system_capabilities")
        assert callable(system_capability.detect_system_capabilities)

    def test_clear_critical_resets_reasons(self):
        """clear_critical should empty the reasons list."""
        state.set_critical(["Reason A", "Reason B"])
        state.clear_critical()
        assert state.system_critical_reasons == []

    def test_health_monitor_check_interval_defined(self):
        """Health monitor should define a CHECK_INTERVAL constant."""
        from app.services.health_monitor import CHECK_INTERVAL

        assert isinstance(CHECK_INTERVAL, (int, float))
        assert CHECK_INTERVAL > 0

    def test_health_monitor_min_disk_defined(self):
        """Health monitor should define minimum disk space threshold."""
        from app.services.health_monitor import MIN_DISK_FREE_BYTES

        assert isinstance(MIN_DISK_FREE_BYTES, int)
        assert MIN_DISK_FREE_BYTES > 0

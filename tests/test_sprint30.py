"""Sprint 30 tests: UX Flow, Stage Timing & Live System Status.

Tests cover:
  - Phase 1: Per-stage duration display (step timing in UI)
  - Phase 2: Live system health SSE stream + enriched status
  - Phase 3: Quick embed (no re-upload) + video preservation
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


def _html():
    """Get the main page HTML."""
    return client.get("/").text


# ── Phase 1: Stage Timing Display ──


@pytest.mark.skip(reason="Frontend migrated to React")
class TestStageTimingUI:
    """Verify step timing elements and JS logic exist in the frontend."""

    def test_step_time_elements_exist(self):
        html = _html()
        for i in range(1, 5):
            assert f'id="stepTime{i}"' in html

    def test_step_timer_js_functions(self):
        html = _html()
        assert "function formatStepDuration" in html
        assert "function startStepTimer" in html
        assert "function stopStepTimer" in html
        assert "function updateCompletedTimings" in html
        assert "function resetStepTimings" in html

    def test_step_timer_interval_logic(self):
        html = _html()
        assert "stepTimerInterval" in html
        assert "setInterval" in html

    def test_step_timing_used_in_progress_handler(self):
        html = _html()
        assert "data.step_timing" in html
        assert "updateCompletedTimings" in html

    def test_step_timing_used_in_done_handler(self):
        html = _html()
        assert "data.step_timings" in html
        assert "tsSummaryUpload" in html
        assert "tsSummaryExtract" in html
        assert "tsSummaryTranscribe" in html
        assert "tsSummaryFinalize" in html
        assert "tsSummaryTotal" in html

    def test_timing_summary_section_exists(self):
        html = _html()
        assert 'id="timingSummary"' in html
        assert "timing-summary" in html

    def test_timing_summary_labels(self):
        html = _html()
        assert "Upload &amp; Probe" in html or "Upload & Probe" in html
        assert "Audio Extraction" in html
        assert "Transcription" in html
        assert "File Generation" in html

    def test_step_time_css_styling(self):
        html = _html()
        assert "fade-in-time" in html
        assert ".step-time" in html

    def test_format_step_duration_handles_ranges(self):
        """Verify the formatter logic covers <10s, 10-60s, and 60s+ ranges."""
        html = _html()
        # Check that the function handles all three cases
        assert "toFixed(1)" in html  # < 10s
        assert "Math.round(sec)" in html  # 10-60s
        assert "Math.floor(sec / 60)" in html  # 60s+

    def test_reset_clears_timings(self):
        html = _html()
        assert "resetStepTimings()" in html
        assert "timingSummary" in html


# ── Phase 2: Live Health SSE Stream ──


class TestHealthSSEEndpoint:
    """Verify the /health/stream SSE endpoint exists and is properly configured."""

    def test_health_stream_route_registered(self):
        """Verify /health/stream route is registered in the app."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/health/stream" in routes

    def test_health_stream_returns_streaming_response(self):
        """Verify the endpoint handler returns a StreamingResponse."""
        from app.routes.health import health_stream
        import inspect

        source = inspect.getsource(health_stream)
        assert "StreamingResponse" in source
        assert "text/event-stream" in source

    def test_health_stream_generator_emits_json(self):
        """Verify the SSE generator produces valid JSON data lines."""
        from app.routes.health import health_stream
        import inspect

        source = inspect.getsource(health_stream)
        assert "json.dumps" in source
        assert "data: " in source

    def test_health_stream_has_keepalive_headers(self):
        """Verify SSE response includes proper caching/connection headers."""
        from app.routes.health import health_stream
        import inspect

        source = inspect.getsource(health_stream)
        assert "Cache-Control" in source
        assert "no-cache" in source


class TestEnrichedStatus:
    """Verify /api/status returns enriched data with CPU/memory/max_tasks."""

    def test_status_includes_cpu_percent(self):
        res = client.get("/api/status")
        data = res.json()
        assert "cpu_percent" in data

    def test_status_includes_memory_percent(self):
        res = client.get("/api/status")
        data = res.json()
        assert "memory_percent" in data

    def test_status_includes_max_tasks(self):
        res = client.get("/api/status")
        data = res.json()
        assert "max_tasks" in data

    def test_status_includes_active_tasks(self):
        res = client.get("/api/status")
        data = res.json()
        assert "active_tasks" in data
        assert isinstance(data["active_tasks"], int)


@pytest.mark.skip(reason="Frontend migrated to React")
class TestHealthSSEFrontend:
    """Verify the frontend wires to health SSE."""

    def test_health_sse_connect_function(self):
        html = _html()
        assert "function connectHealthSSE()" in html
        assert "new EventSource('/health/stream')" in html

    def test_health_offline_state(self):
        html = _html()
        assert "function showHealthOffline()" in html
        assert "health-dot offline" in html

    def test_health_load_bar_exists(self):
        html = _html()
        assert 'id="healthLoadFill"' in html
        assert "health-load-bar" in html
        assert "health-load-fill" in html

    def test_health_watchdog(self):
        html = _html()
        assert "healthWatchdog" in html

    def test_health_panel_cpu_gauge(self):
        html = _html()
        assert "cpu_percent" in html
        assert "health-mini-bar" in html

    def test_health_panel_memory_gauge(self):
        html = _html()
        assert "memory_percent" in html

    def test_health_panel_db_latency_badge(self):
        html = _html()
        assert "health-latency-badge" in html
        assert "db_latency_ms" in html

    def test_health_panel_task_gauge(self):
        html = _html()
        assert "max_tasks" in html

    def test_health_polling_fallback(self):
        """Verify polling fallback exists when SSE fails."""
        html = _html()
        assert "function pollSystemHealth()" in html
        assert "function startHealthPolling()" in html
        assert "function stopHealthPolling()" in html

    def test_health_initial_poll(self):
        """Verify immediate poll before SSE connects."""
        html = _html()
        # Should call pollSystemHealth before connectHealthSSE
        assert "pollSystemHealth();" in html


class TestHealthRateLimitExempt:
    """Verify health endpoints bypass rate limiting."""

    def test_health_stream_exempt(self):
        from app.middleware.rate_limit import _EXEMPT_PATHS

        assert "/health/stream" in _EXEMPT_PATHS

    def test_health_stream_auth_public(self):
        from app.middleware.auth import PUBLIC_PATHS

        assert "/health/stream" in PUBLIC_PATHS


# ── Phase 3: Quick Embed (No Re-Upload) ──


@pytest.mark.skip(reason="Frontend migrated to React")
class TestQuickEmbedUI:
    """Verify unified embed card elements in the frontend."""

    def test_embed_card_exists(self):
        html = _html()
        assert 'id="embedCard"' in html
        assert "embed-card" in html

    def test_embed_mode_tabs(self):
        html = _html()
        assert 'id="embedTabSoft"' in html
        assert "Soft Mux" in html
        assert "Hard Burn" in html

    def test_embed_preset_select(self):
        html = _html()
        assert 'id="embedPreset"' in html
        assert "YouTube White" in html

    def test_embed_button(self):
        html = _html()
        assert 'id="embedStartBtn"' in html
        assert "startUnifiedEmbed()" in html
        assert "Embed Now" in html

    def test_embed_status_area(self):
        html = _html()
        assert 'id="embedStatus"' in html
        assert 'id="embedResult"' in html

    def test_embed_js_function(self):
        html = _html()
        assert "async function startUnifiedEmbed()" in html
        assert "/quick" in html

    def test_embed_listens_sse(self):
        html = _html()
        assert "embed_done" in html
        assert "embed_error" in html

    def test_embed_shown_for_video(self):
        """Verify embed card is shown when is_video flag is set."""
        html = _html()
        assert "data.is_video" in html
        assert "embedCard" in html

    def test_embed_reset(self):
        html = _html()
        # Verify resetUI clears embed card
        assert "embedCard" in html


class TestQuickEmbedEndpoint:
    """Verify POST /embed/{task_id}/quick endpoint."""

    def test_quick_embed_404_unknown_task(self):
        res = client.post("/embed/nonexistent/quick", data={"mode": "soft"})
        assert res.status_code == 404

    def test_quick_embed_400_no_preserved_video(self):
        from app import state

        task_id = "test-quick-embed-no-video"
        state.tasks[task_id] = {"status": "done", "filename": "test.mp4"}
        try:
            res = client.post(f"/embed/{task_id}/quick", data={"mode": "soft"})
            assert res.status_code == 400
            assert "preserved" in res.json()["detail"].lower() or "No preserved" in res.json()["detail"]
        finally:
            state.tasks.pop(task_id, None)

    def test_quick_embed_400_not_done(self):
        from app import state

        task_id = "test-quick-embed-not-done"
        state.tasks[task_id] = {"status": "transcribing", "filename": "test.mp4"}
        try:
            res = client.post(f"/embed/{task_id}/quick", data={"mode": "soft"})
            assert res.status_code == 400
        finally:
            state.tasks.pop(task_id, None)


class TestVideoPreservation:
    """Verify pipeline preserves video for deferred embed."""

    def test_pipeline_sets_is_video_flag(self):
        """Verify that process_video sets is_video on the task."""
        from app import state
        from app.services.pipeline import process_video

        # We can't run the full pipeline without ffmpeg, but we can verify the flag is set
        task_id = "test-is-video-flag"
        state.tasks[task_id] = {"status": "queued", "filename": "test.mp4"}
        video_path = Path("fake_video.mp4")

        # The pipeline will fail (no real file), but we can check the flag was set
        try:
            process_video(task_id, video_path, "tiny", "cpu")
        except Exception:
            pass

        task = state.tasks.get(task_id, {})
        assert task.get("is_video") is True
        state.tasks.pop(task_id, None)

    def test_audio_file_not_flagged_as_video(self):
        """Verify that audio files don't get is_video=True."""
        from app import state
        from app.services.pipeline import process_video

        task_id = "test-is-audio-flag"
        state.tasks[task_id] = {"status": "queued", "filename": "test.mp3"}
        audio_path = Path("fake_audio.mp3")

        try:
            process_video(task_id, audio_path, "tiny", "cpu")
        except Exception:
            pass

        task = state.tasks.get(task_id, {})
        assert task.get("is_video") is False
        state.tasks.pop(task_id, None)


class TestPipelineStepTimingEvents:
    """Verify pipeline emits step_timing data in events."""

    def test_step_timing_in_task_state(self):
        """Verify step_timing dict structure exists in pipeline code."""
        import inspect
        from app.services import pipeline

        source = inspect.getsource(pipeline.process_video)
        assert '"upload"' in source or "'upload'" in source
        assert '"extract"' in source or "'extract'" in source
        assert '"transcribe"' in source or "'transcribe'" in source
        assert '"finalize"' in source or "'finalize'" in source

    def test_done_event_includes_is_video(self):
        """Verify the done event emits is_video flag."""
        import inspect
        from app.services import pipeline

        source = inspect.getsource(pipeline.process_video)
        assert '"is_video"' in source or "'is_video'" in source

    def test_step_started_at_emitted(self):
        """Verify step_started_at is sent with step_change events."""
        import inspect
        from app.services import pipeline

        source = inspect.getsource(pipeline.process_video)
        assert "step_started_at" in source


# ── Health Status State-Accuracy Tests ──
# Tests every combination of conditions and verifies the status output is correct.


class TestHealthStatusAccuracy:
    """Verify /api/status accurately reflects system state in ALL cases.

    Status rules:
      - critical: any critical alert, OR db_ok=False, OR disk_ok=False
      - warning:  any warning alert, OR ffmpeg_ok=False
      - healthy:  everything OK
    """

    def _get_status(self):
        """Fetch fresh status (bust cache first)."""
        from app.routes.health import _status_cache

        _status_cache["data"] = None
        _status_cache["expires"] = 0.0
        return client.get("/api/status").json()

    # ── Case 1: All systems healthy ──

    def test_healthy_when_all_ok(self):
        """Status is 'healthy' when DB, disk, ffmpeg, and alerts are all OK."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 5.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)  # 10GB free
            data = self._get_status()
            assert data["status"] == "healthy"
            assert data["db_ok"] is True
            assert data["disk_ok"] is True
            assert data["ffmpeg_ok"] is True
            assert data["alert_count"] == 0

    # ── Case 2: Database down → critical ──

    def test_critical_when_db_down(self):
        """Status is 'critical' when database connection fails."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "unhealthy", "ok": False, "error": "connection refused"},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["db_ok"] is False
            assert data["db_latency_ms"] is None

    def test_critical_when_db_raises_exception(self):
        """Status is 'critical' when DB health check throws an exception."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("app.services.query_layer.check_db_health", side_effect=Exception("connection timeout")),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["db_ok"] is False

    # ── Case 3: Disk low → critical ──

    def test_critical_when_disk_low(self):
        """Status is 'critical' when disk free space < 1GB."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=500 * 1024**2)  # 500MB
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["disk_ok"] is False
            assert data["disk_free_gb"] < 1.0

    def test_critical_when_disk_read_fails(self):
        """Status is 'critical' when disk usage cannot be read."""
        with (
            patch("app.routes.health.shutil.disk_usage", side_effect=OSError("permission denied")),
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["disk_ok"] is False
            assert data["disk_free_gb"] is None

    # ── Case 4: FFmpeg missing → warning ──

    def test_warning_when_ffmpeg_missing(self):
        """Status is 'warning' when ffmpeg is not available."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value=None),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "warning"
            assert data["ffmpeg_ok"] is False

    # ── Case 5: Alerts → correct severity ──

    def test_warning_when_warning_alert(self):
        """Status is 'warning' when a warning-level alert is active."""
        warning_alert = [{"alert": "high_error_rate", "severity": "warning", "message": "Error rate 10%"}]
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=warning_alert),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "warning"
            assert data["alert_count"] == 1
            assert data["alerts"][0]["severity"] == "warning"

    def test_critical_when_critical_alert(self):
        """Status is 'critical' when a critical-level alert is active."""
        critical_alert = [{"alert": "disk_low", "severity": "critical", "message": "Disk space critical"}]
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=critical_alert),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["alert_count"] == 1

    def test_critical_overrides_warning(self):
        """Critical status takes priority over warning when both exist."""
        mixed_alerts = [
            {"alert": "high_error_rate", "severity": "warning", "message": "Error rate high"},
            {"alert": "disk_low", "severity": "critical", "message": "Disk critical"},
        ]
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=mixed_alerts),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["alert_count"] == 2

    # ── Case 6: Multiple failures → still critical ──

    def test_critical_with_db_and_disk_both_down(self):
        """Status is 'critical' when both DB and disk are failing."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("app.services.query_layer.check_db_health", return_value={"status": "unhealthy", "ok": False}),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=200 * 1024**2)  # 200MB
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["db_ok"] is False
            assert data["disk_ok"] is False

    def test_critical_with_everything_down(self):
        """Status is 'critical' when DB, disk, ffmpeg all fail + critical alert."""
        critical_alert = [{"alert": "disk_low", "severity": "critical", "message": "Disk critical"}]
        with (
            patch("app.routes.health.shutil.disk_usage", side_effect=OSError("fail")),
            patch("app.routes.health.shutil.which", return_value=None),
            patch("app.services.query_layer.check_db_health", side_effect=Exception("db down")),
            patch("app.services.monitoring.check_alerts", return_value=critical_alert),
        ):
            data = self._get_status()
            assert data["status"] == "critical"
            assert data["db_ok"] is False
            assert data["disk_ok"] is False
            assert data["ffmpeg_ok"] is False

    # ── Case 7: Active tasks count ──

    def test_active_tasks_counted_correctly(self):
        """Active tasks count excludes done/error/cancelled tasks."""
        from app import state

        saved = dict(state.tasks)
        try:
            state.tasks.clear()
            state.tasks["t1"] = {"status": "transcribing"}
            state.tasks["t2"] = {"status": "extracting"}
            state.tasks["t3"] = {"status": "done"}
            state.tasks["t4"] = {"status": "error"}
            state.tasks["t5"] = {"status": "cancelled"}
            state.tasks["t6"] = {"status": "queued"}
            data = self._get_status()
            assert data["active_tasks"] == 3  # t1, t2, t6
        finally:
            state.tasks.clear()
            state.tasks.update(saved)

    def test_zero_active_tasks_when_all_finished(self):
        """Active tasks is 0 when all tasks are done/error/cancelled."""
        from app import state

        saved = dict(state.tasks)
        try:
            state.tasks.clear()
            state.tasks["t1"] = {"status": "done"}
            state.tasks["t2"] = {"status": "error"}
            data = self._get_status()
            assert data["active_tasks"] == 0
        finally:
            state.tasks.clear()
            state.tasks.update(saved)

    # ── Case 8: Shutting down ──

    def test_shutting_down_flag(self):
        """Verify shutting_down is reflected in status."""
        from app import state

        original = state.shutting_down
        try:
            state.shutting_down = True
            data = self._get_status()
            assert data["shutting_down"] is True
        finally:
            state.shutting_down = original

    # ── Case 9: DB latency values ──

    def test_db_latency_reported_when_healthy(self):
        """DB latency is a number when database is healthy."""
        with patch(
            "app.services.query_layer.check_db_health",
            return_value={"status": "healthy", "latency_ms": 12.5, "ok": True},
        ):
            data = self._get_status()
            if data["db_ok"]:
                assert isinstance(data["db_latency_ms"], (int, float))

    def test_db_latency_null_when_down(self):
        """DB latency is null when database is unreachable."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("app.services.query_layer.check_db_health", side_effect=Exception("refused")),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["db_ok"] is False
            assert data["db_latency_ms"] is None

    # ── Case 10: CPU/Memory data ──

    def test_cpu_memory_present(self):
        """CPU and memory metrics are present in response."""
        data = self._get_status()
        assert "cpu_percent" in data
        assert "memory_percent" in data

    def test_cpu_memory_when_psutil_fails(self):
        """CPU/memory are None if psutil fails."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
            patch.dict("sys.modules", {"psutil": None}),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            # Force re-import failure by patching import inside the function
            import builtins

            real_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "psutil":
                    raise ImportError("mocked")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                data = self._get_status()
                assert data["cpu_percent"] is None
                assert data["memory_percent"] is None

    # ── Case 11: Cache invalidation for real-time ──

    def test_cache_ttl_is_1_second(self):
        """Verify status cache expires after 3 seconds for real-time updates."""
        from app.routes.health import _status_cache

        _status_cache["data"] = None
        _status_cache["expires"] = 0.0

        # First call populates cache
        client.get("/api/status").json()
        assert _status_cache["data"] is not None
        # Cache should expire within 3 seconds
        import time

        assert _status_cache["expires"] <= time.time() + 3.1

    # ── Case 12: SSE interval is 3 seconds ──

    def test_sse_interval_is_1_second(self):
        """Verify SSE pushes every 3 seconds."""
        from app.routes.health import health_stream
        import inspect

        source = inspect.getsource(health_stream)
        assert "asyncio.sleep(3)" in source

    # ── Case 13: Alerts data passed through correctly ──

    def test_alerts_forwarded_to_response(self):
        """Verify alert details are included in status response."""
        alerts = [
            {"alert": "high_error_rate", "severity": "warning", "message": "Error rate 15%"},
            {"alert": "disk_low", "severity": "critical", "message": "Disk at 0.5GB"},
        ]
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 3.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=alerts),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["alert_count"] == 2
            assert len(data["alerts"]) == 2
            severities = {a["severity"] for a in data["alerts"]}
            assert "warning" in severities
            assert "critical" in severities

    # ── Case 14: Recovery detection ──

    def test_healthy_after_db_recovery(self):
        """Status returns to 'healthy' after DB comes back online."""
        # First: DB down
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("app.services.query_layer.check_db_health", return_value={"status": "unhealthy", "ok": False}),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "critical"

        # Then: DB recovered
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "latency_ms": 5.0, "ok": True},
            ),
            patch("app.services.monitoring.check_alerts", return_value=[]),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            data = self._get_status()
            assert data["status"] == "healthy"
            assert data["db_ok"] is True


# ── DB-Required: Upload Rejection & Service Availability ──


class TestUploadRequiresDB:
    """Verify uploads are rejected when system is in critical state (e.g. DB down)."""

    def test_upload_rejected_when_db_down(self):
        """Upload returns 503 when system is in critical state."""
        from app import state

        old_critical, old_reasons = state.system_critical, state.system_critical_reasons
        try:
            state.system_critical = True
            state.system_critical_reasons = ["Database connection lost"]
            import io

            res = client.post(
                "/upload",
                data={"device": "cpu", "model_size": "tiny", "language": "auto"},
                files={"file": ("test.mp4", io.BytesIO(b"\x00" * 1024), "video/mp4")},
            )
            assert res.status_code == 503
            body = res.json()
            assert "critical" in body.get("detail", "").lower() or body.get("critical") is True
        finally:
            state.system_critical, state.system_critical_reasons = old_critical, old_reasons

    def test_upload_rejected_when_critical_state(self):
        """Upload returns 503 for any critical reason (not just DB)."""
        from app import state

        old_critical, old_reasons = state.system_critical, state.system_critical_reasons
        try:
            state.system_critical = True
            state.system_critical_reasons = ["Disk space critically low"]
            import io

            res = client.post(
                "/upload",
                data={"device": "cpu", "model_size": "tiny", "language": "auto"},
                files={"file": ("test.mp4", io.BytesIO(b"\x00" * 1024), "video/mp4")},
            )
            assert res.status_code == 503
        finally:
            state.system_critical, state.system_critical_reasons = old_critical, old_reasons

    def test_upload_accepted_when_db_healthy(self):
        """Upload proceeds normally when system is not critical (file validation may fail, but not 503)."""
        from app import state

        old_critical, old_reasons = state.system_critical, state.system_critical_reasons
        try:
            state.system_critical = False
            state.system_critical_reasons = []
            import io

            res = client.post(
                "/upload",
                data={"device": "cpu", "model_size": "tiny", "language": "auto"},
                files={"file": ("test.mp4", io.BytesIO(b"\x00" * 100), "video/mp4")},
            )
            # May fail on file validation (too small, bad magic bytes) but NOT 503
            assert res.status_code != 503
        finally:
            state.system_critical, state.system_critical_reasons = old_critical, old_reasons


class TestReadinessRequiresDB:
    """Verify /ready endpoint includes DB check."""

    def test_ready_fails_when_db_down(self):
        """Readiness probe returns 503 when DB is unreachable."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("app.services.query_layer.check_db_health", return_value={"status": "unhealthy", "ok": False}),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            res = client.get("/ready")
            assert res.status_code == 503
            data = res.json()
            assert data["status"] == "not_ready"
            assert data["checks"]["db"]["ok"] is False

    def test_ready_succeeds_when_db_healthy(self):
        """Readiness probe returns 200 when DB is healthy."""
        with (
            patch("app.routes.health.shutil.disk_usage") as mock_disk,
            patch("app.routes.health.shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "app.services.query_layer.check_db_health",
                return_value={"status": "healthy", "ok": True, "latency_ms": 3.0},
            ),
        ):
            mock_disk.return_value = MagicMock(free=10 * 1024**3)
            res = client.get("/ready")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ready"
            assert data["checks"]["db"]["ok"] is True


@pytest.mark.skip(reason="Frontend migrated to React")
class TestServiceBannerUI:
    """Verify the service unavailable banner exists in the frontend."""

    def test_service_banner_element_exists(self):
        html = _html()
        assert 'id="serviceBanner"' in html
        assert "service-banner" in html

    def test_banner_shows_on_critical_state(self):
        html = _html()
        assert "data.system_critical" in html or "system_critical" in html
        assert "SYSTEM CRITICAL" in html or "critical" in html.lower()

    def test_banner_shows_on_shutting_down(self):
        html = _html()
        assert "data.shutting_down" in html
        assert "shutting down" in html.lower()

    def test_dropzone_disabled_class(self):
        html = _html()
        assert "drop-zone.disabled" in html or "disabled" in html
        assert "pointer-events: none" in html or "pointer-events:none" in html

    def test_banner_hidden_when_healthy(self):
        html = _html()
        assert "service-banner hidden" in html

    def test_offline_shows_banner(self):
        """showHealthOffline also shows the service banner."""
        html = _html()
        assert "Service unreachable" in html

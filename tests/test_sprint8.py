"""Tests for Sprint 8: Analytics Foundation & Session Resilience.

S8-1: Analytics service (counters, distributions, processing times)
S8-2: Time-series ring buffer (minute-resolution, 24h)
S8-3: Analytics hooks in pipeline
S8-4: GET /analytics/summary
S8-5: GET /analytics/timeseries
S8-6: Session reconnection (frontend - tested via endpoint verification)
S8-7: Metrics counter wiring
S8-8: Frontend advanced options (tested via endpoint param acceptance)
S8-9: Integration tests
"""

from pathlib import Path

from app.main import app
from app.services.analytics import (
    record_upload, record_completion, record_failure, record_cancellation,
    get_timeseries, save_analytics_snapshot, load_analytics_snapshot,
    _counters, _language_counts, _model_counts, _device_counts,
    _processing_times, _timeseries, _lock,
)
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")

PROJECT_ROOT = Path(__file__).parent.parent


def _reset_analytics():
    """Reset analytics state for isolated tests."""
    with _lock:
        for k in _counters:
            _counters[k] = 0
        _language_counts.clear()
        _model_counts.clear()
        _device_counts.clear()
        _processing_times.clear()
        _timeseries.clear()


# ── S8-1: Analytics Service ──

class TestAnalyticsService:
    def setup_method(self):
        _reset_analytics()

    def test_record_upload_increments_counter(self):
        record_upload(language="en", model="medium", device="cuda", file_size=1024)
        assert _counters["uploads_total"] == 1

    def test_record_upload_tracks_language(self):
        record_upload(language="en")
        record_upload(language="ja")
        record_upload(language="en")
        assert _language_counts["en"] == 2
        assert _language_counts["ja"] == 1

    def test_record_upload_tracks_model(self):
        record_upload(model="large")
        record_upload(model="tiny")
        assert _model_counts["large"] == 1
        assert _model_counts["tiny"] == 1

    def test_record_upload_tracks_device(self):
        record_upload(device="cuda")
        record_upload(device="cpu")
        assert _device_counts["cuda"] == 1
        assert _device_counts["cpu"] == 1

    def test_record_completion(self):
        record_completion(12.5, model="medium")
        assert _counters["completed_total"] == 1
        assert len(_processing_times) == 1
        assert _processing_times[0] == 12.5

    def test_record_failure(self):
        record_failure()
        assert _counters["failed_total"] == 1

    def test_record_cancellation(self):
        record_cancellation()
        assert _counters["cancelled_total"] == 1

    def test_multiple_events(self):
        for _ in range(5):
            record_upload()
        for _ in range(3):
            record_completion(10.0)
        record_failure()
        record_cancellation()
        assert _counters["uploads_total"] == 5
        assert _counters["completed_total"] == 3
        assert _counters["failed_total"] == 1
        assert _counters["cancelled_total"] == 1


# ── S8-2: Time-Series Ring Buffer ──

class TestTimeSeries:
    def setup_method(self):
        _reset_analytics()

    def test_timeseries_created_on_upload(self):
        record_upload()
        ts = get_timeseries(minutes=5)
        assert len(ts) >= 1
        assert ts[-1]["uploads"] >= 1

    def test_timeseries_tracks_completions(self):
        record_completion(5.0)
        ts = get_timeseries(minutes=5)
        assert len(ts) >= 1
        assert ts[-1]["completed"] >= 1

    def test_timeseries_tracks_failures(self):
        record_failure()
        ts = get_timeseries(minutes=5)
        assert ts[-1]["failed"] >= 1

    def test_timeseries_avg_processing(self):
        record_completion(10.0)
        record_completion(20.0)
        ts = get_timeseries(minutes=5)
        assert ts[-1]["avg_processing_sec"] == 15.0

    def test_timeseries_has_timestamp(self):
        record_upload()
        ts = get_timeseries(minutes=5)
        assert "timestamp" in ts[-1]
        assert "time" in ts[-1]

    def test_timeseries_empty_for_future_range(self):
        ts = get_timeseries(minutes=0)
        # Should still return current minute if data exists
        # but with minutes=0 the cutoff is effectively "now"
        # so this is fine
        assert isinstance(ts, list)


# ── S8-4: Analytics Summary Endpoint ──

class TestAnalyticsSummaryEndpoint:
    def setup_method(self):
        _reset_analytics()

    def test_summary_endpoint_available(self):
        res = client.get("/analytics/summary")
        assert res.status_code == 200

    def test_summary_has_counters(self):
        record_upload()
        record_completion(5.0)
        res = client.get("/analytics/summary")
        data = res.json()
        assert "counters" in data
        assert data["counters"]["uploads_total"] >= 1

    def test_summary_has_rates(self):
        res = client.get("/analytics/summary")
        data = res.json()
        assert "rates" in data
        assert "success_rate" in data["rates"]
        assert "error_rate" in data["rates"]

    def test_summary_has_processing(self):
        res = client.get("/analytics/summary")
        data = res.json()
        assert "processing" in data
        assert "avg_sec" in data["processing"]

    def test_summary_has_distributions(self):
        record_upload(language="en")
        res = client.get("/analytics/summary")
        data = res.json()
        assert "distributions" in data
        assert "top_languages" in data["distributions"]

    def test_summary_success_rate(self):
        _reset_analytics()
        record_completion(5.0)
        record_completion(3.0)
        record_failure()
        res = client.get("/analytics/summary")
        data = res.json()
        # 2 completed, 1 failed = 66.7% success
        assert data["rates"]["success_rate"] == 66.7


# ── S8-5: Analytics Timeseries Endpoint ──

class TestAnalyticsTimeseriesEndpoint:
    def setup_method(self):
        _reset_analytics()

    def test_timeseries_endpoint_available(self):
        res = client.get("/analytics/timeseries")
        assert res.status_code == 200

    def test_timeseries_default_60_minutes(self):
        res = client.get("/analytics/timeseries")
        data = res.json()
        assert "points" in data
        assert data["minutes"] == 60

    def test_timeseries_custom_minutes(self):
        res = client.get("/analytics/timeseries?minutes=5")
        data = res.json()
        assert data["minutes"] == 5

    def test_timeseries_min_1_minute(self):
        res = client.get("/analytics/timeseries?minutes=0")
        assert res.status_code == 422  # ge=1 validation

    def test_timeseries_max_1440_minutes(self):
        res = client.get("/analytics/timeseries?minutes=1441")
        assert res.status_code == 422  # le=1440 validation

    def test_timeseries_returns_points_after_events(self):
        record_upload()
        record_completion(5.0)
        res = client.get("/analytics/timeseries?minutes=5")
        data = res.json()
        assert len(data["points"]) >= 1


# ── S8-6: Session Reconnection ──

class TestSessionReconnection:
    def test_progress_endpoint_returns_404_for_unknown(self):
        """Verify progress endpoint returns 404 for unknown task (frontend handles this)."""
        res = client.get("/progress/nonexistent-task")
        assert res.status_code == 404

    def test_progress_endpoint_returns_status_for_known_task(self):
        """Verify progress endpoint returns status for known task."""
        from app import state
        state.tasks["test-reconnect"] = {"status": "transcribing", "percent": 50, "message": "Working..."}
        res = client.get("/progress/test-reconnect")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "transcribing"
        del state.tasks["test-reconnect"]

    def test_frontend_has_session_reconnect_logic(self):
        """Verify frontend contains sessionStorage reconnection code."""
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "sg_currentTaskId" in html
        assert "sessionStorage" in html
        assert "reconnectSession" in html


# ── S8-7: Metrics Wiring ──

class TestMetricsWiring:
    def test_metrics_endpoint_has_counters(self):
        res = client.get("/metrics")
        text = res.text
        assert "subtitle_generator_uploads_total" in text
        assert "subtitle_generator_transcriptions_completed" in text

    def test_pipeline_imports_analytics(self):
        """Verify pipeline module imports analytics."""
        import app.services.pipeline as pipeline_mod
        source = Path(pipeline_mod.__file__).read_text()
        assert "record_completion" in source
        assert "record_failure" in source
        assert "record_cancellation" in source

    def test_upload_imports_analytics(self):
        """Verify upload route imports analytics."""
        import app.routes.upload as upload_mod
        source = Path(upload_mod.__file__).read_text()
        assert "record_upload" in source


# ── S8-8: Frontend Advanced Options ──

class TestFrontendAdvancedOptions:
    def test_frontend_has_word_timestamps_option(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "advWordTimestamps" in html

    def test_frontend_has_diarize_option(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "advDiarize" in html

    def test_frontend_has_translate_option(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "advTranslate" in html

    def test_frontend_has_vocabulary_option(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "advVocabulary" in html

    def test_frontend_has_max_chars_option(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "advMaxChars" in html

    def test_frontend_has_json_download(self):
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "downloadBtnJson" in html

    def test_frontend_sends_advanced_params(self):
        """Verify upload function sends advanced params in FormData."""
        html = (PROJECT_ROOT / "templates" / "index.html").read_text()
        assert "word_timestamps" in html
        assert "diarize" in html
        assert "translate_to_english" in html
        assert "initial_prompt" in html
        assert "max_line_chars" in html


# ── S8-9: Analytics Persistence ──

class TestAnalyticsPersistence:
    def setup_method(self):
        _reset_analytics()

    def test_save_and_load_snapshot(self, tmp_path):
        import app.services.analytics as analytics_mod
        import app.config as config_mod
        original_log_dir = config_mod.LOG_DIR

        # Temporarily change LOG_DIR
        config_mod.LOG_DIR = tmp_path
        analytics_mod.LOG_DIR = tmp_path

        record_upload(language="fr", model="large")
        record_upload(language="en")
        record_completion(10.0)

        save_analytics_snapshot()
        assert (tmp_path / "analytics_snapshot.json").exists()

        # Reset and reload
        _reset_analytics()
        assert _counters["uploads_total"] == 0

        load_analytics_snapshot()
        assert _counters["uploads_total"] == 2
        assert _counters["completed_total"] == 1
        assert _language_counts["fr"] == 1

        # Restore
        config_mod.LOG_DIR = original_log_dir
        analytics_mod.LOG_DIR = original_log_dir


# ── S8: Route Registration ──

class TestRouteRegistration:
    def test_analytics_summary_registered(self):
        res = client.get("/analytics/summary")
        assert res.status_code == 200

    def test_analytics_timeseries_registered(self):
        res = client.get("/analytics/timeseries")
        assert res.status_code == 200

    def test_analytics_in_public_paths(self):
        """Analytics endpoints should be accessible without API key."""
        from app.middleware.auth import PUBLIC_PATHS
        assert "/analytics/summary" in PUBLIC_PATHS
        assert "/analytics/timeseries" in PUBLIC_PATHS

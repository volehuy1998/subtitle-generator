"""Tests for Sprint 9: Real-Time Analytics Dashboard with Charts.

S9-1: /analytics page with Chart.js
S9-2: Processing volume chart (time-series data)
S9-3: Success/error rate chart (pie data)
S9-4: Language distribution chart
S9-5: Average processing time by model
S9-6: File size distribution
S9-7: Real-time counters (KPIs)
S9-8: Auto-refresh with configurable interval
S9-9: Integration tests
"""

from pathlib import Path

from app.main import app
from app.services.analytics import (
    record_upload, record_completion, record_failure, record_cancellation,
    get_summary, get_timeseries, _counters, _language_counts, _timeseries, _lock,
)
from fastapi.testclient import TestClient

client = TestClient(app)

PROJECT_ROOT = Path(__file__).parent.parent


def _reset_analytics():
    """Reset analytics state for isolated tests."""
    from app.services.analytics import _model_counts, _device_counts, _processing_times
    with _lock:
        for k in _counters:
            _counters[k] = 0
        _language_counts.clear()
        _model_counts.clear()
        _device_counts.clear()
        _processing_times.clear()
        _timeseries.clear()


# ── S9-1: Analytics Page ──

class TestAnalyticsPage:
    def test_analytics_page_returns_200(self):
        res = client.get("/analytics")
        assert res.status_code == 200

    def test_analytics_page_is_html(self):
        res = client.get("/analytics")
        assert "text/html" in res.headers.get("content-type", "")

    def test_analytics_page_has_chart_js(self):
        res = client.get("/analytics")
        assert "chart.js" in res.text.lower() or "Chart" in res.text

    def test_analytics_page_has_title(self):
        res = client.get("/analytics")
        assert "Analytics Dashboard" in res.text

    def test_analytics_page_has_home_link(self):
        res = client.get("/analytics")
        assert 'href="/"' in res.text

    def test_analytics_page_has_dashboard_link(self):
        res = client.get("/analytics")
        assert 'href="/dashboard"' in res.text


# ── S9-2: Processing Volume Chart ──

class TestVolumeChart:
    def test_page_has_volume_chart(self):
        res = client.get("/analytics")
        assert "volumeChart" in res.text

    def test_timeseries_provides_upload_data(self):
        _reset_analytics()
        record_upload()
        record_upload()
        ts = get_timeseries(5)
        assert len(ts) >= 1
        assert ts[-1]["uploads"] >= 2

    def test_timeseries_provides_completed_data(self):
        _reset_analytics()
        record_completion(5.0)
        ts = get_timeseries(5)
        assert ts[-1]["completed"] >= 1

    def test_timeseries_provides_failed_data(self):
        _reset_analytics()
        record_failure()
        ts = get_timeseries(5)
        assert ts[-1]["failed"] >= 1


# ── S9-3: Success/Error Rate Chart ──

class TestRateChart:
    def test_page_has_rate_chart(self):
        res = client.get("/analytics")
        assert "rateChart" in res.text

    def test_summary_provides_rate_data(self):
        _reset_analytics()
        record_completion(5.0)
        record_completion(3.0)
        record_failure()
        summary = get_summary()
        assert summary["rates"]["success_rate"] == 66.7
        assert summary["rates"]["error_rate"] == 33.3


# ── S9-4: Language Distribution Chart ──

class TestLanguageChart:
    def test_page_has_language_chart(self):
        res = client.get("/analytics")
        assert "langChart" in res.text

    def test_summary_provides_language_distribution(self):
        _reset_analytics()
        record_upload(language="en")
        record_upload(language="en")
        record_upload(language="ja")
        record_upload(language="zh")
        summary = get_summary()
        langs = summary["distributions"]["top_languages"]
        assert langs["en"] == 2
        assert langs["ja"] == 1

    def test_top_languages_limited_to_10(self):
        _reset_analytics()
        for i in range(15):
            record_upload(language=f"lang{i}")
        summary = get_summary()
        assert len(summary["distributions"]["top_languages"]) <= 10


# ── S9-5: Processing Time by Model ──

class TestModelChart:
    def test_page_has_model_chart(self):
        res = client.get("/analytics")
        assert "modelChart" in res.text

    def test_summary_provides_model_averages(self):
        _reset_analytics()
        record_completion(10.0, model="tiny")
        record_completion(20.0, model="tiny")
        record_completion(30.0, model="large")
        summary = get_summary()
        by_model = summary["processing"]["by_model"]
        assert by_model["tiny"] == 15.0
        assert by_model["large"] == 30.0


# ── S9-6: Device Distribution ──

class TestDeviceChart:
    def test_page_has_device_chart(self):
        res = client.get("/analytics")
        assert "deviceChart" in res.text

    def test_summary_provides_device_distribution(self):
        _reset_analytics()
        record_upload(device="cuda")
        record_upload(device="cuda")
        record_upload(device="cpu")
        summary = get_summary()
        devices = summary["distributions"]["devices"]
        assert devices["cuda"] == 2
        assert devices["cpu"] == 1


# ── S9-7: Real-Time KPI Counters ──

class TestKPICounters:
    def test_page_has_kpi_section(self):
        res = client.get("/analytics")
        assert "kpis" in res.text

    def test_summary_has_uploads_per_hour(self):
        summary = get_summary()
        assert "uploads_per_hour" in summary["rates"]

    def test_summary_has_completions_per_hour(self):
        summary = get_summary()
        assert "completions_per_hour" in summary["rates"]

    def test_summary_has_p95_processing(self):
        summary = get_summary()
        assert "p95_sec" in summary["processing"]

    def test_summary_has_uptime(self):
        summary = get_summary()
        assert "uptime_sec" in summary
        assert summary["uptime_sec"] > 0


# ── S9-8: Auto-Refresh ──

class TestAutoRefresh:
    def test_page_has_refresh_selector(self):
        res = client.get("/analytics")
        assert "refreshInterval" in res.text

    def test_page_has_refresh_options(self):
        res = client.get("/analytics")
        assert "5s refresh" in res.text
        assert "10s refresh" in res.text
        assert "30s refresh" in res.text
        assert "60s refresh" in res.text

    def test_page_has_time_range_buttons(self):
        res = client.get("/analytics")
        assert "1 Hour" in res.text
        assert "6 Hours" in res.text
        assert "12 Hours" in res.text
        assert "24 Hours" in res.text

    def test_page_auto_fetches_on_load(self):
        """Verify the page calls refresh() on load."""
        res = client.get("/analytics")
        assert "refresh();" in res.text


# ── S9-9: Route Registration ──

class TestRouteRegistration:
    def test_analytics_page_registered(self):
        res = client.get("/analytics")
        assert res.status_code == 200

    def test_analytics_page_in_public_paths(self):
        from app.middleware.auth import PUBLIC_PATHS
        assert "/analytics" in PUBLIC_PATHS

    def test_analytics_api_endpoints_still_work(self):
        assert client.get("/analytics/summary").status_code == 200
        assert client.get("/analytics/timeseries").status_code == 200

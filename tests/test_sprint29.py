"""Sprint 29 tests: Monitoring & Observability.

Tests cover:
  - Business metrics (uploads, completions, success rate)
  - Alert system (thresholds, triggers, check)
  - Performance profiling (timing, categories)
  - Health dashboard (aggregated view)
  - Monitoring endpoints
  - Prometheus metrics format
"""

import time

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ── Business Metrics Tests ──

class TestBusinessMetrics:
    """Test business metrics tracking."""

    def test_module_imports(self):
        from app.services import monitoring
        assert hasattr(monitoring, "record_upload")
        assert hasattr(monitoring, "record_completion")
        assert hasattr(monitoring, "record_failure")
        assert hasattr(monitoring, "record_embed")
        assert hasattr(monitoring, "get_business_metrics")

    def test_record_upload(self):
        from app.services.monitoring import record_upload, get_business_metrics
        record_upload()
        metrics = get_business_metrics()
        assert metrics["uploads_per_hour"] >= 1

    def test_record_completion(self):
        from app.services.monitoring import record_completion, get_business_metrics
        record_completion(processing_time=5.0)
        metrics = get_business_metrics()
        assert metrics["completions_per_hour"] >= 1

    def test_record_failure(self):
        from app.services.monitoring import record_failure, get_business_metrics
        record_failure()
        metrics = get_business_metrics()
        assert metrics["failures_per_hour"] >= 1

    def test_success_rate(self):
        from app.services.monitoring import get_business_metrics
        metrics = get_business_metrics()
        assert "success_rate_pct" in metrics
        assert 0 <= metrics["success_rate_pct"] <= 100

    def test_processing_time_stats(self):
        from app.services.monitoring import record_completion, get_business_metrics
        record_completion(processing_time=10.0)
        record_completion(processing_time=20.0)
        metrics = get_business_metrics()
        assert metrics["avg_processing_sec"] > 0
        assert metrics["p95_processing_sec"] > 0

    def test_embed_metrics(self):
        from app.services.monitoring import record_embed, get_business_metrics
        record_embed("soft")
        record_embed("hard")
        metrics = get_business_metrics()
        assert metrics["embed_total"] >= 2
        assert metrics["embed_soft"] >= 1
        assert metrics["embed_hard"] >= 1

    def test_metrics_structure(self):
        from app.services.monitoring import get_business_metrics
        metrics = get_business_metrics()
        expected_keys = {"uploads_per_hour", "completions_per_hour", "failures_per_hour",
                         "success_rate_pct", "avg_processing_sec", "p95_processing_sec",
                         "embed_total", "embed_soft", "embed_hard"}
        assert expected_keys <= set(metrics.keys())


# ── Alert System Tests ──

class TestAlertSystem:
    """Test alerting rules and triggers."""

    def test_get_thresholds(self):
        from app.services.monitoring import get_alert_thresholds
        thresholds = get_alert_thresholds()
        assert "error_rate_pct" in thresholds
        assert "queue_depth_max" in thresholds
        assert "disk_free_min_gb" in thresholds
        assert "latency_max_sec" in thresholds
        assert "memory_pct_max" in thresholds

    def test_set_threshold(self):
        from app.services.monitoring import set_alert_threshold, get_alert_thresholds
        original = get_alert_thresholds()["error_rate_pct"]
        set_alert_threshold("error_rate_pct", 10.0)
        assert get_alert_thresholds()["error_rate_pct"] == 10.0
        set_alert_threshold("error_rate_pct", original)  # Restore

    def test_check_alerts_returns_list(self):
        from app.services.monitoring import check_alerts
        alerts = check_alerts()
        assert isinstance(alerts, list)

    def test_alert_structure(self):
        from app.services.monitoring import check_alerts
        alerts = check_alerts()
        for alert in alerts:
            assert "alert" in alert
            assert "severity" in alert
            assert "message" in alert

    def test_disk_alert_check(self):
        from app.services.monitoring import set_alert_threshold, check_alerts, get_alert_thresholds
        original = get_alert_thresholds()["disk_free_min_gb"]
        # Set impossibly high threshold to trigger alert
        set_alert_threshold("disk_free_min_gb", 999999.0)
        alerts = check_alerts()
        disk_alerts = [a for a in alerts if a["alert"] == "disk_low"]
        assert len(disk_alerts) >= 1
        set_alert_threshold("disk_free_min_gb", original)


# ── Performance Profiling Tests ──

class TestPerformanceProfiling:
    """Test per-request timing breakdown."""

    def test_start_timer(self):
        from app.services.monitoring import start_timer
        t = start_timer()
        assert isinstance(t, float)
        assert t > 0

    def test_record_timing(self):
        from app.services.monitoring import start_timer, record_timing, get_performance_profile
        t = start_timer()
        time.sleep(0.01)
        record_timing("test_category", t, task_id="test-123")
        profile = get_performance_profile()
        assert "test_category" in profile
        assert profile["test_category"]["count"] >= 1
        assert profile["test_category"]["avg_sec"] > 0

    def test_profile_structure(self):
        from app.services.monitoring import start_timer, record_timing, get_performance_profile
        t = start_timer()
        record_timing("probe", t)
        profile = get_performance_profile()
        if "probe" in profile:
            p = profile["probe"]
            assert "count" in p
            assert "avg_sec" in p
            assert "min_sec" in p
            assert "max_sec" in p
            assert "p95_sec" in p

    def test_multiple_categories(self):
        from app.services.monitoring import start_timer, record_timing, get_performance_profile
        for cat in ["upload", "transcribe", "embed"]:
            t = start_timer()
            record_timing(cat, t)
        profile = get_performance_profile()
        assert "upload" in profile
        assert "transcribe" in profile
        assert "embed" in profile


# ── Health Dashboard Tests ──

class TestHealthDashboard:
    """Test comprehensive health dashboard."""

    def test_dashboard_function(self):
        from app.services.monitoring import get_health_dashboard
        dashboard = get_health_dashboard()
        assert "timestamp" in dashboard
        assert "status" in dashboard
        assert "business_metrics" in dashboard
        assert "alerts" in dashboard
        assert "performance" in dashboard
        assert "thresholds" in dashboard

    def test_dashboard_status(self):
        from app.services.monitoring import get_health_dashboard
        dashboard = get_health_dashboard()
        assert dashboard["status"] in ("healthy", "degraded")


# ── Monitoring Endpoint Tests ──

class TestMonitoringEndpoints:
    """Test monitoring API endpoints."""

    def test_business_metrics_endpoint(self):
        res = client.get("/monitoring/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "uploads_per_hour" in data

    def test_alerts_endpoint(self):
        res = client.get("/monitoring/alerts")
        assert res.status_code == 200
        data = res.json()
        assert "alerts" in data
        assert "count" in data
        assert "status" in data

    def test_thresholds_endpoint(self):
        res = client.get("/monitoring/thresholds")
        assert res.status_code == 200
        data = res.json()
        assert "error_rate_pct" in data

    def test_performance_endpoint(self):
        res = client.get("/monitoring/performance")
        assert res.status_code == 200
        assert isinstance(res.json(), dict)

    def test_dashboard_endpoint(self):
        res = client.get("/monitoring/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "business_metrics" in data
        assert "alerts" in data

    def test_update_threshold_endpoint(self):
        res = client.put("/monitoring/thresholds/error_rate_pct?value=15.0")
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_update_unknown_threshold(self):
        res = client.put("/monitoring/thresholds/nonexistent?value=1.0")
        assert res.status_code == 404


# ── Prometheus Metrics Tests ──

class TestPrometheusMetrics:
    """Test Prometheus-format metrics endpoint."""

    def test_metrics_endpoint(self):
        res = client.get("/metrics")
        assert res.status_code == 200

    def test_metrics_format(self):
        res = client.get("/metrics")
        text = res.text
        assert "subtitle_generator_uptime_seconds" in text
        assert "# TYPE" in text
        assert "# HELP" in text

    def test_metrics_has_task_counts(self):
        res = client.get("/metrics")
        assert "subtitle_generator_active_tasks" in res.text

    def test_metrics_has_file_counts(self):
        res = client.get("/metrics")
        assert "subtitle_generator_files_count" in res.text

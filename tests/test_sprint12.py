"""Tests for Sprint 12: Advanced Analytics & User Tracking.

S12-1: Request tracking (IP, user-agent categorization)
S12-2: User traffic stats (unique users, agent distribution)
S12-3: Error categorization
S12-4: Pipeline performance tracking
S12-5: Analytics export (CSV, JSON)
S12-6: User stats endpoint
S12-7: Integration tests
"""

from pathlib import Path

from app.main import app
from app.services.analytics import (
    record_request,
    record_error_category,
    get_user_stats,
    export_analytics_csv,
    _client_ips,
    _user_agents,
    _error_categories,
    _lock,
)
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")


def _reset_user_tracking():
    with _lock:
        _client_ips.clear()
        _user_agents.clear()
        _error_categories.clear()


# ── S12-1: Request Tracking ──


class TestRequestTracking:
    def setup_method(self):
        _reset_user_tracking()

    def test_record_request_tracks_ip(self):
        record_request(client_ip="192.168.1.1")
        assert _client_ips["192.168.1.1"] == 1

    def test_record_request_increments_ip(self):
        record_request(client_ip="10.0.0.1")
        record_request(client_ip="10.0.0.1")
        assert _client_ips["10.0.0.1"] == 2

    def test_record_request_categorizes_browser(self):
        record_request(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120")
        assert _user_agents["browser"] >= 1

    def test_record_request_categorizes_mobile(self):
        record_request(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS) Mobile")
        assert _user_agents["mobile"] >= 1

    def test_record_request_categorizes_api(self):
        record_request(user_agent="python-requests/2.31")
        assert _user_agents["api"] >= 1

    def test_record_request_categorizes_bot(self):
        record_request(user_agent="Googlebot/2.1")
        assert _user_agents["bot"] >= 1


# ── S12-2: User Traffic Stats ──


class TestUserTrafficStats:
    def setup_method(self):
        _reset_user_tracking()

    def test_get_user_stats_unique_users(self):
        record_request(client_ip="1.1.1.1")
        record_request(client_ip="2.2.2.2")
        record_request(client_ip="1.1.1.1")
        stats = get_user_stats()
        assert stats["unique_users"] == 2

    def test_get_user_stats_total_requests(self):
        record_request(client_ip="1.1.1.1")
        record_request(client_ip="2.2.2.2")
        stats = get_user_stats()
        assert stats["total_requests"] == 2

    def test_get_user_stats_top_users(self):
        for _ in range(5):
            record_request(client_ip="1.1.1.1")
        record_request(client_ip="2.2.2.2")
        stats = get_user_stats()
        assert "1.1.1.1" in stats["top_users"]
        assert stats["top_users"]["1.1.1.1"] == 5

    def test_user_agents_distribution(self):
        record_request(user_agent="Chrome/120")
        record_request(user_agent="python-httpx/0.25")
        stats = get_user_stats()
        assert "browser" in stats["user_agents"]
        assert "api" in stats["user_agents"]


# ── S12-3: Error Categorization ──


class TestErrorCategorization:
    def setup_method(self):
        _reset_user_tracking()

    def test_record_error_category(self):
        record_error_category("ValueError")
        assert _error_categories["ValueError"] == 1

    def test_multiple_error_categories(self):
        record_error_category("ValueError")
        record_error_category("RuntimeError")
        record_error_category("ValueError")
        assert _error_categories["ValueError"] == 2
        assert _error_categories["RuntimeError"] == 1

    def test_error_categories_in_user_stats(self):
        record_error_category("TimeoutError")
        stats = get_user_stats()
        assert "error_categories" in stats
        assert stats["error_categories"]["TimeoutError"] == 1

    def test_pipeline_wires_error_category(self):
        """Verify pipeline records error category."""
        source = (Path(__file__).parent.parent / "app" / "services" / "pipeline.py").read_text()
        assert "record_error_category" in source


# ── S12-4: Analytics Users Endpoint ──


class TestUsersEndpoint:
    def test_users_endpoint_available(self):
        res = client.get("/analytics/users")
        assert res.status_code == 200

    def test_users_endpoint_has_structure(self):
        res = client.get("/analytics/users")
        data = res.json()
        assert "unique_users" in data
        assert "total_requests" in data
        assert "user_agents" in data
        assert "top_users" in data
        assert "error_categories" in data

    def test_users_endpoint_in_public_paths(self):
        from app.middleware.auth import PUBLIC_PATHS

        assert "/analytics/users" in PUBLIC_PATHS


# ── S12-5: Analytics Export ──


class TestAnalyticsExport:
    def test_export_csv_endpoint(self):
        res = client.get("/analytics/export?format=csv")
        assert res.status_code == 200
        assert "text/csv" in res.headers.get("content-type", "")

    def test_export_csv_has_header(self):
        res = client.get("/analytics/export?format=csv")
        assert "timestamp,uploads,completed,failed,cancelled" in res.text

    def test_export_csv_content_disposition(self):
        res = client.get("/analytics/export?format=csv")
        assert "analytics_export.csv" in res.headers.get("content-disposition", "")

    def test_export_json_endpoint(self):
        res = client.get("/analytics/export?format=json")
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert "users" in data
        assert "timeseries" in data

    def test_export_json_content_disposition(self):
        res = client.get("/analytics/export?format=json")
        assert "analytics_export.json" in res.headers.get("content-disposition", "")

    def test_export_function_returns_csv_string(self):
        csv = export_analytics_csv()
        assert csv.startswith("timestamp,")

    def test_export_in_public_paths(self):
        from app.middleware.auth import PUBLIC_PATHS

        assert "/analytics/export" in PUBLIC_PATHS


# ── S12-6: Middleware Integration ──


class TestMiddlewareIntegration:
    def test_request_log_middleware_tracks_requests(self):
        """Making requests should populate analytics."""
        _reset_user_tracking()
        # Make a few requests to trigger tracking
        client.get("/health")
        client.get("/languages")
        # health is in quiet paths so won't be tracked, but /languages should be
        stats = get_user_stats()
        assert stats["total_requests"] >= 1

    def test_request_tracking_in_middleware_source(self):
        source = (Path(__file__).parent.parent / "app" / "middleware" / "request_log.py").read_text()
        assert "record_request" in source


# ── S12-7: Integration ──


class TestIntegration:
    def test_all_analytics_endpoints(self):
        endpoints = [
            "/analytics/summary",
            "/analytics/timeseries",
            "/analytics/users",
            "/analytics/export",
            "/analytics/export?format=json",
        ]
        for ep in endpoints:
            assert client.get(ep).status_code == 200, f"{ep} failed"

    def test_analytics_page_still_loads(self):
        assert client.get("/analytics").status_code == 200

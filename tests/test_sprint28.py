"""Sprint 28 tests: Query Layer & Data Management.

Tests cover:
  - Task search & filtering
  - Cursor-based pagination
  - Analytics rollup (daily, weekly, monthly)
  - Data retention enforcement
  - Bulk export (CSV, JSON)
  - DB health check
  - Query endpoints
"""

import asyncio

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Query Service Tests ──


class TestQueryService:
    """Test query layer service functions."""

    def test_module_imports(self):
        from app.services import query_layer

        assert hasattr(query_layer, "search_tasks")
        assert hasattr(query_layer, "get_analytics_rollup")
        assert hasattr(query_layer, "enforce_retention")
        assert hasattr(query_layer, "export_tasks_csv")
        assert hasattr(query_layer, "export_tasks_json")
        assert hasattr(query_layer, "check_db_health")

    def test_search_tasks_is_async(self):
        from app.services.query_layer import search_tasks

        assert asyncio.iscoroutinefunction(search_tasks)

    def test_analytics_rollup_is_async(self):
        from app.services.query_layer import get_analytics_rollup

        assert asyncio.iscoroutinefunction(get_analytics_rollup)

    def test_enforce_retention_is_async(self):
        from app.services.query_layer import enforce_retention

        assert asyncio.iscoroutinefunction(enforce_retention)

    def test_check_db_health_is_async(self):
        from app.services.query_layer import check_db_health

        assert asyncio.iscoroutinefunction(check_db_health)

    def test_default_retention_days(self):
        from app.services.query_layer import DEFAULT_RETENTION_DAYS

        assert isinstance(DEFAULT_RETENTION_DAYS, int)
        assert DEFAULT_RETENTION_DAYS > 0


# ── Aggregation Helper Tests ──


class TestAggregationHelpers:
    """Test weekly/monthly aggregation helpers."""

    def test_weekly_aggregation(self):
        from app.services.query_layer import _aggregate_by_week

        daily = [
            {
                "date": "2026-03-09",
                "uploads": 5,
                "completed": 3,
                "failed": 1,
                "cancelled": 0,
                "total_processing_sec": 100.0,
            },
            {
                "date": "2026-03-10",
                "uploads": 3,
                "completed": 2,
                "failed": 0,
                "cancelled": 1,
                "total_processing_sec": 50.0,
            },
        ]
        result = _aggregate_by_week(daily)
        assert isinstance(result, list)
        if result:
            assert "week" in result[0]
            assert "uploads" in result[0]

    def test_monthly_aggregation(self):
        from app.services.query_layer import _aggregate_by_month

        daily = [
            {
                "date": "2026-03-01",
                "uploads": 10,
                "completed": 8,
                "failed": 1,
                "cancelled": 1,
                "total_processing_sec": 200.0,
            },
            {
                "date": "2026-03-15",
                "uploads": 5,
                "completed": 5,
                "failed": 0,
                "cancelled": 0,
                "total_processing_sec": 100.0,
            },
        ]
        result = _aggregate_by_month(daily)
        assert isinstance(result, list)
        if result:
            assert "month" in result[0]
            assert result[0]["uploads"] == 15  # Aggregated

    def test_empty_aggregation(self):
        from app.services.query_layer import _aggregate_by_month, _aggregate_by_week

        assert _aggregate_by_week([]) == []
        assert _aggregate_by_month([]) == []


# ── Task Search Endpoint Tests ──


class TestTaskSearchEndpoint:
    """Test GET /tasks/search endpoint."""

    def test_search_returns_ok(self):
        res = client.get("/tasks/search")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data

    def test_search_with_status_filter(self):
        res = client.get("/tasks/search?status=completed")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["items"], list)

    def test_search_with_limit(self):
        res = client.get("/tasks/search?limit=5")
        assert res.status_code == 200
        assert len(res.json()["items"]) <= 5

    def test_search_with_sort(self):
        res = client.get("/tasks/search?sort=asc")
        assert res.status_code == 200

    def test_search_with_filename(self):
        res = client.get("/tasks/search?filename=test")
        assert res.status_code == 200

    def test_search_pagination_structure(self):
        res = client.get("/tasks/search")
        data = res.json()
        assert "next_cursor" in data


# ── Analytics Rollup Endpoint Tests ──


class TestAnalyticsRollupEndpoint:
    """Test GET /analytics/rollup endpoint."""

    def test_rollup_daily(self):
        res = client.get("/analytics/rollup?period=daily")
        assert res.status_code == 200
        data = res.json()
        assert data["period"] == "daily"
        assert "data" in data

    def test_rollup_weekly(self):
        res = client.get("/analytics/rollup?period=weekly")
        assert res.status_code == 200
        assert res.json()["period"] == "weekly"

    def test_rollup_monthly(self):
        res = client.get("/analytics/rollup?period=monthly")
        assert res.status_code == 200
        assert res.json()["period"] == "monthly"

    def test_rollup_custom_days(self):
        res = client.get("/analytics/rollup?days=7")
        assert res.status_code == 200
        assert res.json()["days"] == 7


# ── Data Retention Endpoint Tests ──


class TestRetentionEndpoint:
    """Test POST /admin/retention endpoint."""

    def test_retention_returns_ok(self):
        res = client.post("/admin/retention?days=365")
        assert res.status_code == 200
        data = res.json()
        assert "retention_days" in data
        assert "deleted" in data

    def test_retention_with_custom_days(self):
        res = client.post("/admin/retention?days=30")
        assert res.status_code == 200
        assert res.json()["retention_days"] == 30


# ── Export Endpoint Tests ──


class TestExportEndpoint:
    """Test GET /admin/export/tasks endpoint."""

    def test_export_json(self):
        res = client.get("/admin/export/tasks?format=json")
        assert res.status_code == 200
        data = res.json()
        assert "tasks" in data
        assert "count" in data

    def test_export_csv(self):
        res = client.get("/admin/export/tasks?format=csv")
        assert res.status_code == 200
        assert "text/csv" in res.headers.get("content-type", "")

    def test_export_with_limit(self):
        res = client.get("/admin/export/tasks?format=json&limit=5")
        assert res.status_code == 200
        assert res.json()["count"] <= 5

    def test_export_with_status_filter(self):
        res = client.get("/admin/export/tasks?format=json&status=completed")
        assert res.status_code == 200


# ── DB Health Endpoint Tests ──


class TestDbHealthEndpoint:
    """Test GET /health/db endpoint."""

    def test_db_health_returns_ok(self):
        res = client.get("/health/db")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "ok" in data

    def test_db_health_has_latency(self):
        res = client.get("/health/db")
        data = res.json()
        if data["ok"]:
            assert "latency_ms" in data

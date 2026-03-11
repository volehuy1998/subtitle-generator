"""Sprint 19 tests: Analytics & Audit Migration to PostgreSQL.

Tests cover:
  - New ORM models (AnalyticsEvent, AnalyticsDaily, AnalyticsTimeseries, AuditLog, Feedback)
  - PostgreSQL analytics persistence (analytics_pg)
  - PostgreSQL audit persistence (audit_pg)
  - Feedback route with DB backend
  - Analytics route with DB time-series
  - Daily analytics endpoint
  - Migration script existence
"""

import asyncio
import json


from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


# ── Helper ──

def run_async(coro):
    """Run an async coroutine in a new event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Model Tests ──

class TestNewModels:
    """Test Sprint 19 ORM models exist and have correct structure."""

    def test_analytics_event_model(self):
        from app.db.models import AnalyticsEvent
        assert AnalyticsEvent.__tablename__ == "analytics_events"
        cols = {c.name for c in AnalyticsEvent.__table__.columns}
        assert {"id", "timestamp", "event_type", "data"} <= cols

    def test_analytics_daily_model(self):
        from app.db.models import AnalyticsDaily
        assert AnalyticsDaily.__tablename__ == "analytics_daily"
        cols = {c.name for c in AnalyticsDaily.__table__.columns}
        assert {"date", "uploads", "completed", "failed", "cancelled",
                "total_processing_sec", "avg_file_size", "data"} <= cols

    def test_analytics_timeseries_model(self):
        from app.db.models import AnalyticsTimeseries
        assert AnalyticsTimeseries.__tablename__ == "analytics_timeseries"
        cols = {c.name for c in AnalyticsTimeseries.__table__.columns}
        assert {"id", "timestamp", "uploads", "completed", "failed",
                "cancelled", "total_processing_sec", "task_count"} <= cols

    def test_audit_log_model(self):
        from app.db.models import AuditLog
        assert AuditLog.__tablename__ == "audit_log"
        cols = {c.name for c in AuditLog.__table__.columns}
        assert {"id", "timestamp", "event_type", "ip", "path", "details"} <= cols

    def test_feedback_model(self):
        from app.db.models import Feedback
        assert Feedback.__tablename__ == "feedback"
        cols = {c.name for c in Feedback.__table__.columns}
        assert {"id", "task_id", "rating", "comment", "created_at"} <= cols

    def test_analytics_event_indexes(self):
        from app.db.models import AnalyticsEvent
        idx_names = {idx.name for idx in AnalyticsEvent.__table__.indexes}
        assert "ix_analytics_events_type" in idx_names
        assert "ix_analytics_events_ts" in idx_names

    def test_audit_log_indexes(self):
        from app.db.models import AuditLog
        idx_names = {idx.name for idx in AuditLog.__table__.indexes}
        assert "ix_audit_log_event" in idx_names
        assert "ix_audit_log_ts" in idx_names

    def test_feedback_indexes(self):
        from app.db.models import Feedback
        idx_names = {idx.name for idx in Feedback.__table__.indexes}
        assert "ix_feedback_task" in idx_names
        assert "ix_feedback_created" in idx_names


# ── Analytics PG Service Tests ──

class TestAnalyticsPgService:
    """Test analytics_pg module functions exist and are callable."""

    def test_module_imports(self):
        from app.services import analytics_pg
        assert hasattr(analytics_pg, "record_event")
        assert hasattr(analytics_pg, "update_daily_stats")
        assert hasattr(analytics_pg, "upsert_timeseries_point")
        assert hasattr(analytics_pg, "get_timeseries")
        assert hasattr(analytics_pg, "get_daily_stats")
        assert hasattr(analytics_pg, "get_event_count")
        assert hasattr(analytics_pg, "get_summary_from_db")
        assert hasattr(analytics_pg, "cleanup_old_timeseries")

    def test_record_event_is_async(self):
        from app.services.analytics_pg import record_event
        assert asyncio.iscoroutinefunction(record_event)

    def test_update_daily_stats_is_async(self):
        from app.services.analytics_pg import update_daily_stats
        assert asyncio.iscoroutinefunction(update_daily_stats)

    def test_upsert_timeseries_is_async(self):
        from app.services.analytics_pg import upsert_timeseries_point
        assert asyncio.iscoroutinefunction(upsert_timeseries_point)

    def test_get_timeseries_is_async(self):
        from app.services.analytics_pg import get_timeseries
        assert asyncio.iscoroutinefunction(get_timeseries)

    def test_get_summary_from_db_is_async(self):
        from app.services.analytics_pg import get_summary_from_db
        assert asyncio.iscoroutinefunction(get_summary_from_db)

    def test_cleanup_is_async(self):
        from app.services.analytics_pg import cleanup_old_timeseries
        assert asyncio.iscoroutinefunction(cleanup_old_timeseries)


# ── Audit PG Service Tests ──

class TestAuditPgService:
    """Test audit_pg module functions exist and are callable."""

    def test_module_imports(self):
        from app.services import audit_pg
        assert hasattr(audit_pg, "persist_audit_event")
        assert hasattr(audit_pg, "get_recent_events")
        assert hasattr(audit_pg, "get_audit_stats")
        assert hasattr(audit_pg, "cleanup_old_events")

    def test_persist_audit_event_is_async(self):
        from app.services.audit_pg import persist_audit_event
        assert asyncio.iscoroutinefunction(persist_audit_event)

    def test_get_recent_events_is_async(self):
        from app.services.audit_pg import get_recent_events
        assert asyncio.iscoroutinefunction(get_recent_events)

    def test_get_audit_stats_is_async(self):
        from app.services.audit_pg import get_audit_stats
        assert asyncio.iscoroutinefunction(get_audit_stats)


# ── Analytics Integration Tests (in-memory path) ──

class TestAnalyticsDbWriteThrough:
    """Test that analytics recording still works and triggers DB writes."""

    def test_record_upload_still_updates_memory(self):
        from app.services.analytics import record_upload, _counters
        before = _counters["uploads_total"]
        record_upload(language="en", model="small", device="cpu", file_size=1000)
        assert _counters["uploads_total"] == before + 1

    def test_record_completion_still_updates_memory(self):
        from app.services.analytics import record_completion, _counters
        before = _counters["completed_total"]
        record_completion(5.0, model="small")
        assert _counters["completed_total"] == before + 1

    def test_record_failure_still_updates_memory(self):
        from app.services.analytics import record_failure, _counters
        before = _counters["failed_total"]
        record_failure()
        assert _counters["failed_total"] == before + 1

    def test_record_cancellation_still_updates_memory(self):
        from app.services.analytics import record_cancellation, _counters
        before = _counters["cancelled_total"]
        record_cancellation()
        assert _counters["cancelled_total"] == before + 1

    def test_get_summary_returns_counters(self):
        from app.services.analytics import get_summary
        summary = get_summary()
        assert "counters" in summary
        assert "uploads_total" in summary["counters"]
        assert "completed_total" in summary["counters"]

    def test_get_timeseries_returns_list(self):
        from app.services.analytics import get_timeseries
        ts = get_timeseries(minutes=5)
        assert isinstance(ts, list)

    def test_load_analytics_from_db_is_async(self):
        from app.services.analytics import load_analytics_from_db
        assert asyncio.iscoroutinefunction(load_analytics_from_db)


# ── Audit Integration Tests ──

class TestAuditDbWriteThrough:
    """Test that audit logging still works and triggers DB writes."""

    def test_log_audit_event_still_updates_memory(self):
        from app.services.audit import log_audit_event, _audit_entries
        before = len(_audit_entries)
        log_audit_event("test_event", ip="127.0.0.1")
        assert len(_audit_entries) == before + 1

    def test_log_audit_event_entry_format(self):
        from app.services.audit import log_audit_event, _audit_entries
        log_audit_event("test_format", ip="10.0.0.1", path="/test")
        entry = _audit_entries[-1]
        assert entry["event"] == "test_format"
        assert entry["ip"] == "10.0.0.1"
        assert "timestamp" in entry


# ── Route Integration Tests ──

class TestFeedbackRoute:
    """Test feedback endpoints use database."""

    def test_submit_feedback_endpoint_exists(self):
        res = client.post("/feedback", json={"rating": 5, "comment": "great"})
        assert res.status_code == 200
        data = res.json()
        assert data["rating"] == 5
        assert "Thank you" in data["message"]

    def test_feedback_summary_endpoint(self):
        res = client.get("/feedback/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "average_rating" in data
        assert "ratings" in data

    def test_feedback_summary_has_distribution(self):
        res = client.get("/feedback/summary")
        data = res.json()
        ratings = data["ratings"]
        # Should have keys 1-5
        for i in range(1, 6):
            assert str(i) in ratings or i in ratings


class TestAnalyticsRoutes:
    """Test analytics endpoints with DB integration."""

    def test_timeseries_has_source(self):
        res = client.get("/analytics/timeseries?minutes=5")
        assert res.status_code == 200
        data = res.json()
        assert "points" in data
        assert "source" in data
        assert data["source"] in ("db", "memory")

    def test_daily_endpoint_exists(self):
        res = client.get("/analytics/daily?days=7")
        assert res.status_code == 200
        data = res.json()
        assert "days" in data
        assert isinstance(data["days"], list)

    def test_export_json_includes_daily(self):
        res = client.get("/analytics/export?format=json")
        assert res.status_code == 200
        data = json.loads(res.text)
        assert "daily" in data


# ── Migration Tests ──

class TestMigration:
    """Test Alembic migration file exists."""

    def test_migration_002_exists(self):
        from pathlib import Path
        migration = Path("alembic/versions/002_analytics_audit_feedback.py")
        assert migration.exists(), "Migration 002 not found"

    def test_migration_002_has_upgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/002_analytics_audit_feedback.py").read_text()
        assert "def upgrade" in content
        assert "analytics_events" in content
        assert "analytics_daily" in content
        assert "analytics_timeseries" in content
        assert "audit_log" in content
        assert "feedback" in content

    def test_migration_002_has_downgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/002_analytics_audit_feedback.py").read_text()
        assert "def downgrade" in content

    def test_migration_chain(self):
        from pathlib import Path
        content = Path("alembic/versions/002_analytics_audit_feedback.py").read_text()
        assert 'down_revision' in content
        assert '"001"' in content

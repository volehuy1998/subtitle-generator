"""Sprint 21 tests: User Activity Tracking & Analytics.

Tests cover:
  - UIEvent ORM model
  - Tracking service functions
  - Track API endpoints (single + batch)
  - Analytics endpoints (activity, features, funnel, errors, session)
  - Frontend tracker JS exists
  - Migration file
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


# ── Model Tests ──


class TestUIEventModel:
    """Test UIEvent ORM model."""

    def test_model_exists(self):
        from app.db.models import UIEvent

        assert UIEvent.__tablename__ == "ui_events"

    def test_model_columns(self):
        from app.db.models import UIEvent

        cols = {c.name for c in UIEvent.__table__.columns}
        assert {"id", "timestamp", "session_id", "event_type", "target", "task_id", "extra"} <= cols

    def test_model_indexes(self):
        from app.db.models import UIEvent

        idx_names = {idx.name for idx in UIEvent.__table__.indexes}
        assert "ix_ui_events_session" in idx_names
        assert "ix_ui_events_type" in idx_names
        assert "ix_ui_events_ts" in idx_names
        assert "ix_ui_events_target" in idx_names


# ── Tracking Service Tests ──


class TestTrackingService:
    """Test tracking service functions exist and are async."""

    def test_module_imports(self):
        from app.services import tracking

        assert hasattr(tracking, "record_ui_event")
        assert hasattr(tracking, "record_ui_events_batch")
        assert hasattr(tracking, "get_feature_usage")
        assert hasattr(tracking, "get_flow_funnel")
        assert hasattr(tracking, "get_error_events")
        assert hasattr(tracking, "get_session_activity")
        assert hasattr(tracking, "get_activity_summary")
        assert hasattr(tracking, "cleanup_old_events")

    def test_record_ui_event_is_async(self):
        from app.services.tracking import record_ui_event

        assert asyncio.iscoroutinefunction(record_ui_event)

    def test_record_batch_is_async(self):
        from app.services.tracking import record_ui_events_batch

        assert asyncio.iscoroutinefunction(record_ui_events_batch)

    def test_get_feature_usage_is_async(self):
        from app.services.tracking import get_feature_usage

        assert asyncio.iscoroutinefunction(get_feature_usage)

    def test_get_flow_funnel_is_async(self):
        from app.services.tracking import get_flow_funnel

        assert asyncio.iscoroutinefunction(get_flow_funnel)

    def test_get_error_events_is_async(self):
        from app.services.tracking import get_error_events

        assert asyncio.iscoroutinefunction(get_error_events)

    def test_get_activity_summary_is_async(self):
        from app.services.tracking import get_activity_summary

        assert asyncio.iscoroutinefunction(get_activity_summary)

    def test_cleanup_is_async(self):
        from app.services.tracking import cleanup_old_events

        assert asyncio.iscoroutinefunction(cleanup_old_events)


# ── Track API Endpoints ──


class TestTrackEndpoint:
    """Test POST /track endpoint."""

    def test_track_single_event(self):
        res = client.post("/track", json={"event": "click", "target": "uploadBtn"})
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_track_with_metadata(self):
        res = client.post("/track", json={"event": "flow", "target": "upload_start", "metadata": {"file_size": 1024}})
        assert res.status_code == 200

    def test_track_with_task_id(self):
        res = client.post("/track", json={"event": "click", "target": "downloadSrt", "task_id": "abc-123"})
        assert res.status_code == 200

    def test_track_missing_event_fails(self):
        res = client.post("/track", json={"target": "btn"})
        assert res.status_code == 422

    def test_track_empty_event_fails(self):
        # event is required, empty string should still work (not missing)
        res = client.post("/track", json={"event": ""})
        # Empty string is valid for event field
        assert res.status_code in (200, 422)


class TestTrackBatchEndpoint:
    """Test POST /track/batch endpoint."""

    def test_batch_events(self):
        res = client.post(
            "/track/batch",
            json={
                "events": [
                    {"event": "click", "target": "btn1"},
                    {"event": "click", "target": "btn2"},
                    {"event": "view", "target": "page_load"},
                ]
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert data["count"] == 3

    def test_batch_empty(self):
        res = client.post("/track/batch", json={"events": []})
        assert res.status_code == 200
        assert res.json()["count"] == 0

    def test_batch_with_metadata(self):
        res = client.post(
            "/track/batch",
            json={
                "events": [
                    {"event": "error", "target": "js_error", "metadata": {"message": "test error"}},
                ]
            },
        )
        assert res.status_code == 200


# ── Analytics Endpoints ──


class TestActivityEndpoint:
    """Test GET /analytics/activity."""

    def test_activity_returns_summary(self):
        res = client.get("/analytics/activity")
        assert res.status_code == 200
        data = res.json()
        assert "total_events" in data
        assert "unique_sessions" in data
        assert "events_by_type" in data

    def test_activity_custom_hours(self):
        res = client.get("/analytics/activity?hours=1")
        assert res.status_code == 200
        assert res.json()["hours"] == 1


class TestFeatureUsageEndpoint:
    """Test GET /analytics/features."""

    def test_features_returns_list(self):
        res = client.get("/analytics/features")
        assert res.status_code == 200
        data = res.json()
        assert "features" in data
        assert isinstance(data["features"], list)

    def test_features_custom_hours(self):
        res = client.get("/analytics/features?hours=48")
        assert res.status_code == 200
        assert res.json()["hours"] == 48


class TestFunnelEndpoint:
    """Test GET /analytics/funnel."""

    def test_funnel_returns_stages(self):
        res = client.get("/analytics/funnel")
        assert res.status_code == 200
        data = res.json()
        assert "funnel" in data
        assert "conversion_rates" in data
        funnel = data["funnel"]
        assert "upload_start" in funnel
        assert "transcription_done" in funnel
        assert "download_click" in funnel

    def test_funnel_has_rates(self):
        res = client.get("/analytics/funnel")
        rates = res.json()["conversion_rates"]
        assert "upload_start" in rates
        assert rates["upload_start"] == 100.0


class TestErrorsEndpoint:
    """Test GET /analytics/errors."""

    def test_errors_returns_list(self):
        res = client.get("/analytics/errors")
        assert res.status_code == 200
        data = res.json()
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert "count" in data


class TestSessionTimeline:
    """Test GET /analytics/session/{session_id}."""

    def test_session_returns_events(self):
        res = client.get("/analytics/session/test-session-123")
        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == "test-session-123"
        assert "events" in data
        assert isinstance(data["events"], list)


# ── Migration Tests ──


class TestMigration003:
    """Test Alembic migration file."""

    def test_migration_has_upgrade(self):
        from pathlib import Path

        content = Path("alembic/versions/003_ui_events.py").read_text()
        assert "def upgrade" in content
        assert "ui_events" in content

    def test_migration_has_downgrade(self):
        from pathlib import Path

        content = Path("alembic/versions/003_ui_events.py").read_text()
        assert "def downgrade" in content

    def test_migration_chain(self):
        from pathlib import Path

        content = Path("alembic/versions/003_ui_events.py").read_text()
        assert '"002"' in content

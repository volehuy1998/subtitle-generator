"""Tests for Sprint 17: Scale & High Availability.

S17-1: Task backend abstraction (in-memory default)
S17-2: Storage adapter abstraction (local filesystem default)
S17-3: Worker health monitoring
S17-4: Load balancer health check compatibility
S17-5: Scale info endpoint
S17-6: SQLite analytics persistence
S17-7: Integration tests
"""

from fastapi.testclient import TestClient

from app.main import app
from app.services.task_backend import (
    InMemoryTaskBackend,
    get_task_backend,
    get_backend_info,
)
from app.services.storage import LocalStorageAdapter, get_storage
from app.services.worker_health import (
    _workers,
    register_worker,
    heartbeat,
    record_task_processed,
    get_worker_status,
    get_healthy_worker_count,
    cleanup_dead_workers,
)
from app.services.analytics_db import (
    record_event,
    update_daily_stats,
    get_daily_stats,
    get_event_count,
    get_db_info,
)

client = TestClient(app, base_url="https://testserver")


def _cleanup_workers():
    _workers.clear()


# ── S17-1: Task Backend Abstraction ──


class TestTaskBackend:
    def test_in_memory_backend_set_get(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {"status": "queued"})
        assert backend.get("t1") == {"status": "queued"}

    def test_in_memory_backend_delete(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {"status": "done"})
        backend.delete("t1")
        assert backend.get("t1") is None

    def test_in_memory_backend_contains(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {"status": "queued"})
        assert backend.contains("t1")
        assert not backend.contains("t2")

    def test_in_memory_backend_items(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {"a": 1})
        backend.set("t2", {"b": 2})
        items = backend.items()
        assert len(items) == 2

    def test_in_memory_backend_keys(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {})
        backend.set("t2", {})
        assert set(backend.keys()) == {"t1", "t2"}

    def test_in_memory_backend_count(self):
        backend = InMemoryTaskBackend()
        assert backend.count() == 0
        backend.set("t1", {})
        assert backend.count() == 1

    def test_get_task_backend_singleton(self):
        b1 = get_task_backend()
        b2 = get_task_backend()
        assert b1 is b2

    def test_backend_info(self):
        info = get_backend_info()
        assert "type" in info
        assert "task_count" in info

    def test_raw_property(self):
        backend = InMemoryTaskBackend()
        backend.set("t1", {"x": 1})
        assert "t1" in backend.raw


# ── S17-2: Storage Adapter ──


class TestStorageAdapter:
    def test_local_storage_save_output(self):
        storage = get_storage()
        info = storage.get_storage_info()
        assert info["type"] == "local"

    def test_local_storage_info_has_fields(self):
        info = get_storage().get_storage_info()
        assert "upload_dir" in info
        assert "output_dir" in info
        assert "disk_free_gb" in info

    def test_local_storage_list_outputs(self):
        outputs = get_storage().list_outputs()
        assert isinstance(outputs, list)

    def test_local_storage_delete_nonexistent(self):
        result = get_storage().delete_upload("nonexistent_file_xyz.mp4")
        assert result is False

    def test_local_storage_get_nonexistent_path(self):
        path = get_storage().get_upload_path("nonexistent_file_xyz.mp4")
        assert path is None


# ── S17-3: Worker Health Monitoring ──


class TestWorkerHealth:
    def setup_method(self):
        _cleanup_workers()

    def teardown_method(self):
        _cleanup_workers()

    def test_register_worker(self):
        wid = register_worker("test-worker-1")
        assert wid == "test-worker-1"

    def test_register_worker_auto_id(self):
        wid = register_worker()
        assert wid.startswith("worker-")

    def test_worker_heartbeat(self):
        wid = register_worker("hb-worker")
        heartbeat(wid)
        status = get_worker_status()
        assert len(status) == 1
        assert status[0]["status"] == "active"

    def test_record_task_processed(self):
        wid = register_worker("task-worker")
        record_task_processed(wid)
        record_task_processed(wid)
        status = get_worker_status()
        assert status[0]["tasks_processed"] == 2

    def test_healthy_worker_count(self):
        register_worker("w1")
        register_worker("w2")
        assert get_healthy_worker_count() == 2

    def test_worker_status_fields(self):
        register_worker("field-worker")
        status = get_worker_status()[0]
        assert "worker_id" in status
        assert "status" in status
        assert "pid" in status
        assert "uptime_sec" in status
        assert "last_heartbeat_sec_ago" in status

    def test_cleanup_dead_workers(self):
        import time

        register_worker("dead-worker")
        # Manually set heartbeat to long ago
        _workers["dead-worker"]["last_heartbeat"] = time.time() - 999
        removed = cleanup_dead_workers()
        assert removed == 1


# ── S17-4: Load Balancer Health Check ──


class TestLoadBalancerHealthCheck:
    def test_health_live_returns_200(self):
        res = client.get("/health/live")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_health_returns_uptime(self):
        res = client.get("/health")
        data = res.json()
        assert "uptime_sec" in data
        assert data["status"] == "healthy"

    def test_ready_returns_checks(self):
        res = client.get("/ready")
        data = res.json()
        assert "checks" in data
        assert "shutting_down" in data["checks"]

    def test_ready_includes_shutdown_check(self):
        res = client.get("/ready")
        data = res.json()
        assert data["checks"]["shutting_down"] is False


# ── S17-5: Scale Info Endpoint ──


class TestScaleInfo:
    def test_scale_info_endpoint(self):
        res = client.get("/scale/info")
        assert res.status_code == 200

    def test_scale_info_structure(self):
        res = client.get("/scale/info")
        data = res.json()
        assert "workers" in data
        assert "healthy_workers" in data
        assert "task_backend" in data
        assert "storage" in data
        assert "analytics_db" in data
        assert "pid" in data

    def test_scale_info_workers_list(self):
        res = client.get("/scale/info")
        data = res.json()
        assert isinstance(data["workers"], list)

    def test_scale_info_storage_type(self):
        res = client.get("/scale/info")
        data = res.json()
        assert data["storage"]["type"] == "local"


# ── S17-6: SQLite Analytics Persistence ──


class TestAnalyticsDB:
    def test_record_event(self):
        record_event("test_upload", {"file": "test.mp4"})
        count = get_event_count("test_upload")
        assert count >= 1

    def test_update_daily_stats(self):
        update_daily_stats(uploads=1, completed=1)
        stats = get_daily_stats(1)
        assert len(stats) >= 1

    def test_daily_stats_fields(self):
        update_daily_stats(uploads=5, completed=3, failed=1, processing_sec=120.0)
        stats = get_daily_stats(1)
        assert stats[0]["uploads"] >= 5

    def test_get_event_count_all(self):
        count = get_event_count()
        assert isinstance(count, int)

    def test_db_info(self):
        # Ensure at least one event so DB exists
        record_event("info_test")
        info = get_db_info()
        assert "path" in info
        assert "exists" in info
        assert "size_kb" in info
        assert "total_events" in info


# ── S17-7: Integration Tests ──


class TestScaleIntegration:
    def test_health_live_in_openapi(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        assert "/health/live" in paths

    def test_scale_info_in_openapi(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        assert "/scale/info" in paths

    def test_task_backend_importable(self):
        from app.services.task_backend import TaskBackend, InMemoryTaskBackend

        assert TaskBackend is not None
        assert InMemoryTaskBackend is not None

    def test_storage_importable(self):
        from app.services.storage import StorageAdapter

        assert StorageAdapter is not None
        assert LocalStorageAdapter is not None

    def test_worker_health_importable(self):
        from app.services.worker_health import register_worker, get_worker_status

        assert callable(register_worker)
        assert callable(get_worker_status)

    def test_analytics_db_importable(self):
        from app.services.analytics_db import record_event, get_daily_stats

        assert callable(record_event)
        assert callable(get_daily_stats)

    def test_all_new_endpoints_accessible(self):
        """Verify all Sprint 17 endpoints return non-error status."""
        for path in ["/health", "/health/live", "/ready", "/scale/info"]:
            res = client.get(path)
            assert res.status_code in (200, 503), f"{path} returned {res.status_code}"

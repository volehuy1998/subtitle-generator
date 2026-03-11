"""Sprint 27 tests: Scalability & Multi-Instance.

Tests cover:
  - MemoryCache (Redis fallback)
  - Worker management (register, heartbeat, cleanup)
  - Connection pool configuration
  - Task queue abstraction
  - Scale info endpoint
"""

import time

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Cache Backend Tests ──

class TestMemoryCache:
    """Test in-memory cache backend."""

    def test_cache_exists(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        assert cache is not None

    def test_set_and_get(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

    def test_get_missing_key(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        assert cache.get("nonexistent_key_xyz") is None

    def test_delete(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        cache.set("del_key", "value")
        assert cache.delete("del_key") is True
        assert cache.get("del_key") is None

    def test_exists(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        cache.set("exists_key", "yes")
        assert cache.exists("exists_key") is True
        assert cache.exists("nope_key_xyz") is False

    def test_incr(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        cache.set("counter", "5")
        result = cache.incr("counter")
        assert result == 6

    def test_incr_new_key(self):
        from app.services.scaling import get_cache
        cache = get_cache()
        result = cache.incr(f"new_counter_{time.time()}")
        assert result == 1

    def test_ttl_expiry(self):
        from app.services.scaling import MemoryCache
        cache = MemoryCache()
        cache.set("ttl_key", "value", ttl=1)
        assert cache.get("ttl_key") == "value"
        time.sleep(1.1)
        assert cache.get("ttl_key") is None

    def test_keys_pattern(self):
        from app.services.scaling import MemoryCache
        cache = MemoryCache()
        cache.set("session:abc", "1")
        cache.set("session:def", "2")
        cache.set("other:xyz", "3")
        keys = cache.keys("session:*")
        assert "session:abc" in keys
        assert "session:def" in keys
        assert "other:xyz" not in keys

    def test_stats(self):
        from app.services.scaling import get_cache
        stats = get_cache().stats()
        assert "total_keys" in stats
        assert "active_keys" in stats


# ── Worker Management Tests ──

class TestWorkerManagement:
    """Test worker registration and heartbeat."""

    def test_get_worker_id(self):
        from app.services.scaling import get_worker_id
        wid = get_worker_id()
        assert isinstance(wid, str)
        assert len(wid) > 0

    def test_register_worker(self):
        from app.services.scaling import register_worker, get_workers
        register_worker("test-worker-1", hostname="test-host")
        workers = get_workers()
        ids = [w["id"] for w in workers]
        assert "test-worker-1" in ids

    def test_heartbeat_worker(self):
        from app.services.scaling import register_worker, heartbeat_worker, get_workers
        register_worker("heartbeat-test")
        heartbeat_worker("heartbeat-test")
        workers = get_workers()
        w = next(w for w in workers if w["id"] == "heartbeat-test")
        assert "last_heartbeat" in w

    def test_cleanup_dead_workers(self):
        from app.services.scaling import register_worker, cleanup_dead_workers, _workers, _workers_lock
        register_worker("dead-worker")
        # Manually set old heartbeat
        with _workers_lock:
            from datetime import datetime, timedelta, timezone
            old = (datetime.now(timezone.utc) - timedelta(seconds=300)).isoformat()
            _workers["dead-worker"]["last_heartbeat"] = old
        removed = cleanup_dead_workers(timeout_sec=60)
        assert removed >= 1

    def test_get_workers_returns_list(self):
        from app.services.scaling import get_workers
        workers = get_workers()
        assert isinstance(workers, list)


# ── Connection Pool Config Tests ──

class TestPoolConfig:
    """Test connection pool configuration."""

    def test_pool_config(self):
        from app.services.scaling import get_pool_config
        config = get_pool_config()
        assert "pool_size" in config
        assert "max_overflow" in config
        assert "pool_recycle" in config
        assert "pool_pre_ping" in config

    def test_pool_size_positive(self):
        from app.services.scaling import get_pool_config
        config = get_pool_config()
        assert config["pool_size"] > 0

    def test_pool_env_vars(self):
        from app.config import DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
        assert isinstance(DB_POOL_SIZE, int)
        assert isinstance(DB_MAX_OVERFLOW, int)
        assert isinstance(DB_POOL_RECYCLE, int)


# ── Task Queue Tests ──

class TestTaskQueue:
    """Test in-memory task queue."""

    def test_queue_exists(self):
        from app.services.scaling import get_task_queue
        q = get_task_queue()
        assert q is not None

    def test_enqueue_dequeue(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        q.enqueue({"task_id": "t1"})
        item = q.dequeue()
        assert item == {"task_id": "t1"}

    def test_queue_fifo(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        q.enqueue({"id": "1"})
        q.enqueue({"id": "2"})
        assert q.dequeue()["id"] == "1"
        assert q.dequeue()["id"] == "2"

    def test_queue_empty_dequeue(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        assert q.dequeue() is None

    def test_queue_size(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        q.enqueue({"id": "a"})
        q.enqueue({"id": "b"})
        assert q.size() == 2

    def test_queue_max_size(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue(max_size=2)
        assert q.enqueue({"id": "1"}) is True
        assert q.enqueue({"id": "2"}) is True
        assert q.enqueue({"id": "3"}) is False  # Full

    def test_queue_peek(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        q.enqueue({"id": "peek"})
        assert q.peek()["id"] == "peek"
        assert q.size() == 1  # Not removed

    def test_queue_clear(self):
        from app.services.scaling import InMemoryTaskQueue
        q = InMemoryTaskQueue()
        q.enqueue({"id": "1"})
        q.clear()
        assert q.size() == 0


# ── Scale Info Tests ──

class TestScaleInfo:
    """Test scale info endpoint."""

    def test_scale_info_endpoint(self):
        res = client.get("/scale/info")
        assert res.status_code == 200
        data = res.json()
        # Existing endpoint has workers, task_backend, storage
        assert "workers" in data or "worker_id" in data

    def test_scale_info_has_workers(self):
        res = client.get("/scale/info")
        data = res.json()
        assert "workers" in data or "worker_id" in data

    def test_scale_info_function(self):
        from app.services.scaling import get_scale_info
        info = get_scale_info()
        assert "worker_id" in info
        assert "redis_enabled" in info
        assert "pool_config" in info
        assert "cache_stats" in info
        assert "queue_size" in info


# ── Redis Config Tests ──

class TestRedisConfig:
    """Test Redis configuration."""

    def test_redis_url_config(self):
        from app.services.scaling import REDIS_URL, REDIS_ENABLED
        assert isinstance(REDIS_URL, str)
        assert isinstance(REDIS_ENABLED, bool)

    def test_redis_disabled_by_default(self):
        from app.services.scaling import REDIS_ENABLED
        # Should be disabled unless REDIS_URL is set
        import os
        if not os.environ.get("REDIS_URL"):
            assert REDIS_ENABLED is False

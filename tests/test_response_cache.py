"""Tests for app/services/response_cache.py — TTL cache decorator and cache_clear().

**Scout (QA Lead) — Team Sentinel**

Covers:
  1. Cache hit (second call returns cached result)
  2. Cache miss after TTL expiry
  3. Cache key isolation by path + query
  4. cache_clear() — clear all
  5. cache_clear(prefix) — clear matching prefix only
  6. Thread safety under concurrent access
  7–11. Integration tests for cached endpoints
"""

import asyncio
import time
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.response_cache import _caches, cache_clear, ttl_cache

client = TestClient(app, base_url="https://testserver")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_loop = asyncio.new_event_loop()


def run(coro):
    """Run an async coroutine synchronously."""
    return _loop.run_until_complete(coro)


def _clear_all_caches() -> None:
    """Reset every registered cache store so tests are isolated."""
    for store in _caches.values():
        store.clear()


def _make_request(path: str = "/test", query: str = "") -> MagicMock:
    req = MagicMock()
    req.url.path = path
    req.url.query = query
    return req


# ---------------------------------------------------------------------------
# Unit tests — ttl_cache decorator
# ---------------------------------------------------------------------------


class TestTTLCacheHit:
    """1. Second call returns cached result (function not re-invoked)."""

    def setup_method(self):
        _clear_all_caches()

    def test_second_call_returns_cached_value(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"n": call_count}

        req = _make_request("/cache-hit")

        result1 = run(handler(req))
        result2 = run(handler(req))

        assert result1 == {"n": 1}
        assert result2 == {"n": 1}
        assert call_count == 1


class TestTTLCacheMissAfterTTL:
    """2. After TTL expires the function is re-invoked."""

    def setup_method(self):
        _clear_all_caches()

    def test_recomputes_after_ttl(self):
        call_count = 0

        @ttl_cache(seconds=1)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"n": call_count}

        req = _make_request("/ttl-miss")

        result1 = run(handler(req))
        assert result1 == {"n": 1}

        # Expire the entry by setting its timestamp to the past
        store = _caches[handler.cache_name]
        for key in store:
            _ts, val = store[key]
            store[key] = (time.monotonic() - 1, val)

        result2 = run(handler(req))
        assert result2 == {"n": 2}
        assert call_count == 2


class TestCacheKeyByPathAndQuery:
    """3. Different query strings produce separate cache entries."""

    def setup_method(self):
        _clear_all_caches()

    def test_different_queries_are_separate(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return {"q": request.url.query, "n": call_count}

        req_a = _make_request("/items", "page=1")
        req_b = _make_request("/items", "page=2")

        result_a = run(handler(req_a))
        result_b = run(handler(req_b))

        assert result_a["q"] == "page=1"
        assert result_b["q"] == "page=2"
        assert result_a["n"] != result_b["n"]
        assert call_count == 2

    def test_same_path_and_query_hits_cache(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return call_count

        req1 = _make_request("/same", "a=1")
        req2 = _make_request("/same", "a=1")

        run(handler(req1))
        run(handler(req2))
        assert call_count == 1

    def test_different_paths_are_separate(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return call_count

        req_a = _make_request("/path-a", "")
        req_b = _make_request("/path-b", "")

        run(handler(req_a))
        run(handler(req_b))
        assert call_count == 2


class TestCacheClearAll:
    """4. cache_clear() removes all entries across all caches."""

    def setup_method(self):
        _clear_all_caches()

    def test_clear_all(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            return call_count

        req = _make_request("/clear-all")
        run(handler(req))
        assert call_count == 1

        removed = cache_clear()
        assert removed >= 1

        run(handler(req))
        assert call_count == 2  # recomputed after clear


class TestCacheClearPrefix:
    """5. cache_clear(prefix) removes only matching entries."""

    def setup_method(self):
        _clear_all_caches()

    def test_clear_with_prefix(self):
        count_a = 0
        count_b = 0

        @ttl_cache(seconds=60)
        async def handler_a(request):
            nonlocal count_a
            count_a += 1
            return count_a

        @ttl_cache(seconds=60)
        async def handler_b(request):
            nonlocal count_b
            count_b += 1
            return count_b

        req_a = _make_request("/api/alpha")
        req_b = _make_request("/api/beta")

        run(handler_a(req_a))
        run(handler_b(req_b))
        assert count_a == 1
        assert count_b == 1

        # Clear only /api/alpha entries
        removed = cache_clear(prefix="/api/alpha")
        assert removed >= 1

        # handler_a should recompute
        run(handler_a(req_a))
        assert count_a == 2

        # handler_b should still be cached
        run(handler_b(req_b))
        assert count_b == 1

    def test_no_match_returns_zero(self):
        @ttl_cache(seconds=60)
        async def handler(request):
            return 1

        req = _make_request("/data")
        run(handler(req))

        removed = cache_clear(prefix="/nonexistent")
        assert removed == 0


class TestThreadSafety:
    """6. Concurrent access does not crash or corrupt the cache."""

    def setup_method(self):
        _clear_all_caches()

    def test_concurrent_calls(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler(request):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.005)  # simulate brief I/O
            return {"n": call_count}

        req = _make_request("/concurrent")

        async def run_concurrent():
            return await asyncio.gather(*[handler(req) for _ in range(20)])

        results = run(run_concurrent())

        # All results should be dicts with "n" key (no corruption)
        for r in results:
            assert isinstance(r, dict)
            assert "n" in r

        # The function should be called very few times (not 20)
        assert call_count < 20


class TestBypassWithoutRequest:
    """When no request object is available, the cache is bypassed."""

    def setup_method(self):
        _clear_all_caches()

    def test_no_request_bypasses_cache(self):
        call_count = 0

        @ttl_cache(seconds=60)
        async def handler():
            nonlocal call_count
            call_count += 1
            return call_count

        r1 = run(handler())
        r2 = run(handler())
        assert r1 == 1
        assert r2 == 2
        assert call_count == 2


# ---------------------------------------------------------------------------
# Integration tests — cached endpoints via TestClient
# ---------------------------------------------------------------------------


class TestLanguagesEndpointCached:
    """7. GET /languages returns valid JSON and is cacheable."""

    def test_returns_languages(self):
        resp = client.get("/languages")
        assert resp.status_code == 200
        data = resp.json()
        assert "languages" in data
        assert isinstance(data["languages"], dict)
        assert "auto" in data["languages"]
        assert "en" in data["languages"]

    def test_subsequent_call_same_result(self):
        resp1 = client.get("/languages")
        resp2 = client.get("/languages")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json() == resp2.json()


class TestSystemInfoEndpointCached:
    """8. GET /system-info returns valid JSON with expected fields."""

    def test_returns_system_info(self):
        resp = client.get("/system-info")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestHealthEndpointCached:
    """9. GET /health returns cached response within TTL."""

    def test_returns_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "uptime_sec" in data

    def test_cached_within_ttl(self):
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both should have the same uptime (cached within 2s TTL)
        assert r1.json()["uptime_sec"] == r2.json()["uptime_sec"]


class TestCapabilitiesEndpointCached:
    """10. GET /api/capabilities returns cached capabilities."""

    def test_returns_capabilities(self):
        resp = client.get("/api/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert "accepted_extensions" in data
        assert isinstance(data["features"], dict)


class TestModelStatusEndpointCached:
    """11. GET /api/model-status returns model status."""

    def test_returns_model_status(self):
        resp = client.get("/api/model-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "preload" in data
        assert "models" in data

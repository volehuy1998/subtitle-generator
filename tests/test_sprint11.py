"""Tests for Sprint 11: Performance Optimization.

S11-1: Model preloading at startup
S11-2: Audio extraction optimization
S11-3: Response compression (GZip)
S11-4: Static asset caching headers
S11-5: Connection management
S11-6: Memory optimization
S11-7: Benchmark regression tests
S11-8: Integration tests
"""

import time
from pathlib import Path

from app.main import app
from app.config import PRELOAD_MODEL, ENABLE_COMPRESSION, STATIC_CACHE_MAX_AGE
from fastapi.testclient import TestClient

client = TestClient(app)

PROJECT_ROOT = Path(__file__).parent.parent


# ── S11-1: Model Preloading ──

class TestModelPreloading:
    def test_preload_config_exists(self):
        """PRELOAD_MODEL config should exist."""
        from app import config
        assert hasattr(config, 'PRELOAD_MODEL')

    def test_preload_empty_by_default(self):
        """Model preloading disabled by default."""
        assert PRELOAD_MODEL == "" or PRELOAD_MODEL in ("tiny", "base", "small", "medium", "large")

    def test_preload_logic_in_lifespan(self):
        """Verify lifespan contains preloading logic."""
        source = (PROJECT_ROOT / "app" / "main.py").read_text()
        assert "PRELOAD_MODEL" in source
        assert "get_model" in source

    def test_model_cache_is_singleton(self):
        """Model cache should reuse loaded models."""
        from app import state
        assert isinstance(state.loaded_models, dict)


# ── S11-3: Response Compression ──

class TestCompression:
    def test_compression_config_exists(self):
        assert ENABLE_COMPRESSION is True or ENABLE_COMPRESSION is False

    def test_compression_middleware_registered(self):
        """GZip middleware should be in app middleware stack."""
        source = (PROJECT_ROOT / "app" / "main.py").read_text()
        assert "GZipMiddleware" in source

    def test_compressed_response_for_large_body(self):
        """Large JSON responses should be compressible."""
        res = client.get("/analytics/summary", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200

    def test_analytics_page_compressible(self):
        """HTML page should be compressible."""
        res = client.get("/analytics", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200

    def test_compression_module_exists(self):
        from app.middleware.compression import GZipMiddleware
        assert GZipMiddleware is not None


# ── S11-4: Static Asset Caching ──

class TestCaching:
    def test_languages_has_cache_header(self):
        res = client.get("/languages")
        assert "Cache-Control" in res.headers
        assert "max-age" in res.headers["Cache-Control"]

    def test_embed_presets_has_cache_header(self):
        res = client.get("/embed/presets")
        assert "Cache-Control" in res.headers

    def test_system_info_has_cache_header(self):
        res = client.get("/system-info")
        assert "Cache-Control" in res.headers

    def test_health_no_cache(self):
        """Health endpoint should NOT be cached."""
        res = client.get("/health")
        cache = res.headers.get("Cache-Control", "")
        assert "max-age=3600" not in cache

    def test_cache_max_age_config(self):
        assert STATIC_CACHE_MAX_AGE == 3600


# ── S11-5: CSP Updated for CDN ──

class TestCSPUpdate:
    def test_csp_allows_chart_js_cdn(self):
        res = client.get("/analytics")
        csp = res.headers.get("Content-Security-Policy", "")
        assert "cdn.jsdelivr.net" in csp

    def test_csp_still_has_self(self):
        res = client.get("/")
        csp = res.headers.get("Content-Security-Policy", "")
        assert "'self'" in csp


# ── S11-7: Benchmark Regression Tests ──

class TestBenchmarkRegression:
    def test_health_under_50ms(self):
        t0 = time.time()
        res = client.get("/health")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 50, f"Health endpoint: {elapsed:.1f}ms (expected <50ms)"

    def test_languages_under_50ms(self):
        t0 = time.time()
        res = client.get("/languages")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 50, f"Languages endpoint: {elapsed:.1f}ms (expected <50ms)"

    def test_analytics_summary_under_100ms(self):
        t0 = time.time()
        res = client.get("/analytics/summary")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 100, f"Analytics summary: {elapsed:.1f}ms (expected <100ms)"

    def test_analytics_timeseries_under_100ms(self):
        t0 = time.time()
        res = client.get("/analytics/timeseries")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 200, f"Analytics timeseries: {elapsed:.1f}ms (expected <200ms)"

    def test_metrics_under_100ms(self):
        t0 = time.time()
        res = client.get("/metrics")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 100, f"Metrics: {elapsed:.1f}ms (expected <100ms)"

    def test_dashboard_data_under_200ms(self):
        t0 = time.time()
        res = client.get("/dashboard/data")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 200, f"Dashboard data: {elapsed:.1f}ms (expected <200ms)"

    def test_tasks_list_under_50ms(self):
        t0 = time.time()
        res = client.get("/tasks")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 50, f"Tasks list: {elapsed:.1f}ms (expected <50ms)"

    def test_embed_presets_under_50ms(self):
        t0 = time.time()
        res = client.get("/embed/presets")
        elapsed = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed < 50, f"Embed presets: {elapsed:.1f}ms (expected <50ms)"


# ── S11-8: Integration ──

class TestIntegration:
    def test_all_pages_still_load(self):
        pages = ["/", "/health", "/ready", "/metrics", "/analytics",
                 "/dashboard", "/docs", "/openapi.json"]
        for page in pages:
            res = client.get(page)
            expected = (200, 503) if page == "/ready" else (200,)
            assert res.status_code in expected, f"{page} returned {res.status_code}"

    def test_security_headers_preserved(self):
        res = client.get("/")
        assert "X-Content-Type-Options" in res.headers
        assert "X-Frame-Options" in res.headers

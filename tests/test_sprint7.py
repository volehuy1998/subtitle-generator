"""Tests for Sprint 7: Polish & Ship v1.0.

S7-1: User feedback collection
S7-2: API documentation (OpenAPI)
S7-3: User guide (FAQ page placeholder)
S7-4: Release v1.0 with changelog
S7-5: Performance benchmarks
"""

from pathlib import Path

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app, base_url="https://testserver")

PROJECT_ROOT = Path(__file__).parent.parent


# ── S7-1: User Feedback ──


class TestFeedback:
    def test_submit_feedback(self):
        res = client.post("/feedback", json={"rating": 5, "comment": "Great tool!"})
        assert res.status_code == 200
        data = res.json()
        assert data["rating"] == 5
        assert "thank" in data["message"].lower()

    def test_submit_feedback_with_task(self):
        res = client.post("/feedback", json={"task_id": "abc123", "rating": 4})
        assert res.status_code == 200

    def test_submit_feedback_min_rating(self):
        res = client.post("/feedback", json={"rating": 1})
        assert res.status_code == 200

    def test_submit_feedback_invalid_rating_high(self):
        res = client.post("/feedback", json={"rating": 6})
        assert res.status_code == 422

    def test_submit_feedback_invalid_rating_low(self):
        res = client.post("/feedback", json={"rating": 0})
        assert res.status_code == 422

    def test_feedback_summary(self):
        res = client.get("/feedback/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "average_rating" in data
        assert "ratings" in data

    def test_feedback_summary_has_counts(self):
        res = client.get("/feedback/summary")
        data = res.json()
        for i in range(1, 6):
            assert str(i) in data["ratings"] or i in data["ratings"]


# ── S7-2: API Documentation ──


class TestApiDocs:
    def test_openapi_schema_available(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Subtitle Generator"

    def test_openapi_version(self):
        res = client.get("/openapi.json")
        data = res.json()
        assert data["info"]["version"] == "2.0.0"

    def test_openapi_description(self):
        res = client.get("/openapi.json")
        data = res.json()
        assert "faster-whisper" in data["info"]["description"]

    def test_docs_page_available(self):
        res = client.get("/docs")
        assert res.status_code == 200

    def test_redoc_page_available(self):
        res = client.get("/redoc")
        assert res.status_code == 200

    def test_openapi_has_endpoints(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        assert "/upload" in paths
        assert "/health" in paths
        assert "/metrics" in paths
        assert "/feedback" in paths
        assert "/dashboard" in paths


# ── S7-4: Release v1.0 ──


class TestRelease:
    def test_changelog_exists(self):
        assert (PROJECT_ROOT / "CHANGELOG.md").exists()

    def test_changelog_has_version(self):
        content = (PROJECT_ROOT / "CHANGELOG.md").read_text()
        assert "1.0.0" in content

    def test_changelog_has_sections(self):
        content = (PROJECT_ROOT / "CHANGELOG.md").read_text()
        # Keep a Changelog format uses ### Added, ### Security, etc.
        assert "### Added" in content
        assert "### Security" in content

    def test_roadmap_exists(self):
        assert (PROJECT_ROOT / "ROADMAP.md").exists()

    def test_architecture_exists(self):
        assert (PROJECT_ROOT / "ARCHITECTURE.md").exists()


# ── S7-5: Performance Benchmarks ──


class TestBenchmarks:
    def test_benchmark_script_exists(self):
        assert (PROJECT_ROOT / "benchmark.py").exists()

    def test_loadtest_script_exists(self):
        assert (PROJECT_ROOT / "loadtest.py").exists()

    def test_health_endpoint_fast(self):
        """Health endpoint should respond in under 100ms."""
        import time

        t0 = time.time()
        res = client.get("/health")
        elapsed_ms = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed_ms < 100, f"Health endpoint too slow: {elapsed_ms:.1f}ms"

    def test_metrics_endpoint_fast(self):
        """Metrics endpoint should respond in under 200ms."""
        import time

        t0 = time.time()
        res = client.get("/metrics")
        elapsed_ms = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed_ms < 200, f"Metrics endpoint too slow: {elapsed_ms:.1f}ms"

    def test_system_info_fast(self):
        """System info should respond in under 500ms."""
        import time

        t0 = time.time()
        res = client.get("/system-info")
        elapsed_ms = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed_ms < 500, f"System info too slow: {elapsed_ms:.1f}ms"


# ── Full API Surface Verification ──


class TestApiSurface:
    """Verify all major endpoints are accessible."""

    def test_root(self):
        res = client.get("/")
        assert res.status_code == 200

    def test_health(self):
        assert client.get("/health").status_code == 200

    def test_ready(self):
        assert client.get("/ready").status_code in (200, 503)

    def test_metrics(self):
        assert client.get("/metrics").status_code == 200

    def test_system_info(self):
        assert client.get("/system-info").status_code == 200

    def test_languages(self):
        res = client.get("/languages")
        assert res.status_code == 200
        assert len(res.json()["languages"]) >= 99

    def test_tasks(self):
        assert client.get("/tasks").status_code == 200

    def test_dashboard(self):
        assert client.get("/dashboard").status_code == 200

    def test_dashboard_data(self):
        assert client.get("/dashboard/data").status_code == 200

    def test_embed_presets(self):
        assert client.get("/embed/presets").status_code == 200

    def test_feedback_summary(self):
        assert client.get("/feedback/summary").status_code == 200

    def test_docs(self):
        assert client.get("/docs").status_code == 200

    def test_openapi(self):
        assert client.get("/openapi.json").status_code == 200

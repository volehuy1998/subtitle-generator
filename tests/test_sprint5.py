"""Tests for Sprint 5: Production Deployment features.

S5-1: Dockerfile + docker-compose (file existence tests)
S5-2: CI/CD pipeline (file existence tests)
S5-3: API key authentication
S5-4: Rate limiting (existing slowapi - verify still works)
S5-5: Prometheus /metrics endpoint
S5-6: Graceful shutdown with in-flight task draining
S5-7: Load testing (script existence)
"""

import os
from pathlib import Path
from unittest.mock import patch

from app.main import app
from app import state
from app.middleware.auth import (
    is_auth_enabled, validate_api_key,
    PUBLIC_PATHS,
)
from fastapi.testclient import TestClient

client = TestClient(app)

PROJECT_ROOT = Path(__file__).parent.parent


# ── S5-1: Docker Files ──

class TestDockerFiles:
    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_dockerfile_gpu_exists(self):
        assert (PROJECT_ROOT / "Dockerfile.gpu").exists()

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_dockerignore_exists(self):
        assert (PROJECT_ROOT / ".dockerignore").exists()

    def test_dockerfile_has_healthcheck(self):
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "HEALTHCHECK" in content

    def test_dockerfile_non_root_user(self):
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "USER appuser" in content

    def test_dockerfile_gpu_nvidia_env(self):
        content = (PROJECT_ROOT / "Dockerfile.gpu").read_text()
        assert "NVIDIA_VISIBLE_DEVICES" in content

    def test_docker_compose_gpu_profile(self):
        content = (PROJECT_ROOT / "docker-compose.yml").read_text()
        assert "gpu" in content
        assert "nvidia" in content


# ── S5-2: CI/CD Pipeline ──

class TestCICD:
    def test_ci_workflow_exists(self):
        assert (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").exists()

    def test_ci_has_lint_step(self):
        content = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert "lint" in content.lower() or "ruff" in content

    def test_ci_has_test_step(self):
        content = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert "pytest" in content

    def test_ci_has_build_step(self):
        content = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert "docker build" in content or "Build" in content


# ── S5-3: API Key Authentication ──

class TestApiKeyAuth:
    def setup_method(self):
        """Reset cached keys before each test."""
        import app.middleware.auth as auth_mod
        auth_mod._api_keys = None

    def test_auth_disabled_by_default(self):
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            import app.middleware.auth as auth_mod
            auth_mod._api_keys = None
            assert not is_auth_enabled()

    def test_auth_enabled_with_keys(self):
        with patch.dict(os.environ, {"API_KEYS": "key1,key2"}, clear=False):
            import app.middleware.auth as auth_mod
            auth_mod._api_keys = None
            assert is_auth_enabled()

    def test_validate_correct_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}, clear=False):
            import app.middleware.auth as auth_mod
            auth_mod._api_keys = None
            assert validate_api_key("test-key-123")

    def test_validate_wrong_key(self):
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}, clear=False):
            import app.middleware.auth as auth_mod
            auth_mod._api_keys = None
            assert not validate_api_key("wrong-key")

    def test_validate_when_disabled(self):
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=False):
            import app.middleware.auth as auth_mod
            auth_mod._api_keys = None
            assert validate_api_key("any-key")

    def test_public_paths_defined(self):
        assert "/" in PUBLIC_PATHS
        assert "/health" in PUBLIC_PATHS
        assert "/ready" in PUBLIC_PATHS
        assert "/metrics" in PUBLIC_PATHS

    def test_health_accessible_without_key(self):
        """Health endpoint should always be accessible."""
        res = client.get("/health")
        assert res.status_code == 200

    def test_metrics_accessible_without_key(self):
        """Metrics endpoint should always be accessible."""
        res = client.get("/metrics")
        assert res.status_code == 200


# ── S5-5: Prometheus Metrics ──

class TestPrometheusMetrics:
    def test_metrics_endpoint_returns_200(self):
        res = client.get("/metrics")
        assert res.status_code == 200

    def test_metrics_content_type(self):
        res = client.get("/metrics")
        assert "text/plain" in res.headers["content-type"]

    def test_metrics_has_uptime(self):
        res = client.get("/metrics")
        assert "subtitle_generator_uptime_seconds" in res.text

    def test_metrics_has_tasks(self):
        res = client.get("/metrics")
        assert "subtitle_generator_tasks_created_total" in res.text

    def test_metrics_has_active_tasks(self):
        res = client.get("/metrics")
        assert "subtitle_generator_active_tasks" in res.text

    def test_metrics_has_files_count(self):
        res = client.get("/metrics")
        assert "subtitle_generator_files_count" in res.text

    def test_metrics_has_cpu(self):
        res = client.get("/metrics")
        assert "subtitle_generator_cpu_percent" in res.text

    def test_metrics_has_memory(self):
        res = client.get("/metrics")
        assert "subtitle_generator_memory_used_bytes" in res.text

    def test_metrics_prometheus_format(self):
        """Verify output follows Prometheus text exposition format."""
        res = client.get("/metrics")
        lines = res.text.strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                assert line.startswith("# HELP") or line.startswith("# TYPE")
            else:
                # Metric line: name{labels} value
                parts = line.split(" ")
                assert len(parts) >= 2, f"Invalid metric line: {line}"


# ── S5-6: Graceful Shutdown ──

class TestGracefulShutdown:
    def test_shutting_down_flag(self):
        assert state.shutting_down is False

    def test_drain_tasks_empty(self):
        """Drain should return True immediately when no active tasks."""
        assert state.drain_tasks(timeout=1.0) is True

    def test_get_active_task_count_empty(self):
        assert state.get_active_task_count() == 0

    def test_get_active_task_count_with_tasks(self):
        original = state.tasks.copy()
        state.tasks["test-active-1"] = {"status": "transcribing"}
        state.tasks["test-active-2"] = {"status": "done"}
        state.tasks["test-active-3"] = {"status": "extracting"}
        try:
            assert state.get_active_task_count() == 2
        finally:
            state.tasks.clear()
            state.tasks.update(original)


# ── S5-7: Load Testing ──

class TestLoadTesting:
    def test_loadtest_script_exists(self):
        assert (PROJECT_ROOT / "loadtest.py").exists()

    def test_loadtest_has_main(self):
        content = (PROJECT_ROOT / "loadtest.py").read_text()
        assert "def main()" in content
        assert "argparse" in content

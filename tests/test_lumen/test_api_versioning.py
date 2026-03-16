"""Phase Lumen L29-L32 — API versioning, OpenAPI organization, and consistency tests.

Validates that API version headers are present on all responses, OpenAPI spec
is well-organized with tags, and endpoints behave consistently.
— Scout (QA Lead)
"""

import re
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# VERSION HEADER TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestVersionHeader:
    """X-API-Version header is present on all responses with correct format."""

    def test_version_header_present_on_health(self):
        """X-API-Version header present on GET /health."""
        res = client.get("/health")
        assert "x-api-version" in res.headers, "X-API-Version header missing on GET /health"

    def test_version_header_present_on_tasks(self):
        """X-API-Version header present on GET /tasks."""
        res = client.get("/tasks")
        assert "x-api-version" in res.headers, "X-API-Version header missing on GET /tasks"

    def test_version_header_matches_app_version(self):
        """X-API-Version value matches the FastAPI app version."""
        res = client.get("/health")
        assert res.headers["x-api-version"] == app.version

    def test_version_header_is_semver(self):
        """X-API-Version value follows semver format (x.y.z)."""
        res = client.get("/health")
        version = res.headers["x-api-version"]
        assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version '{version}' is not valid semver"

    def test_version_header_on_404_error(self):
        """X-API-Version header present even on 404 error responses."""
        res = client.get("/nonexistent-endpoint-xyz")
        assert res.status_code == 404
        assert "x-api-version" in res.headers, "X-API-Version missing on 404 response"

    def test_version_header_on_post_upload(self):
        """X-API-Version header present on POST /upload (validation error)."""
        res = client.post("/upload")
        assert "x-api-version" in res.headers, "X-API-Version missing on POST endpoint"

    def test_version_header_on_metrics(self):
        """X-API-Version header present on GET /metrics."""
        res = client.get("/metrics")
        assert "x-api-version" in res.headers

    def test_version_header_on_system_info(self):
        """X-API-Version header present on GET /system-info."""
        res = client.get("/system-info")
        assert "x-api-version" in res.headers

    def test_version_header_on_delete_endpoint(self):
        """X-API-Version header present on DELETE response."""
        res = client.delete("/tasks/nonexistent-id")
        assert "x-api-version" in res.headers

    def test_version_header_on_cancel_endpoint(self):
        """X-API-Version header present on POST /cancel response."""
        res = client.post("/cancel/nonexistent-id")
        assert "x-api-version" in res.headers


# ══════════════════════════════════════════════════════════════════════════════
# OPENAPI ORGANIZATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestOpenAPIOrganization:
    """OpenAPI specification is well-organized with proper tagging."""

    @pytest.fixture(autouse=True)
    def _load_openapi(self):
        """Load OpenAPI spec once for all tests in this class."""
        res = client.get("/openapi.json")
        assert res.status_code == 200
        self.spec = res.json()

    def test_openapi_has_tags_list(self):
        """OpenAPI spec contains a top-level tags list."""
        assert "tags" in self.spec, "OpenAPI spec missing 'tags' list"
        assert isinstance(self.spec["tags"], list)
        assert len(self.spec["tags"]) > 0, "Tags list should not be empty"

    def test_tags_include_upload(self):
        """Tags include Upload."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        assert "Upload" in tag_names, "Missing 'Upload' tag"

    def test_tags_include_tasks(self):
        """Tags include Tasks."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        assert "Tasks" in tag_names, "Missing 'Tasks' tag"

    def test_tags_include_download(self):
        """Tags include Download."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        assert "Download" in tag_names, "Missing 'Download' tag"

    def test_tags_include_system(self):
        """Tags include a system/health-related tag."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        has_system = "System" in tag_names or "Health" in tag_names
        assert has_system, "Missing system/health tag"

    def test_tags_include_progress(self):
        """Tags include Progress (events/SSE)."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        has_events = "Progress" in tag_names or "Events" in tag_names
        assert has_events, "Missing progress/events tag"

    def test_tags_include_admin_or_control(self):
        """Tags include Admin or Control functionality."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        has_control = "Admin" in tag_names or "Control" in tag_names or "Auth" in tag_names
        assert has_control, "Missing admin/control tag"

    def test_each_tag_has_name_and_description(self):
        """Every tag entry has both 'name' and 'description' fields."""
        for tag in self.spec["tags"]:
            assert "name" in tag, f"Tag missing 'name': {tag}"
            assert "description" in tag, f"Tag '{tag.get('name')}' missing 'description'"
            assert len(tag["description"]) > 0, f"Tag '{tag['name']}' has empty description"

    def test_no_duplicate_tag_names(self):
        """No duplicate tag names in the tags list."""
        tag_names = [t["name"] for t in self.spec["tags"]]
        duplicates = [n for n in tag_names if tag_names.count(n) > 1]
        assert len(duplicates) == 0, f"Duplicate tag names found: {set(duplicates)}"

    def test_tagged_endpoints_outnumber_untagged(self):
        """The majority of API paths have at least one tag assigned."""
        paths = self.spec.get("paths", {})
        tagged = 0
        total = 0
        for path, methods in paths.items():
            for method, spec in methods.items():
                if isinstance(spec, dict):
                    total += 1
                    if spec.get("tags"):
                        tagged += 1
        assert tagged > total * 0.5, f"Only {tagged}/{total} endpoints have tags — majority should be tagged"


# ══════════════════════════════════════════════════════════════════════════════
# API CONSISTENCY TESTS
# ══════════════════════════════════════════════════════════════════════════════

FAST_ENDPOINTS = [
    "/health",
    "/health/live",
    "/ready",
    "/tasks",
    "/metrics",
    "/system-info",
    "/languages",
    "/embed/presets",
]


class TestAPIConsistency:
    """API endpoints behave consistently and gracefully."""

    @pytest.mark.parametrize("path", FAST_ENDPOINTS)
    def test_endpoint_returns_within_timeout(self, path):
        """All GET endpoints respond within 5 seconds."""
        start = time.monotonic()
        res = client.get(path)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"{path} took {elapsed:.2f}s — exceeds 5s timeout"
        assert res.status_code == 200

    def test_get_health_is_idempotent(self):
        """GET /health returns same structure on consecutive calls."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.status_code == r2.status_code
        d1, d2 = r1.json(), r2.json()
        assert d1.keys() == d2.keys(), "Health response structure changed between calls"
        assert d1["status"] == d2["status"]

    def test_get_tasks_is_idempotent(self):
        """GET /tasks returns same data on consecutive calls (no side effects)."""
        r1 = client.get("/tasks")
        r2 = client.get("/tasks")
        assert r1.status_code == r2.status_code
        assert r1.json() == r2.json(), "Task list changed between identical requests"

    def test_post_upload_without_body_returns_422(self):
        """POST /upload without file returns 422 (validation error), not 500."""
        res = client.post("/upload")
        assert res.status_code == 422, f"Expected 422, got {res.status_code}"

    def test_delete_nonexistent_task_returns_404(self):
        """DELETE /tasks/{nonexistent} returns 404, not 500."""
        res = client.delete("/tasks/nonexistent-task-id-abc123")
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"

    def test_accept_json_on_health(self):
        """Content negotiation: Accept: application/json returns JSON response."""
        res = client.get("/health", headers={"Accept": "application/json"})
        assert res.status_code == 200
        ct = res.headers.get("content-type", "")
        assert "application/json" in ct

    def test_utf8_encoding_on_json_responses(self):
        """JSON responses use UTF-8 encoding."""
        res = client.get("/tasks")
        assert res.encoding == "utf-8" or "utf-8" in res.headers.get("content-type", "").lower() or res.encoding is None
        # Verify content is valid UTF-8
        res.content.decode("utf-8")

    def test_no_server_error_on_health(self):
        """GET /health never returns 5xx."""
        res = client.get("/health")
        assert res.status_code < 500, f"/health returned server error {res.status_code}"

    def test_no_server_error_on_tasks(self):
        """GET /tasks never returns 5xx."""
        res = client.get("/tasks")
        assert res.status_code < 500, f"/tasks returned server error {res.status_code}"

    def test_no_server_error_on_languages(self):
        """GET /languages never returns 5xx."""
        res = client.get("/languages")
        assert res.status_code < 500, f"/languages returned server error {res.status_code}"

    def test_response_size_reasonable_for_tasks(self):
        """GET /tasks response is under 1MB (no unbounded data)."""
        res = client.get("/tasks")
        assert len(res.content) < 1_000_000, f"/tasks response is {len(res.content)} bytes — too large"

    def test_response_size_reasonable_for_health(self):
        """GET /health response is under 1MB."""
        res = client.get("/health")
        assert len(res.content) < 1_000_000, f"/health response is {len(res.content)} bytes — too large"

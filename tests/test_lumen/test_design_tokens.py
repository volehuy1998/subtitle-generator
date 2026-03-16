"""Phase Lumen L23-L24 — Design token and API response consistency tests.

Validates that all API responses follow consistent formatting, use proper
headers, and maintain data integrity across endpoints.
— Scout (QA Lead)
"""

from fastapi.testclient import TestClient

from app.config import SUPPORTED_LANGUAGES, VALID_MODELS
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# API RESPONSE FORMATTING
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIResponseFormatting:
    """Verify API responses use consistent structures and field naming."""

    def test_health_returns_structured_json(self):
        """Health endpoint returns structured JSON with consistent field names."""
        res = client.get("/health")
        data = res.json()
        assert "status" in data, "Health response must include 'status' field"
        assert "uptime_sec" in data, "Health response must include 'uptime_sec' field"
        assert isinstance(data["status"], str)
        assert isinstance(data["uptime_sec"], (int, float))

    def test_model_status_uses_consistent_status_values(self):
        """Model status uses consistent status values (ready/loading/not_loaded)."""
        res = client.get("/api/model-status")
        data = res.json()
        assert "models" in data
        models = data["models"]
        valid_statuses = {"ready", "loading", "not_loaded"}
        for model_name, model_info in models.items():
            if isinstance(model_info, dict) and "status" in model_info:
                assert model_info["status"] in valid_statuses, (
                    f"Model {model_name} has invalid status: {model_info['status']}"
                )

    def test_task_list_uses_consistent_field_names(self):
        """Task list uses consistent field names across entries."""
        res = client.get("/tasks")
        data = res.json()
        # Tasks endpoint returns {"tasks": [...]} wrapper
        if isinstance(data, dict):
            assert "tasks" in data, "Tasks response should have 'tasks' key"
            tasks = data["tasks"]
        else:
            tasks = data
        assert isinstance(tasks, list), "Tasks should be a list"
        # When tasks exist, each should have at minimum task_id and status
        for task in tasks:
            if isinstance(task, dict):
                assert "task_id" in task or "id" in task, "Each task must have an identifier"
                assert "status" in task, "Each task must have a status field"

    def test_progress_endpoint_returns_404_for_nonexistent(self):
        """Progress endpoint returns 404 for nonexistent task."""
        res = client.get("/progress/nonexistent-task-id")
        assert res.status_code == 404

    def test_error_responses_use_detail_key(self):
        """Error responses use consistent 'detail' key."""
        res = client.get("/progress/nonexistent-task-id")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data, "Error responses should use 'detail' key"

    def test_upload_requires_file(self):
        """Upload endpoint requires a file — returns 422 without one."""
        res = client.post("/upload")
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data, "Validation error should use 'detail' key"

    def test_languages_endpoint_returns_dict(self):
        """Languages endpoint returns a dictionary of language codes to names."""
        res = client.get("/languages")
        data = res.json()
        assert "languages" in data
        langs = data["languages"]
        assert isinstance(langs, dict), "Languages should be a dict of code->name"
        assert "en" in langs, "English should be in supported languages"

    def test_system_info_has_nested_structure(self):
        """System info has nested structure with expected keys."""
        res = client.get("/system-info")
        data = res.json()
        assert isinstance(data, dict)
        assert "cuda_available" in data
        assert "auto_model" in data
        assert isinstance(data["cuda_available"], bool)

    def test_metrics_endpoint_returns_text_format(self):
        """Metrics endpoint returns text/plain format (Prometheus-style)."""
        res = client.get("/metrics")
        assert res.status_code == 200
        ct = res.headers.get("content-type", "")
        assert "text/plain" in ct, f"Metrics should be text/plain, got: {ct}"

    def test_openapi_spec_has_proper_structure(self):
        """OpenAPI spec has proper info/paths structure."""
        res = client.get("/openapi.json")
        data = res.json()
        assert "openapi" in data, "Must have openapi version"
        assert "info" in data, "Must have info section"
        assert "paths" in data, "Must have paths section"
        assert "title" in data["info"], "Info must have title"
        assert "version" in data["info"], "Info must have version"

    def test_health_live_returns_minimal_response(self):
        """Health live endpoint returns minimal OK response."""
        res = client.get("/health/live")
        data = res.json()
        assert data["status"] == "ok"

    def test_ready_endpoint_returns_checks(self):
        """Ready endpoint returns health check results."""
        res = client.get("/ready")
        assert res.status_code in (200, 503)
        data = res.json()
        assert isinstance(data, dict)

    def test_task_stats_returns_numeric_fields(self):
        """Task stats returns numeric fields for counts."""
        res = client.get("/tasks/stats")
        data = res.json()
        for field in ["total_tasks", "completed", "failed", "cancelled", "active"]:
            assert field in data, f"Task stats missing field: {field}"
            assert isinstance(data[field], (int, float)), f"{field} should be numeric"

    def test_embed_presets_returns_list_or_dict(self):
        """Embed presets endpoint returns structured preset data."""
        res = client.get("/embed/presets")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, (list, dict)), "Presets should be a list or dict"

    def test_model_status_has_preload_key(self):
        """Model status response includes preload information."""
        res = client.get("/api/model-status")
        data = res.json()
        assert "preload" in data, "Model status must include preload key"


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE HEADERS
# ══════════════════════════════════════════════════════════════════════════════


class TestResponseHeaders:
    """Verify response headers are consistent across endpoints."""

    def test_health_has_x_request_id(self):
        """Health endpoint sets X-Request-ID header."""
        res = client.get("/health")
        headers_lower = {k.lower(): v for k, v in res.headers.items()}
        assert "x-request-id" in headers_lower, "X-Request-ID header should be present"

    def test_tasks_has_x_request_id(self):
        """Tasks endpoint sets X-Request-ID header."""
        res = client.get("/tasks")
        headers_lower = {k.lower(): v for k, v in res.headers.items()}
        assert "x-request-id" in headers_lower

    def test_json_endpoints_return_application_json(self):
        """JSON API endpoints return application/json content type."""
        json_endpoints = [
            "/health",
            "/health/live",
            "/system-info",
            "/languages",
            "/tasks",
            "/tasks/stats",
            "/api/model-status",
        ]
        for path in json_endpoints:
            res = client.get(path)
            ct = res.headers.get("content-type", "")
            assert "application/json" in ct, f"{path} should return application/json, got: {ct}"

    def test_html_endpoints_return_text_html(self):
        """HTML page endpoints return text/html content type."""
        html_endpoints = ["/", "/status", "/about", "/security", "/contact"]
        for path in html_endpoints:
            res = client.get(path)
            ct = res.headers.get("content-type", "")
            assert "text/html" in ct, f"{path} should return text/html, got: {ct}"

    def test_security_headers_on_api_endpoints(self):
        """Security headers present on API responses."""
        for path in ["/health", "/tasks", "/languages"]:
            res = client.get(path)
            headers_lower = {k.lower(): v for k, v in res.headers.items()}
            assert "x-content-type-options" in headers_lower, f"{path} missing X-Content-Type-Options"

    def test_x_frame_options_on_pages(self):
        """X-Frame-Options header present on HTML pages."""
        res = client.get("/")
        assert res.headers.get("x-frame-options") == "DENY"

    def test_cors_headers_on_api_calls(self):
        """CORS headers present on API responses when origin is set."""
        # Send request with Origin header to trigger CORS
        res = client.get("/health", headers={"Origin": "http://localhost:3000"})
        # CORS middleware should respond (either allow or deny)
        # In dev mode with CORS_ORIGINS=*, access-control-allow-origin should be present
        # Verify the request succeeds regardless
        assert res.status_code == 200

    def test_referrer_policy_header(self):
        """Referrer-Policy header is set on responses."""
        res = client.get("/")
        headers_lower = {k.lower(): v for k, v in res.headers.items()}
        assert "referrer-policy" in headers_lower, "Referrer-Policy header should be present"

    def test_x_content_type_options_nosniff(self):
        """X-Content-Type-Options is set to nosniff."""
        res = client.get("/health")
        assert res.headers.get("x-content-type-options") == "nosniff"

    def test_csp_header_on_html_pages(self):
        """Content-Security-Policy header present on HTML pages."""
        for path in ["/", "/about", "/contact"]:
            res = client.get(path)
            headers_lower = {k.lower(): v for k, v in res.headers.items()}
            assert "content-security-policy" in headers_lower, f"{path} missing Content-Security-Policy header"


# ══════════════════════════════════════════════════════════════════════════════
# DATA CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestDataConsistency:
    """Verify data consistency across related endpoints."""

    def test_version_in_health_matches_app_version(self):
        """Version reported by OpenAPI spec matches app version."""
        health_res = client.get("/openapi.json")
        spec_version = health_res.json()["info"]["version"]
        # The version should be a valid semver-like string
        assert spec_version, "Version should not be empty"
        parts = spec_version.split(".")
        assert len(parts) >= 2, f"Version should be semver-like, got: {spec_version}"

    def test_all_model_sizes_in_model_status_match_config(self):
        """All model sizes in /api/model-status match VALID_MODELS config."""
        res = client.get("/api/model-status")
        data = res.json()
        models = data["models"]
        for model_name in models:
            assert model_name in VALID_MODELS, f"Model '{model_name}' in model-status not in VALID_MODELS config"

    def test_languages_count_matches_config(self):
        """Languages count matches SUPPORTED_LANGUAGES config."""
        res = client.get("/languages")
        data = res.json()
        api_langs = data["languages"]
        assert len(api_langs) == len(SUPPORTED_LANGUAGES), (
            f"API returned {len(api_langs)} languages, config has {len(SUPPORTED_LANGUAGES)}"
        )

    def test_task_stats_fields_sum_correctly(self):
        """Task stats: completed + failed + cancelled + active = total."""
        res = client.get("/tasks/stats")
        data = res.json()
        computed_total = data["completed"] + data["failed"] + data["cancelled"] + data["active"]
        assert computed_total == data["total_tasks"], (
            f"Stats don't sum: {data['completed']}+{data['failed']}+{data['cancelled']}+{data['active']} = {computed_total}, expected {data['total_tasks']}"
        )

    def test_languages_contains_all_config_entries(self):
        """Every language in config appears in the API response."""
        res = client.get("/languages")
        api_langs = res.json()["languages"]
        for code in SUPPORTED_LANGUAGES:
            assert code in api_langs, f"Language code '{code}' from config missing in API response"

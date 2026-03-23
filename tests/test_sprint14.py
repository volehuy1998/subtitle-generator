"""Tests for Sprint 14: API v2 & Swagger UI Enhancement.

S14-1: OpenAPI tags on all routes
S14-2: Enhanced Swagger UI config
S14-3: Rich API description with markdown
S14-4: Webhook callbacks
S14-5: API version bump
S14-6: OpenAPI tag groups
S14-7: Integration tests
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app import state
from app.main import app
from app.routes.webhooks import _webhooks

client = TestClient(app, base_url="https://testserver")

PROJECT_ROOT = Path(__file__).parent.parent


def _cleanup():
    _webhooks.clear()
    for tid in ["wh-task-1", "wh-task-done"]:
        state.tasks.pop(tid, None)


# ── S14-1: OpenAPI Tags ──


class TestOpenAPITags:
    def test_openapi_has_tags(self):
        res = client.get("/openapi.json")
        data = res.json()
        assert "tags" in data
        tag_names = [t["name"] for t in data["tags"]]
        assert "Upload" in tag_names
        assert "Analytics" in tag_names
        assert "System" in tag_names

    def test_upload_endpoint_tagged(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        upload_tags = paths.get("/upload", {}).get("post", {}).get("tags", [])
        assert "Upload" in upload_tags

    def test_health_endpoint_tagged(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        health_tags = paths.get("/health", {}).get("get", {}).get("tags", [])
        assert "System" in health_tags

    def test_analytics_endpoint_tagged(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        analytics_tags = paths.get("/analytics/summary", {}).get("get", {}).get("tags", [])
        assert "Analytics" in analytics_tags

    def test_tasks_endpoint_tagged(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        tasks_tags = paths.get("/tasks", {}).get("get", {}).get("tags", [])
        assert "Tasks" in tasks_tags


# ── S14-2: Enhanced Swagger UI ──


class TestSwaggerUI:
    def test_docs_page_available(self):
        res = client.get("/docs")
        assert res.status_code == 200

    def test_redoc_page_available(self):
        res = client.get("/redoc")
        assert res.status_code == 200

    def test_swagger_has_try_it_out(self):
        """Swagger UI should have tryItOut enabled."""
        # This is configured in FastAPI constructor
        source = (PROJECT_ROOT / "app" / "main.py").read_text()
        assert "tryItOutEnabled" in source

    def test_swagger_has_filter(self):
        source = (PROJECT_ROOT / "app" / "main.py").read_text()
        assert '"filter": True' in source


# ── S14-3: Rich API Description ──


class TestAPIDescription:
    def test_openapi_has_rich_description(self):
        res = client.get("/openapi.json")
        desc = res.json()["info"]["description"]
        assert "99 languages" in desc
        assert "Word-level timestamps" in desc

    def test_openapi_has_features_section(self):
        res = client.get("/openapi.json")
        desc = res.json()["info"]["description"]
        assert "Features" in desc

    def test_openapi_has_auth_info(self):
        res = client.get("/openapi.json")
        desc = res.json()["info"]["description"]
        assert "Authentication" in desc
        assert "X-API-Key" in desc


# ── S14-4: Webhook Callbacks ──


class TestWebhooks:
    def setup_method(self):
        _cleanup()
        state.tasks["wh-task-1"] = {"status": "transcribing", "percent": 50, "filename": "test.mp4"}
        state.tasks["wh-task-done"] = {"status": "done", "percent": 100, "filename": "done.mp4"}

    def teardown_method(self):
        _cleanup()

    def test_register_webhook(self):
        res = client.post(
            "/webhooks/register",
            json={
                "task_id": "wh-task-1",
                "url": "https://example.com/callback",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["task_id"] == "wh-task-1"

    def test_register_webhook_unknown_task(self):
        res = client.post(
            "/webhooks/register",
            json={
                "task_id": "nonexistent",
                "url": "https://example.com/callback",
            },
        )
        assert res.status_code == 404

    def test_register_webhook_completed_task(self):
        res = client.post(
            "/webhooks/register",
            json={
                "task_id": "wh-task-done",
                "url": "https://example.com/callback",
            },
        )
        assert res.status_code == 400

    def test_get_webhook(self):
        _webhooks["wh-task-1"] = "https://example.com/cb"
        res = client.get("/webhooks/wh-task-1")
        assert res.status_code == 200
        assert res.json()["url"] == "https://example.com/cb"

    def test_get_webhook_not_found(self):
        res = client.get("/webhooks/nonexistent")
        assert res.status_code == 404

    def test_delete_webhook(self):
        _webhooks["wh-task-1"] = "https://example.com/cb"
        res = client.delete("/webhooks/wh-task-1")
        assert res.status_code == 200
        assert "wh-task-1" not in _webhooks

    def test_webhook_module_has_fire_function(self):
        from app.routes.webhooks import fire_webhook

        assert callable(fire_webhook)

    def test_webhook_pending_list(self):
        from app.routes.webhooks import get_pending_webhooks

        _webhooks["wh-task-1"] = "https://example.com/cb"
        pending = get_pending_webhooks()
        assert "wh-task-1" in pending


# ── S14-6: Tag Descriptions ──


class TestTagDescriptions:
    def test_tags_have_descriptions(self):
        res = client.get("/openapi.json")
        tags = res.json()["tags"]
        for tag in tags:
            assert "description" in tag, f"Tag '{tag['name']}' missing description"

    def test_tag_count(self):
        res = client.get("/openapi.json")
        tags = res.json()["tags"]
        assert len(tags) >= 8  # At least 8 tag groups


# ── S14-7: Integration ──


class TestIntegration:
    def test_openapi_json_valid(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "openapi" in data
        assert "paths" in data
        assert len(data["paths"]) >= 15  # Many endpoints

    def test_all_key_endpoints_in_openapi(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        required = ["/upload", "/health", "/ready", "/metrics", "/analytics/summary", "/tasks", "/feedback"]
        for ep in required:
            assert ep in paths, f"{ep} not in OpenAPI paths"

    def test_webhook_endpoints_in_openapi(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        assert "/webhooks/register" in paths

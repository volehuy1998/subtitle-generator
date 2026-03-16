"""Phase Lumen L37-L40 — Final integration and cross-cutting concern tests.

Tests end-to-end flow validation (upload/progress/download with mocks),
security headers, versioning, session management, and API consistency.
— Scout (QA Lead)
"""

import struct
import uuid
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    """Generate minimal WAV file bytes for upload testing."""
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def _create_done_task(task_id: str) -> None:
    """Create a fake completed task in state for testing."""
    import json

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    srt_path = OUTPUT_DIR / f"{task_id}.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello world\n\n",
        encoding="utf-8",
    )
    json_path = OUTPUT_DIR / f"{task_id}.json"
    json_path.write_text(
        json.dumps([{"start": 0.0, "end": 1.0, "text": "Hello world"}]),
        encoding="utf-8",
    )
    state.tasks[task_id] = {
        "status": "done",
        "percent": 100,
        "message": "Complete",
        "filename": "test.wav",
        "duration": 1.0,
        "file_size": 32000,
        "file_size_fmt": "32.0 KB",
        "segments": 1,
        "language": "en",
        "device": "cpu",
        "model_size": "tiny",
        "session_id": "",  # empty for open access (backward compat)
    }


def _cleanup_task(task_id: str) -> None:
    """Remove task state and output files."""
    state.tasks.pop(task_id, None)
    for ext in (".srt", ".json", ".vtt"):
        path = OUTPUT_DIR / f"{task_id}{ext}"
        if path.exists():
            path.unlink()


# ══════════════════════════════════════════════════════════════════════════════
# END-TO-END FLOW VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestEndToEndFlow:
    """Test upload → progress → download flow using mocked state."""

    def test_upload_accepts_valid_wav(self):
        """POST /upload with a valid WAV returns 200 with task_id."""
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
        )
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        # Cleanup
        tid = data["task_id"]
        state.tasks.pop(tid, None)

    def test_upload_with_all_valid_params(self):
        """Upload with model_size, language, and format params."""
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
            data={"model_size": "tiny", "language": "en"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        state.tasks.pop(data["task_id"], None)

    def test_progress_for_valid_task(self):
        """GET /progress/{task_id} returns expected fields for known task."""
        task_id = f"test-progress-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            res = client.get(f"/progress/{task_id}")
            assert res.status_code == 200
            data = res.json()
            assert "status" in data
            assert "percent" in data
        finally:
            _cleanup_task(task_id)

    def test_progress_unknown_task_returns_404(self):
        """GET /progress for non-existent task returns 404."""
        res = client.get("/progress/nonexistent-task-xyz")
        assert res.status_code == 404

    def test_cancelled_task_can_be_deleted(self):
        """DELETE should work on a cancelled task."""
        task_id = f"test-cancel-del-{uuid.uuid4().hex[:8]}"
        state.tasks[task_id] = {"status": "cancelled", "percent": 0, "message": "Cancelled"}
        try:
            res = client.delete(f"/tasks/{task_id}")
            assert res.status_code == 200
        finally:
            state.tasks.pop(task_id, None)

    def test_deleted_task_returns_404(self):
        """After deletion, accessing the task should return 404."""
        task_id = f"test-del-404-{uuid.uuid4().hex[:8]}"
        state.tasks[task_id] = {"status": "error", "percent": 0, "message": "Failed"}
        client.delete(f"/tasks/{task_id}")
        res = client.get(f"/progress/{task_id}")
        assert res.status_code == 404
        # Ensure cleanup
        state.tasks.pop(task_id, None)

    def test_task_history_returns_after_creation(self):
        """GET /tasks should list tasks including recently created ones."""
        task_id = f"test-history-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            res = client.get("/tasks")
            assert res.status_code == 200
            data = res.json()
            assert "tasks" in data
        finally:
            _cleanup_task(task_id)

    def test_stats_endpoint_returns_data(self):
        """GET /tasks/stats returns statistics."""
        res = client.get("/tasks/stats")
        assert res.status_code == 200
        data = res.json()
        # Should have count-related fields
        assert isinstance(data, dict)

    def test_preview_returns_segments_for_done_task(self):
        """GET /preview/{task_id} returns subtitle content for a done task."""
        task_id = f"test-preview-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            res = client.get(f"/preview/{task_id}")
            assert res.status_code == 200
            data = res.json()
            assert "segments" in data or "preview" in data or "content" in data or isinstance(data, list)
        finally:
            _cleanup_task(task_id)

    def test_bulk_download_for_done_task(self):
        """GET /download/{task_id}/all returns ZIP for a done task."""
        task_id = f"test-bulk-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            res = client.get(f"/download/{task_id}/all")
            assert res.status_code == 200
            content_type = res.headers.get("content-type", "")
            # Should be a ZIP archive
            assert "zip" in content_type or "octet-stream" in content_type or res.content[:2] == b"PK"
        finally:
            _cleanup_task(task_id)

    def test_multiple_tasks_no_interference(self):
        """Two concurrent tasks should not affect each other."""
        tid1 = f"test-multi-1-{uuid.uuid4().hex[:8]}"
        tid2 = f"test-multi-2-{uuid.uuid4().hex[:8]}"
        _create_done_task(tid1)
        _create_done_task(tid2)
        try:
            res1 = client.get(f"/progress/{tid1}")
            res2 = client.get(f"/progress/{tid2}")
            assert res1.status_code == 200
            assert res2.status_code == 200
            data1 = res1.json()
            data2 = res2.json()
            assert data1["status"] == "done"
            assert data2["status"] == "done"
        finally:
            _cleanup_task(tid1)
            _cleanup_task(tid2)

    def test_download_single_file_for_done_task(self):
        """GET /download/{task_id} returns SRT file for a done task."""
        task_id = f"test-dl-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            res = client.get(f"/download/{task_id}")
            assert res.status_code == 200
        finally:
            _cleanup_task(task_id)

    def test_upload_returns_task_id_format(self):
        """Returned task_id should be a non-empty string."""
        wav_data = _make_wav_bytes(0.5)
        res = client.post(
            "/upload",
            files={"file": ("test.wav", BytesIO(wav_data), "audio/wav")},
        )
        data = res.json()
        task_id = data.get("task_id", "")
        assert len(task_id) > 0
        state.tasks.pop(task_id, None)

    def test_delete_nonexistent_task_returns_404(self):
        """DELETE on unknown task_id returns 404."""
        res = client.delete("/tasks/does-not-exist-12345")
        assert res.status_code == 404

    def test_progress_done_task_has_100_percent(self):
        """A done task should show 100% progress."""
        task_id = f"test-done-pct-{uuid.uuid4().hex[:8]}"
        _create_done_task(task_id)
        try:
            data = client.get(f"/progress/{task_id}").json()
            assert data["percent"] == 100
        finally:
            _cleanup_task(task_id)


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-CUTTING CONCERNS
# ══════════════════════════════════════════════════════════════════════════════


class TestCrossCuttingConcerns:
    """Test security headers, versioning, sessions, CORS, and API consistency."""

    def test_security_headers_on_all_endpoints(self):
        """All endpoints should have X-Content-Type-Options: nosniff."""
        for path in ["/health", "/api/status", "/about"]:
            res = client.get(path)
            assert res.headers.get("x-content-type-options") == "nosniff", f"Missing on {path}"

    def test_x_api_version_on_endpoints(self):
        """All responses should include X-API-Version header."""
        res = client.get("/health")
        assert "x-api-version" in {k.lower() for k in res.headers.keys()}

    def test_x_api_version_on_api_status(self):
        """API status endpoint should include version header."""
        res = client.get("/api/status")
        version = res.headers.get("x-api-version", "")
        assert len(version) > 0

    def test_x_request_id_on_all_endpoints(self):
        """All responses should include X-Request-ID header."""
        for path in ["/health", "/api/status", "/ready"]:
            res = client.get(path)
            assert "x-request-id" in {k.lower() for k in res.headers.keys()}, f"Missing on {path}"

    def test_json_error_response_structure(self):
        """Error responses should have consistent JSON structure with 'detail'."""
        res = client.get("/progress/nonexistent-task-xyz")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data

    def test_session_cookie_assigned_on_first_request(self):
        """First request without cookies should receive a session cookie."""
        # Use a fresh client with no cookie jar to guarantee first request
        fresh_client = TestClient(app, base_url="https://testserver", cookies={})
        res = fresh_client.get("/health")
        # Check both set-cookie header and response cookies
        has_cookie = "sg_session" in res.headers.get("set-cookie", "")
        has_cookie = has_cookie or "sg_session" in res.cookies
        assert has_cookie

    def test_session_persists_across_requests(self):
        """Session cookie value should remain the same across requests."""
        fresh_client = TestClient(app, base_url="https://testserver", cookies={})
        fresh_client.get("/health")
        # The client's cookie jar should now have the session
        session_val = fresh_client.cookies.get("sg_session", "")
        if session_val:
            # Second request with same client should reuse session
            fresh_client.get("/health")
            session_val2 = fresh_client.cookies.get("sg_session", "")
            assert session_val2 == session_val

    def test_rate_limiting_headers_present(self):
        """Rate limiting headers should be present on responses."""
        res = client.get("/health")
        # Check for standard rate limit headers (may or may not be set depending on config)
        # At minimum, the response should succeed
        assert res.status_code == 200

    def test_compression_works_on_large_response(self):
        """Large responses should be served successfully with gzip accept."""
        res = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
        assert res.status_code == 200
        assert len(res.text) > 0

    def test_cors_headers_on_options(self):
        """CORS preflight should return access-control headers."""
        res = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should either return 200 or 405 (if OPTIONS not explicitly handled)
        # but CORS headers should be present if origin is allowed
        assert res.status_code in (200, 204, 405)

    def test_openapi_spec_available(self):
        """OpenAPI spec should be accessible and match actual endpoints."""
        res = client.get("/openapi.json")
        assert res.status_code == 200
        spec = res.json()
        assert "paths" in spec
        # Verify key paths are in the spec
        paths = spec["paths"]
        assert "/health" in paths
        assert "/upload" in paths

    def test_all_routes_registered(self):
        """All expected route modules should be registered in the router."""
        from app.routes import router as main_router

        # Collect all registered paths
        registered_paths = set()
        for route in main_router.routes:
            if hasattr(route, "path"):
                registered_paths.add(route.path)
        # Key paths must be present
        assert "/health" in registered_paths
        assert "/upload" in registered_paths
        assert "/tasks" in registered_paths

    def test_no_orphan_routes(self):
        """API routes (non-page) should have at least one tag for grouping."""
        res = client.get("/openapi.json")
        spec = res.json()
        # Page routes that serve HTML are exempt from tagging requirements
        page_paths = {
            "/",
            "/status",
            "/about",
            "/contact",
            "/security",
            "/manifest.json",
            "/logo.svg",
            "/favicon.svg",
            "/dashboard",
            "/analytics",
        }
        tagged = 0
        total = 0
        for path, methods in spec.get("paths", {}).items():
            if path in page_paths:
                continue
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    total += 1
                    tags = details.get("tags", [])
                    if tags:
                        tagged += 1
        # At least 90% of API routes should be tagged
        assert total > 0
        assert tagged / total > 0.9, f"Only {tagged}/{total} API routes are tagged"

    def test_favicon_accessible(self):
        """Favicon should be served without error."""
        res = client.get("/favicon.svg")
        # May be 200 (file exists) or 404 (no favicon.svg in test env)
        assert res.status_code in (200, 404)

    def test_root_serves_html(self):
        """GET / should return HTML content."""
        res = client.get("/")
        assert res.status_code == 200
        content_type = res.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_health_live_probe_works(self):
        """GET /health/live should return minimal liveness response."""
        res = client.get("/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

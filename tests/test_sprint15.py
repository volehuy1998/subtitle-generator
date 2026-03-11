"""Tests for Sprint 15: Notification & Export System.

S15-1: Bulk export as ZIP
S15-2: Share link creation
S15-3: Share link download
S15-4: Share link info
S15-5: Integration tests
"""

import tempfile
from pathlib import Path

from app.main import app
from app import state
from app.config import OUTPUT_DIR
from app.routes.export import _share_links
from fastapi.testclient import TestClient

client = TestClient(app)


def _cleanup():
    _share_links.clear()
    for tid in ["exp-task-1", "exp-task-2", "exp-task-pending"]:
        state.tasks.pop(tid, None)
        for ext in ("srt", "vtt", "json"):
            (OUTPUT_DIR / f"{tid}.{ext}").unlink(missing_ok=True)


def _setup_done_tasks():
    """Create done tasks with actual subtitle files."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    state.tasks["exp-task-1"] = {
        "status": "done", "filename": "lecture.mp4", "language": "en",
        "segments": 10, "session_id": "test-session",
    }
    state.tasks["exp-task-2"] = {
        "status": "done", "filename": "interview.mp4", "language": "ja",
        "segments": 20, "session_id": "test-session",
    }
    state.tasks["exp-task-pending"] = {
        "status": "transcribing", "filename": "pending.mp4",
        "session_id": "test-session",
    }

    # Create actual subtitle files
    (OUTPUT_DIR / "exp-task-1.srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
    (OUTPUT_DIR / "exp-task-1.vtt").write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n", encoding="utf-8")
    (OUTPUT_DIR / "exp-task-2.srt").write_text("1\n00:00:01,000 --> 00:00:03,000\nKonnichiwa\n", encoding="utf-8")


# ── S15-1: Bulk Export ──

class TestBulkExport:
    def setup_method(self):
        _cleanup()
        _setup_done_tasks()

    def teardown_method(self):
        _cleanup()

    def test_bulk_export_returns_zip(self):
        res = client.get("/export/bulk?session_only=false")
        assert res.status_code == 200
        assert "application/zip" in res.headers.get("content-type", "")

    def test_bulk_export_content_disposition(self):
        res = client.get("/export/bulk?session_only=false")
        assert "subtitles_srt.zip" in res.headers.get("content-disposition", "")

    def test_bulk_export_vtt_format(self):
        res = client.get("/export/bulk?format=vtt&session_only=false")
        assert res.status_code == 200

    def test_bulk_export_no_tasks_404(self):
        _cleanup()
        res = client.get("/export/bulk?session_only=false")
        assert res.status_code == 404


# ── S15-2: Share Link Creation ──

class TestShareLinks:
    def setup_method(self):
        _cleanup()
        _setup_done_tasks()

    def teardown_method(self):
        _cleanup()

    def test_create_share_link(self):
        res = client.post("/share/exp-task-1")
        assert res.status_code == 200
        data = res.json()
        assert "share_id" in data
        assert "share_url" in data

    def test_create_share_link_unknown_task(self):
        res = client.post("/share/nonexistent")
        assert res.status_code == 404

    def test_create_share_link_pending_task(self):
        res = client.post("/share/exp-task-pending")
        assert res.status_code == 400

    def test_share_link_stored(self):
        res = client.post("/share/exp-task-1")
        share_id = res.json()["share_id"]
        assert share_id in _share_links


# ── S15-3: Share Link Download ──

class TestShareDownload:
    def setup_method(self):
        _cleanup()
        _setup_done_tasks()

    def teardown_method(self):
        _cleanup()

    def test_download_via_share_link(self):
        res = client.post("/share/exp-task-1")
        share_id = res.json()["share_id"]
        dl = client.get(f"/share/{share_id}/download?format=srt")
        assert dl.status_code == 200
        assert "Hello" in dl.text

    def test_download_share_link_vtt(self):
        res = client.post("/share/exp-task-1")
        share_id = res.json()["share_id"]
        dl = client.get(f"/share/{share_id}/download?format=vtt")
        assert dl.status_code == 200

    def test_download_invalid_share_link(self):
        res = client.get("/share/invalid123/download")
        assert res.status_code == 404


# ── S15-4: Share Link Info ──

class TestShareInfo:
    def setup_method(self):
        _cleanup()
        _setup_done_tasks()

    def teardown_method(self):
        _cleanup()

    def test_share_info(self):
        res = client.post("/share/exp-task-1")
        share_id = res.json()["share_id"]
        info = client.get(f"/share/{share_id}/info")
        assert info.status_code == 200
        assert info.json()["filename"] == "lecture.mp4"

    def test_share_info_not_found(self):
        res = client.get("/share/invalid123/info")
        assert res.status_code == 404


# ── S15-5: Integration ──

class TestIntegration:
    def test_export_route_registered(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        assert "/export/bulk" in paths

    def test_share_route_registered(self):
        res = client.get("/openapi.json")
        paths = list(res.json()["paths"].keys())
        # Dynamic path will be /share/{task_id}
        share_paths = [p for p in paths if p.startswith("/share")]
        assert len(share_paths) >= 1

    def test_active_shares_function(self):
        from app.routes.export import get_active_shares
        assert isinstance(get_active_shares(), int)

"""Phase Lumen L9 — Subtitle embedding tests.

Tests embed/combine endpoints: POST /combine, GET /combine/{task_id}/status,
GET /combine/{task_id}/download, embed presets, quick embed, mode validation,
style parameters, and error handling.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")


def _add_task(task_id=None, status="done", **kwargs):
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test.wav",
        "session_id": "",
        "language_requested": "auto",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    task.update(kwargs)
    state.tasks[tid] = task
    return tid


def _cleanup(*task_ids):
    for tid in task_ids:
        state.tasks.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# EMBED PRESETS
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbedPresets:
    """Test GET /embed/presets."""

    def test_presets_returns_200(self):
        res = client.get("/embed/presets")
        assert res.status_code == 200

    def test_presets_has_presets_key(self):
        res = client.get("/embed/presets")
        assert "presets" in res.json()

    def test_presets_is_dict(self):
        res = client.get("/embed/presets")
        assert isinstance(res.json()["presets"], dict)

    def test_presets_has_default(self):
        res = client.get("/embed/presets")
        assert "default" in res.json()["presets"]

    def test_presets_default_has_font_name(self):
        res = client.get("/embed/presets")
        assert "font_name" in res.json()["presets"]["default"]

    def test_presets_default_has_font_size(self):
        res = client.get("/embed/presets")
        assert "font_size" in res.json()["presets"]["default"]

    def test_presets_default_has_bold(self):
        res = client.get("/embed/presets")
        assert "bold" in res.json()["presets"]["default"]

    def test_presets_default_has_position(self):
        res = client.get("/embed/presets")
        assert "position" in res.json()["presets"]["default"]

    def test_presets_multiple_available(self):
        res = client.get("/embed/presets")
        presets = res.json()["presets"]
        assert len(presets) >= 2


# ══════════════════════════════════════════════════════════════════════════════
# EMBED DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbedDownload:
    """Test GET /embed/download/{task_id}."""

    def test_download_nonexistent_task_returns_404(self):
        res = client.get("/embed/download/nonexistent-task")
        assert res.status_code == 404

    def test_download_task_without_embed_returns_404(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/embed/download/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_download_detail_message_no_embed(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/embed/download/{tid}")
            assert "No embedded video" in res.json()["detail"]
        finally:
            _cleanup(tid)

    def test_download_embed_file_not_on_disk(self):
        tid = _add_task(status="done", embedded_video="nonexistent_file.mp4")
        try:
            res = client.get(f"/embed/download/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EMBED ENDPOINT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbedEndpointValidation:
    """Test POST /embed/{task_id} validation."""

    def test_embed_nonexistent_task_returns_404(self):
        from io import BytesIO

        res = client.post(
            "/embed/nonexistent-task",
            files={"video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4")},
            data={"mode": "soft"},
        )
        assert res.status_code == 404

    def test_embed_task_not_done_returns_400(self):
        from io import BytesIO

        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                f"/embed/{tid}",
                files={"video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4")},
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_embed_invalid_video_extension_returns_400(self):
        from io import BytesIO

        tid = _add_task(status="done")
        try:
            res = client.post(
                f"/embed/{tid}",
                files={"video": ("test.txt", BytesIO(b"\x00" * 100), "text/plain")},
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# QUICK EMBED VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestQuickEmbedValidation:
    """Test POST /embed/{task_id}/quick validation."""

    def test_quick_embed_nonexistent_task_returns_404(self):
        res = client.post(
            "/embed/nonexistent-task/quick",
            data={"mode": "soft"},
        )
        assert res.status_code == 404

    def test_quick_embed_task_not_done_returns_400(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(
                f"/embed/{tid}/quick",
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_quick_embed_no_preserved_video_returns_400(self):
        tid = _add_task(status="done")
        try:
            res = client.post(
                f"/embed/{tid}/quick",
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_quick_embed_in_progress_returns_409(self):
        tid = _add_task(status="done", embed_in_progress=True, preserved_video="test.mp4")
        try:
            res = client.post(
                f"/embed/{tid}/quick",
                data={"mode": "soft"},
            )
            assert res.status_code == 409
        finally:
            _cleanup(tid)

    def test_quick_embed_preserved_file_missing_returns_404(self):
        tid = _add_task(status="done", preserved_video="nonexistent_video.mp4")
        try:
            res = client.post(
                f"/embed/{tid}/quick",
                data={"mode": "soft"},
            )
            assert res.status_code == 404
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# COMBINE STATUS
# ══════════════════════════════════════════════════════════════════════════════


class TestCombineStatus:
    """Test GET /combine/status/{task_id}."""

    def test_combine_status_nonexistent_returns_404(self):
        res = client.get("/combine/status/nonexistent-task")
        assert res.status_code == 404

    def test_combine_status_returns_200(self):
        tid = _add_task(status="combining", mode="soft")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_combine_status_has_task_id(self):
        tid = _add_task(status="combining")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)

    def test_combine_status_has_status_field(self):
        tid = _add_task(status="combining")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["status"] == "combining"
        finally:
            _cleanup(tid)

    def test_combine_status_has_percent(self):
        tid = _add_task(status="combining", percent=50)
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["percent"] == 50
        finally:
            _cleanup(tid)

    def test_combine_status_has_message(self):
        tid = _add_task(status="combining", message="Processing...")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["message"] == "Processing..."
        finally:
            _cleanup(tid)

    def test_combine_status_done_has_combined_video(self):
        tid = _add_task(status="done", combined_video="out.mp4")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["combined_video"] == "out.mp4"
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# COMBINE DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════


class TestCombineDownload:
    """Test GET /combine/download/{task_id}."""

    def test_combine_download_nonexistent_returns_404(self):
        res = client.get("/combine/download/nonexistent-task")
        assert res.status_code == 404

    def test_combine_download_no_video_returns_404(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/combine/download/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_combine_download_detail_message(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/combine/download/{tid}")
            assert "No combined video" in res.json()["detail"]
        finally:
            _cleanup(tid)

    def test_combine_download_file_missing_returns_404(self):
        tid = _add_task(status="done", combined_video="missing_file.mp4")
        try:
            res = client.get(f"/combine/download/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# COMBINE ENDPOINT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestCombineEndpointValidation:
    """Test POST /combine validation."""

    def test_combine_missing_video_returns_422(self):
        from io import BytesIO

        res = client.post(
            "/combine",
            files={"subtitle": ("test.srt", BytesIO(b"1\n00:00:00,000 --> 00:00:01,000\nHello\n"), "text/plain")},
            data={"mode": "soft"},
        )
        assert res.status_code == 422

    def test_combine_missing_subtitle_returns_422(self):
        from io import BytesIO

        res = client.post(
            "/combine",
            files={"video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4")},
            data={"mode": "soft"},
        )
        assert res.status_code == 422

    def test_combine_invalid_video_ext_returns_400(self):
        from io import BytesIO

        res = client.post(
            "/combine",
            files={
                "video": ("test.txt", BytesIO(b"\x00" * 100), "text/plain"),
                "subtitle": ("test.srt", BytesIO(b"1\n00:00:00,000 --> 00:00:01,000\nHi\n"), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert res.status_code == 400

    def test_combine_invalid_subtitle_ext_returns_400(self):
        from io import BytesIO

        res = client.post(
            "/combine",
            files={
                "video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4"),
                "subtitle": ("test.txt", BytesIO(b"some text"), "text/plain"),
            },
            data={"mode": "soft"},
        )
        assert res.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# STYLE PRESETS CONTENT
# ══════════════════════════════════════════════════════════════════════════════


class TestStylePresetsContent:
    """Test preset content values."""

    def test_preset_font_size_is_int(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert isinstance(preset["font_size"], int), f"{name} font_size not int"

    def test_preset_bold_is_bool(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert isinstance(preset["bold"], bool), f"{name} bold not bool"

    def test_preset_position_valid(self):
        res = client.get("/embed/presets")
        valid_positions = {"top", "center", "bottom"}
        for name, preset in res.json()["presets"].items():
            assert preset["position"] in valid_positions, f"{name} invalid position"

    def test_preset_font_name_is_string(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert isinstance(preset["font_name"], str), f"{name} font_name not str"

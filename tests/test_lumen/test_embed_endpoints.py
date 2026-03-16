"""Phase Lumen L25 — Embed/combine endpoint comprehensive tests.

Tests embed presets content validation, quick embed edge cases, combine
endpoint validation, style parameters, mode handling, and download behavior.
Complements test_subtitle_embedding.py with deeper coverage.
— Scout (QA Lead)
"""

import uuid
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app
from app.services.subtitle_embed import STYLE_PRESETS, SubtitleStyle

client = TestClient(app, base_url="https://testserver")


def _add_task(task_id=None, status="done", **kwargs):
    tid = task_id or str(uuid.uuid4())
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test_video.mp4",
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
# PRESET CONTENT DEEP VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestPresetContentDeep:
    """Deep validation of embed preset content and structure."""

    def test_presets_contains_youtube_white(self):
        res = client.get("/embed/presets")
        assert "youtube_white" in res.json()["presets"]

    def test_presets_contains_youtube_yellow(self):
        res = client.get("/embed/presets")
        assert "youtube_yellow" in res.json()["presets"]

    def test_presets_contains_cinema(self):
        res = client.get("/embed/presets")
        assert "cinema" in res.json()["presets"]

    def test_presets_contains_large_bold(self):
        res = client.get("/embed/presets")
        assert "large_bold" in res.json()["presets"]

    def test_all_presets_have_font_name(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert "font_name" in preset, f"Preset {name} missing font_name"

    def test_all_presets_have_font_size(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert "font_size" in preset, f"Preset {name} missing font_size"

    def test_all_presets_have_position(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert "position" in preset, f"Preset {name} missing position"

    def test_all_presets_have_bold(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert "bold" in preset, f"Preset {name} missing bold"

    def test_all_preset_names_are_strings(self):
        res = client.get("/embed/presets")
        for name in res.json()["presets"]:
            assert isinstance(name, str)

    def test_all_preset_font_sizes_positive(self):
        res = client.get("/embed/presets")
        for name, preset in res.json()["presets"].items():
            assert preset["font_size"] > 0, f"Preset {name} has non-positive font_size"

    def test_presets_endpoint_is_cacheable(self):
        res = client.get("/embed/presets")
        assert res.headers.get("cache-control") is not None


# ══════════════════════════════════════════════════════════════════════════════
# STYLE PRESETS UNIT TESTS (in-memory, no HTTP)
# ══════════════════════════════════════════════════════════════════════════════


class TestStylePresetsUnit:
    """Unit tests for STYLE_PRESETS dictionary."""

    def test_default_preset_exists(self):
        assert "default" in STYLE_PRESETS

    def test_default_preset_is_subtitle_style(self):
        assert isinstance(STYLE_PRESETS["default"], SubtitleStyle)

    def test_default_font_is_arial(self):
        assert STYLE_PRESETS["default"].font_name == "Arial"

    def test_default_font_size_is_24(self):
        assert STYLE_PRESETS["default"].font_size == 24

    def test_default_position_is_bottom(self):
        assert STYLE_PRESETS["default"].position == "bottom"

    def test_all_presets_are_subtitle_style(self):
        for name, style in STYLE_PRESETS.items():
            assert isinstance(style, SubtitleStyle), f"Preset {name} is not SubtitleStyle"

    def test_font_size_bounds_reasonable(self):
        for name, style in STYLE_PRESETS.items():
            assert 8 <= style.font_size <= 72, f"Preset {name} font_size {style.font_size} out of bounds"

    def test_position_values_valid(self):
        valid = {"top", "center", "bottom"}
        for name, style in STYLE_PRESETS.items():
            assert style.position in valid, f"Preset {name} has invalid position '{style.position}'"


# ══════════════════════════════════════════════════════════════════════════════
# QUICK EMBED EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestQuickEmbedEdgeCases:
    """Additional edge case tests for POST /embed/{task_id}/quick."""

    def test_quick_embed_returns_404_for_random_uuid(self):
        fake_id = str(uuid.uuid4())
        res = client.post(f"/embed/{fake_id}/quick", data={"mode": "soft"})
        assert res.status_code == 404

    def test_quick_embed_error_status_returns_400(self):
        tid = _add_task(status="error")
        try:
            res = client.post(f"/embed/{tid}/quick", data={"mode": "soft"})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_quick_embed_pending_status_returns_400(self):
        tid = _add_task(status="pending")
        try:
            res = client.post(f"/embed/{tid}/quick", data={"mode": "soft"})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_quick_embed_no_preserved_video_detail_message(self):
        tid = _add_task(status="done")
        try:
            res = client.post(f"/embed/{tid}/quick", data={"mode": "soft"})
            assert "preserved" in res.json()["detail"].lower() or "upload" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_quick_embed_in_progress_detail_message(self):
        tid = _add_task(status="done", embed_in_progress=True, preserved_video="test.mp4")
        try:
            res = client.post(f"/embed/{tid}/quick", data={"mode": "soft"})
            assert res.status_code == 409
            assert "progress" in res.json()["detail"].lower() or "wait" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EMBED ENDPOINT — TASK STATE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbedTaskStateValidation:
    """Test POST /embed/{task_id} task state requirements."""

    def test_embed_transcribing_task_returns_400(self):
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

    def test_embed_error_task_returns_400(self):
        tid = _add_task(status="error")
        try:
            res = client.post(
                f"/embed/{tid}",
                files={"video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4")},
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_embed_extracting_task_returns_400(self):
        tid = _add_task(status="extracting")
        try:
            res = client.post(
                f"/embed/{tid}",
                files={"video": ("test.mp4", BytesIO(b"\x00" * 100), "video/mp4")},
                data={"mode": "soft"},
            )
            assert res.status_code == 400
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EMBED DOWNLOAD EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestEmbedDownloadEdgeCases:
    """Additional edge cases for embed download endpoint."""

    def test_embed_download_random_uuid_returns_404(self):
        fake_id = str(uuid.uuid4())
        res = client.get(f"/embed/download/{fake_id}")
        assert res.status_code == 404

    def test_embed_download_empty_string_task_returns_404(self):
        # Empty task_id path segment; FastAPI may handle this differently
        res = client.get("/embed/download/")
        # Either 404 or 307 redirect is acceptable
        assert res.status_code in (404, 307, 405)

    def test_embed_download_detail_when_no_embed(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/embed/download/{tid}")
            detail = res.json()["detail"]
            assert "embed" in detail.lower() or "No embedded" in detail
        finally:
            _cleanup(tid)

    def test_embed_download_embedded_file_not_on_disk(self):
        tid = _add_task(status="done", embedded_video="ghost_file_xyz.mp4")
        try:
            res = client.get(f"/embed/download/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_embed_download_returns_file_when_exists(self):
        """If an embedded video file exists on disk, download returns 200."""
        tid = _add_task(status="done", embedded_video="test_embed_output.mp4")
        out_file = OUTPUT_DIR / "test_embed_output.mp4"
        try:
            out_file.write_bytes(b"\x00" * 1000)
            res = client.get(f"/embed/download/{tid}")
            assert res.status_code == 200
        finally:
            out_file.unlink(missing_ok=True)
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# COMBINE STATUS STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════


class TestCombineStatusStructure:
    """Test combine status response structure in detail."""

    def test_combine_status_has_mode_field(self):
        tid = _add_task(status="combining", mode="hard")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["mode"] == "hard"
        finally:
            _cleanup(tid)

    def test_combine_status_default_percent_zero(self):
        tid = _add_task(status="combining")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["percent"] == 0
        finally:
            _cleanup(tid)

    def test_combine_status_done_combined_video_none_when_missing(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/combine/status/{tid}")
            assert res.json()["combined_video"] is None
        finally:
            _cleanup(tid)

    def test_combine_status_random_uuid_returns_404(self):
        fake_id = str(uuid.uuid4())
        res = client.get(f"/combine/status/{fake_id}")
        assert res.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# COMBINE DOWNLOAD EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════


class TestCombineDownloadEdgeCases:
    """Additional edge cases for combine download endpoint."""

    def test_combine_download_random_uuid_returns_404(self):
        fake_id = str(uuid.uuid4())
        res = client.get(f"/combine/download/{fake_id}")
        assert res.status_code == 404

    def test_combine_download_returns_file_when_exists(self):
        tid = _add_task(status="done", combined_video="test_combine_output.mp4")
        out_file = OUTPUT_DIR / "test_combine_output.mp4"
        try:
            out_file.write_bytes(b"\x00" * 1000)
            res = client.get(f"/combine/download/{tid}")
            assert res.status_code == 200
        finally:
            out_file.unlink(missing_ok=True)
            _cleanup(tid)

    def test_combine_download_filename_uses_original_stem(self):
        tid = _add_task(status="done", combined_video="test_combine_dl.mp4", filename="my_video.mp4")
        out_file = OUTPUT_DIR / "test_combine_dl.mp4"
        try:
            out_file.write_bytes(b"\x00" * 1000)
            res = client.get(f"/combine/download/{tid}")
            disposition = res.headers.get("content-disposition", "")
            assert "my_video" in disposition
        finally:
            out_file.unlink(missing_ok=True)
            _cleanup(tid)

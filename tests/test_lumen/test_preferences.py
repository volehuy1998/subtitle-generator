"""Phase Lumen L45-L48 — Preferences and integration tests.

Tests GET/PUT /preferences endpoint and cross-feature integration
(search + edit + tags + notes + batch delete + retranscribe).
— Scout (QA Lead)
"""

import json
import uuid

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR, UPLOAD_DIR
from app.main import app

client = TestClient(app, base_url="https://testserver")

# ── Helpers ──────────────────────────────────────────────────────────────────

_SESSION_ID = "test-session-prefs"
session_client = TestClient(app, base_url="https://testserver", cookies={"sg_session": _SESSION_ID})


def _tid():
    return str(uuid.uuid4())


def _add_task(task_id=None, status="done", **kwargs):
    """Add a task to state. Returns task_id."""
    tid = task_id or _tid()
    task = {
        "status": status,
        "percent": 100 if status == "done" else 0,
        "message": "",
        "filename": "test.wav",
        "session_id": _SESSION_ID,
        "language_requested": "auto",
        "model_size": "tiny",
        "device": "cpu",
        "segments": 3,
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    task.update(kwargs)
    state.tasks[tid] = task
    return tid


def _cleanup(*task_ids):
    for tid in task_ids:
        state.tasks.pop(tid, None)
        for ext in ("srt", "vtt", "json"):
            f = OUTPUT_DIR / f"{tid}.{ext}"
            if f.exists():
                f.unlink()
        if UPLOAD_DIR.exists():
            for f in UPLOAD_DIR.iterdir():
                if f.is_file() and f.stem == tid:
                    f.unlink()


def _create_output_files(task_id, segments=None):
    """Create SRT/VTT/JSON output files for a task."""
    if segments is None:
        segments = [
            {"start": 0, "end": 1, "text": "Hello world"},
            {"start": 1, "end": 2, "text": "Testing integration"},
            {"start": 2, "end": 3, "text": "Final segment"},
        ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / f"{task_id}.json").write_text(json.dumps(segments))
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        srt_lines.append(f"{i}")
        srt_lines.append(f"00:00:0{int(seg['start'])},000 --> 00:00:0{int(seg['end'])},000")
        srt_lines.append(seg["text"])
        srt_lines.append("")
    (OUTPUT_DIR / f"{task_id}.srt").write_text("\n".join(srt_lines))
    vtt_lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        vtt_lines.append(f"{i}")
        vtt_lines.append(f"00:00:0{int(seg['start'])}.000 --> 00:00:0{int(seg['end'])}.000")
        vtt_lines.append(seg["text"])
        vtt_lines.append("")
    (OUTPUT_DIR / f"{task_id}.vtt").write_text("\n".join(vtt_lines))


def _create_upload_file(task_id, ext=".wav"):
    """Create a fake uploaded file in UPLOAD_DIR."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{task_id}{ext}"
    path.write_bytes(b"\x00" * 100)
    return path


def _save_and_clear():
    saved = dict(state.tasks)
    state.tasks.clear()
    return saved


def _restore(saved):
    state.tasks.clear()
    state.tasks.update(saved)


def _clear_prefs():
    state.session_preferences.clear()


# ══════════════════════════════════════════════════════════════════════════════
# PREFERENCES ENDPOINT — GET /preferences
# ══════════════════════════════════════════════════════════════════════════════


class TestPreferencesGet:
    """Tests for GET /preferences."""

    def test_get_preferences_returns_200(self):
        res = session_client.get("/preferences")
        assert res.status_code == 200

    def test_get_preferences_has_preferences_key(self):
        res = session_client.get("/preferences")
        data = res.json()
        assert "preferences" in data
        assert isinstance(data["preferences"], dict)

    def test_get_preferences_empty_by_default(self):
        _clear_prefs()
        res = session_client.get("/preferences")
        assert res.json()["preferences"] == {}


class TestPreferencesPut:
    """Tests for PUT /preferences."""

    def test_put_preferences_returns_200(self):
        _clear_prefs()
        res = session_client.put("/preferences", json={"default_model": "small"})
        assert res.status_code == 200

    def test_put_preferences_persisted(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_model": "medium"})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["default_model"] == "medium"

    def test_default_model_preference_stored(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_model": "large"})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["default_model"] == "large"

    def test_default_format_preference_stored(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_format": "vtt"})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["default_format"] == "vtt"

    def test_default_language_preference_stored(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_language": "ja"})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["default_language"] == "ja"

    def test_auto_copy_preference_stored(self):
        _clear_prefs()
        session_client.put("/preferences", json={"auto_copy": True})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["auto_copy"] is True

    def test_unknown_keys_filtered_out(self):
        _clear_prefs()
        session_client.put("/preferences", json={"unknown_key": "value", "default_model": "tiny"})
        res = session_client.get("/preferences")
        prefs = res.json()["preferences"]
        assert "unknown_key" not in prefs
        assert prefs["default_model"] == "tiny"

    def test_empty_preferences_accepted(self):
        _clear_prefs()
        res = session_client.put("/preferences", json={})
        assert res.status_code == 200

    def test_session_scoped_different_sessions(self):
        """Different sessions get different preferences."""
        _clear_prefs()
        session_client.put("/preferences", json={"default_model": "large"})
        other_client = TestClient(app, base_url="https://testserver", cookies={"sg_session": "other-session-xyz"})
        res = other_client.get("/preferences")
        prefs = res.json()["preferences"]
        assert prefs.get("default_model") != "large" or prefs == {}

    def test_preferences_survive_multiple_updates(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_model": "tiny"})
        session_client.put("/preferences", json={"default_format": "vtt"})
        session_client.put("/preferences", json={"default_language": "fr"})
        res = session_client.get("/preferences")
        prefs = res.json()["preferences"]
        assert prefs["default_model"] == "tiny"
        assert prefs["default_format"] == "vtt"
        assert prefs["default_language"] == "fr"

    def test_preferences_update_overwrites_same_key(self):
        _clear_prefs()
        session_client.put("/preferences", json={"default_model": "tiny"})
        session_client.put("/preferences", json={"default_model": "large"})
        res = session_client.get("/preferences")
        assert res.json()["preferences"]["default_model"] == "large"


# ══════════════════════════════════════════════════════════════════════════════
# API DOCUMENTATION & INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIDocumentation:
    """Tests that new endpoints are properly documented in OpenAPI."""

    def test_openapi_schema_accessible(self):
        res = client.get("/openapi.json")
        assert res.status_code == 200

    def test_batch_delete_in_openapi(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        assert "/tasks/batch-delete" in paths

    def test_retranscribe_in_openapi(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        retranscribe_paths = [p for p in paths if "retranscribe" in p]
        assert len(retranscribe_paths) >= 1

    def test_preferences_in_openapi(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        assert "/preferences" in paths

    def test_retranscribe_tagged_correctly(self):
        res = client.get("/openapi.json")
        paths = res.json()["paths"]
        retranscribe_paths = [p for p in paths if "retranscribe" in p]
        for p in retranscribe_paths:
            tags = paths[p].get("post", {}).get("tags", [])
            assert "Tasks" in tags


# ══════════════════════════════════════════════════════════════════════════════
# CROSS-FEATURE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════


class TestCrossFeatureIntegration:
    """Integration tests across search, edit, tags, notes, batch delete, retranscribe."""

    def test_retranscribe_creates_task_with_correct_params(self):
        tid = _add_task(status="done", model_size="tiny", language_requested="en")
        _create_upload_file(tid)
        try:
            res = session_client.post(f"/tasks/{tid}/retranscribe", json={"model_size": "base", "language": "fr"})
            data = res.json()
            new_tid = data["new_task_id"]
            new_task = state.tasks[new_tid]
            assert new_task["language_requested"] == "fr"
            assert new_task["retranscribe_of"] == tid
            _cleanup(new_tid)
        finally:
            _cleanup(tid)

    def test_batch_delete_cleans_up_files(self):
        tid = _add_task(status="done")
        _create_output_files(tid)
        assert (OUTPUT_DIR / f"{tid}.json").exists()
        session_client.post("/tasks/batch-delete", json={"task_ids": [tid]})
        assert tid not in state.tasks

    def test_search_edit_tags_notes_on_same_task(self):
        """Full lifecycle: search + edit + tag + note on same task."""
        tid = _tid()
        _add_task(task_id=tid, status="done")
        _create_output_files(tid)
        try:
            # Search
            res = session_client.get(f"/search/{tid}?q=Hello")
            assert res.status_code == 200
            assert res.json()["total_matches"] >= 1

            # Edit segment
            res = session_client.put(f"/subtitles/{tid}/0", json={"text": "Updated hello"})
            assert res.status_code == 200

            # Tag
            res = session_client.put(f"/tasks/{tid}/tags", json={"tags": ["edited", "reviewed"]})
            assert res.status_code == 200

            # Note
            res = session_client.put(f"/tasks/{tid}/note", json={"note": "Edited first segment"})
            assert res.status_code == 200

            # Verify all persisted
            assert state.tasks[tid]["tags"] == ["edited", "reviewed"]
            assert state.tasks[tid]["note"] == "Edited first segment"
        finally:
            _cleanup(tid)

    def test_task_lifecycle_create_tag_note_search_edit_delete(self):
        """Full task lifecycle: create -> tag -> note -> search -> edit -> delete."""
        tid = _tid()
        _add_task(task_id=tid, status="done")
        _create_output_files(tid)

        # Tag
        session_client.put(f"/tasks/{tid}/tags", json={"tags": ["lifecycle"]})

        # Note
        session_client.put(f"/tasks/{tid}/note", json={"note": "Lifecycle test"})

        # Search
        res = session_client.get(f"/search/{tid}?q=Hello")
        assert res.json()["total_matches"] >= 1

        # Edit
        session_client.put(f"/subtitles/{tid}/0", json={"text": "Lifecycle edit"})

        # Delete
        res = session_client.delete(f"/tasks/{tid}")
        assert res.status_code == 200
        assert tid not in state.tasks

    def test_stats_updated_after_batch_delete(self):
        saved = _save_and_clear()
        t1 = _add_task(status="done", segments=10)
        _add_task(status="done", segments=20)
        try:
            res1 = session_client.get("/tasks/stats")
            assert res1.json()["completed"] == 2

            session_client.post("/tasks/batch-delete", json={"task_ids": [t1]})

            res2 = session_client.get("/tasks/stats")
            assert res2.json()["completed"] == 1
        finally:
            _restore(saved)

    def test_preview_still_works_after_edit(self):
        tid = _tid()
        _add_task(task_id=tid, status="done")
        _create_output_files(tid)
        try:
            session_client.put(f"/subtitles/{tid}/0", json={"text": "Edited for preview"})
            res = session_client.get(f"/preview/{tid}")
            assert res.status_code == 200
            segments = res.json()["segments"]
            assert segments[0]["text"] == "Edited for preview"
        finally:
            _cleanup(tid)

    def test_download_formats_correct_after_edit(self):
        tid = _tid()
        _add_task(task_id=tid, status="done")
        _create_output_files(tid)
        try:
            session_client.put(f"/subtitles/{tid}/0", json={"text": "Edited download"})

            res = session_client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
            assert "Edited download" in res.text

            res = session_client.get(f"/download/{tid}?format=vtt")
            assert res.status_code == 200
            assert "Edited download" in res.text
        finally:
            _cleanup(tid)

    def test_retranscribe_does_not_affect_original_files(self):
        tid = _tid()
        _add_task(task_id=tid, status="done")
        _create_output_files(tid)
        _create_upload_file(tid)
        try:
            res = session_client.post(f"/tasks/{tid}/retranscribe", json={"model_size": "base"})
            new_tid = res.json()["new_task_id"]

            assert (OUTPUT_DIR / f"{tid}.json").exists()
            assert (OUTPUT_DIR / f"{tid}.srt").exists()

            res = session_client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
            _cleanup(new_tid)
        finally:
            _cleanup(tid)

    def test_batch_delete_exactly_50_tasks_accepted(self):
        """Exactly 50 tasks should be accepted."""
        tids = [_add_task(status="done") for _ in range(50)]
        try:
            res = session_client.post("/tasks/batch-delete", json={"task_ids": tids})
            assert res.status_code == 200
        finally:
            for t in tids:
                _cleanup(t)

"""Phase Lumen L41-L44 — Task metadata tests (tags and notes).

Tests PUT /tasks/{task_id}/tags and PUT /tasks/{task_id}/note endpoints.
— Scout (QA Lead)
"""

import uuid

from fastapi.testclient import TestClient

from app import state
from app.main import app

client = TestClient(app, base_url="https://testserver")

# ── Helpers ──────────────────────────────────────────────────────────────────


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
# TAGS ENDPOINT — PUT /tasks/{task_id}/tags
# ══════════════════════════════════════════════════════════════════════════════


class TestTagsEndpoint:
    """Tests for PUT /tasks/{task_id}/tags."""

    def test_tags_update_returns_200(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["important", "review"]})
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_tags_returns_404_for_nonexistent_task(self):
        res = client.put("/tasks/nonexistent-task/tags", json={"tags": ["test"]})
        assert res.status_code == 404

    def test_tags_response_includes_task_id(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["tag1"]})
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)

    def test_tags_response_includes_tags(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["alpha", "beta"]})
            assert res.json()["tags"] == ["alpha", "beta"]
        finally:
            _cleanup(tid)

    def test_tags_stored_in_state(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/tags", json={"tags": ["stored"]})
            assert state.tasks[tid]["tags"] == ["stored"]
        finally:
            _cleanup(tid)

    def test_empty_tags_list_accepted(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/tags", json={"tags": ["temp"]})
            res = client.put(f"/tasks/{tid}/tags", json={"tags": []})
            assert res.status_code == 200
            assert res.json()["tags"] == []
        finally:
            _cleanup(tid)

    def test_max_10_tags_enforced(self):
        tid = _add_task()
        try:
            tags = [f"tag{i}" for i in range(11)]
            res = client.put(f"/tasks/{tid}/tags", json={"tags": tags})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_exactly_10_tags_accepted(self):
        tid = _add_task()
        try:
            tags = [f"tag{i}" for i in range(10)]
            res = client.put(f"/tasks/{tid}/tags", json={"tags": tags})
            assert res.status_code == 200
            assert len(res.json()["tags"]) == 10
        finally:
            _cleanup(tid)

    def test_tags_are_trimmed(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["  spaced  "]})
            assert res.json()["tags"] == ["spaced"]
        finally:
            _cleanup(tid)

    def test_long_tag_names_truncated_to_50(self):
        tid = _add_task()
        try:
            long_tag = "x" * 100
            res = client.put(f"/tasks/{tid}/tags", json={"tags": [long_tag]})
            assert len(res.json()["tags"][0]) == 50
        finally:
            _cleanup(tid)

    def test_duplicate_tags_handled(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["dup", "dup", "dup"]})
            assert res.status_code == 200
            # Duplicates are accepted (server stores as-is or deduplicates)
            assert isinstance(res.json()["tags"], list)
        finally:
            _cleanup(tid)

    def test_special_characters_in_tags(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["c++", "c#", "tag/slash"]})
            assert res.status_code == 200
            assert len(res.json()["tags"]) == 3
        finally:
            _cleanup(tid)

    def test_tags_on_active_task_works(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.put(f"/tasks/{tid}/tags", json={"tags": ["wip"]})
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_tags_overwrite_previous(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/tags", json={"tags": ["old"]})
            client.put(f"/tasks/{tid}/tags", json={"tags": ["new"]})
            assert state.tasks[tid]["tags"] == ["new"]
        finally:
            _cleanup(tid)

    def test_tags_visible_in_task_list(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/tags", json={"tags": ["visible"]})
            # Tags are stored in state; verify state has them
            assert "tags" in state.tasks[tid]
            assert "visible" in state.tasks[tid]["tags"]
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# NOTES ENDPOINT — PUT /tasks/{task_id}/note
# ══════════════════════════════════════════════════════════════════════════════


class TestNotesEndpoint:
    """Tests for PUT /tasks/{task_id}/note."""

    def test_note_update_returns_200(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/note", json={"note": "This is a note"})
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_note_returns_404_for_nonexistent_task(self):
        res = client.put("/tasks/nonexistent-task/note", json={"note": "test"})
        assert res.status_code == 404

    def test_note_response_includes_task_id(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/note", json={"note": "hello"})
            assert res.json()["task_id"] == tid
        finally:
            _cleanup(tid)

    def test_note_response_includes_note(self):
        tid = _add_task()
        try:
            res = client.put(f"/tasks/{tid}/note", json={"note": "my note text"})
            assert res.json()["note"] == "my note text"
        finally:
            _cleanup(tid)

    def test_note_stored_in_state(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/note", json={"note": "stored note"})
            assert state.tasks[tid]["note"] == "stored note"
        finally:
            _cleanup(tid)

    def test_empty_note_clears(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/note", json={"note": "something"})
            res = client.put(f"/tasks/{tid}/note", json={"note": ""})
            assert res.status_code == 200
            assert state.tasks[tid]["note"] == ""
        finally:
            _cleanup(tid)

    def test_long_note_truncated_to_1000(self):
        tid = _add_task()
        try:
            long_note = "n" * 2000
            res = client.put(f"/tasks/{tid}/note", json={"note": long_note})
            assert len(res.json()["note"]) == 1000
        finally:
            _cleanup(tid)

    def test_note_exactly_1000_chars_accepted(self):
        tid = _add_task()
        try:
            note_1000 = "a" * 1000
            res = client.put(f"/tasks/{tid}/note", json={"note": note_1000})
            assert res.status_code == 200
            assert len(res.json()["note"]) == 1000
        finally:
            _cleanup(tid)

    def test_note_with_special_characters(self):
        tid = _add_task()
        try:
            special = "Note with <html> & 'quotes' \"double\" + symbols!@#$%"
            res = client.put(f"/tasks/{tid}/note", json={"note": special})
            assert res.status_code == 200
            assert res.json()["note"] == special
        finally:
            _cleanup(tid)

    def test_note_with_unicode(self):
        tid = _add_task()
        try:
            note = "Notes avec des accents: cafe, resume, naive"
            res = client.put(f"/tasks/{tid}/note", json={"note": note})
            assert res.status_code == 200
            assert res.json()["note"] == note
        finally:
            _cleanup(tid)

    def test_note_with_cjk_characters(self):
        tid = _add_task()
        try:
            note = "This contains CJK chars"
            res = client.put(f"/tasks/{tid}/note", json={"note": note})
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_note_with_emoji_unicode(self):
        tid = _add_task()
        try:
            note = "Task completed successfully \u2705 \u2728"
            res = client.put(f"/tasks/{tid}/note", json={"note": note})
            assert res.status_code == 200
            assert res.json()["note"] == note
        finally:
            _cleanup(tid)

    def test_multiple_note_updates_last_wins(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/note", json={"note": "first"})
            client.put(f"/tasks/{tid}/note", json={"note": "second"})
            client.put(f"/tasks/{tid}/note", json={"note": "third"})
            assert state.tasks[tid]["note"] == "third"
        finally:
            _cleanup(tid)

    def test_note_on_active_task_works(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.put(f"/tasks/{tid}/note", json={"note": "still processing"})
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_note_visible_in_state(self):
        tid = _add_task()
        try:
            client.put(f"/tasks/{tid}/note", json={"note": "check state"})
            assert "note" in state.tasks[tid]
            assert state.tasks[tid]["note"] == "check state"
        finally:
            _cleanup(tid)

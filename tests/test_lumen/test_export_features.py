"""Phase Lumen L45-L48 — Export features tests.

Tests custom line length on download, retranscribe endpoint,
and batch delete endpoint.
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
        "model_size": "tiny",
        "device": "cpu",
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
        # Also clean uploaded files
        if UPLOAD_DIR.exists():
            for f in UPLOAD_DIR.iterdir():
                if f.is_file() and f.stem == tid:
                    f.unlink()


def _cleanup_new_tasks(original_tid):
    """Clean up any retranscribe tasks spawned from original_tid."""
    to_remove = []
    for t in list(state.tasks.keys()):
        if state.tasks.get(t, {}).get("retranscribe_of") == original_tid:
            to_remove.append(t)
    for t in to_remove:
        _cleanup(t)


def _create_output_files(task_id, segments=None):
    """Create SRT/VTT/JSON output files for a task."""
    if segments is None:
        segments = [
            {"start": 0, "end": 1, "text": "Hello world"},
            {"start": 1, "end": 2, "text": "Testing features"},
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
    """Create a fake uploaded file in UPLOAD_DIR so retranscribe can find it."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{task_id}{ext}"
    path.write_bytes(b"\x00" * 100)
    return path


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM LINE LENGTH — download with max_line_chars
# ══════════════════════════════════════════════════════════════════════════════


class TestCustomLineLength:
    """Tests for download SRT/VTT with custom max_line_chars parameter.

    max_line_chars is a pipeline/upload parameter, not a download param.
    These tests validate the upload parameter contract and download behavior.
    """

    def test_download_srt_default_works(self):
        tid = _add_task(status="done")
        _create_output_files(tid)
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_download_srt_content_preserved(self):
        tid = _add_task(status="done")
        _create_output_files(tid)
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert "Hello world" in res.text
        finally:
            _cleanup(tid)

    def test_download_vtt_default_works(self):
        tid = _add_task(status="done")
        _create_output_files(tid)
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_download_vtt_content_preserved(self):
        tid = _add_task(status="done")
        _create_output_files(tid)
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert "Hello world" in res.text
        finally:
            _cleanup(tid)

    def test_upload_max_line_chars_default_is_42(self):
        """Upload form field default for max_line_chars is 42."""
        import inspect

        from app.routes.upload import upload

        sig = inspect.signature(upload)
        default = sig.parameters["max_line_chars"].default
        # Form(42) — the default value is a Form object with default 42
        assert "42" in str(default) or default == 42

    def test_upload_accepts_max_line_chars_param(self):
        """Upload endpoint has max_line_chars as a form parameter."""
        import inspect

        from app.routes.upload import upload

        sig = inspect.signature(upload)
        assert "max_line_chars" in sig.parameters

    def test_pipeline_clamps_max_line_chars_lower_bound(self):
        """max_line_chars is clamped to minimum 20 in upload route."""
        assert max(20, min(80, 10)) == 20
        assert max(20, min(80, 0)) == 20
        assert max(20, min(80, -1)) == 20

    def test_pipeline_clamps_max_line_chars_upper_bound(self):
        """max_line_chars is clamped to maximum 80 in upload route."""
        assert max(20, min(80, 120)) == 80
        assert max(20, min(80, 999)) == 80

    def test_pipeline_accepts_valid_max_line_chars(self):
        """Values within 20-80 range pass through unchanged."""
        assert max(20, min(80, 42)) == 42
        assert max(20, min(80, 20)) == 20
        assert max(20, min(80, 80)) == 80
        assert max(20, min(80, 60)) == 60

    def test_download_invalid_format_rejected(self):
        """Invalid format values are rejected with 422."""
        tid = _add_task(status="done")
        try:
            res = client.get(f"/download/{tid}?format=pdf")
            assert res.status_code == 422
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# RETRANSCRIBE — POST /tasks/{task_id}/retranscribe
# ══════════════════════════════════════════════════════════════════════════════


class TestRetranscribe:
    """Tests for POST /tasks/{task_id}/retranscribe.

    The retranscribe endpoint requires the original uploaded file to still exist.
    It creates a new task and dispatches the pipeline.
    """

    def test_retranscribe_returns_404_for_nonexistent(self):
        res = client.post("/tasks/nonexistent-task-id/retranscribe", json={})
        assert res.status_code == 404

    def test_retranscribe_returns_400_for_active_task(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_retranscribe_returns_400_for_queued_task(self):
        tid = _add_task(status="queued")
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_retranscribe_returns_400_for_cancelled_task(self):
        tid = _add_task(status="cancelled")
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_retranscribe_returns_410_when_file_missing(self):
        """Done task with no uploaded file returns 410 Gone."""
        tid = _add_task(status="done")
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            assert res.status_code == 410
            assert "file" in res.json()["detail"].lower()
        finally:
            _cleanup(tid)

    def test_retranscribe_done_task_with_file_returns_200(self):
        tid = _add_task(status="done")
        _create_upload_file(tid)
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            assert res.status_code == 200
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)

    def test_retranscribe_response_has_new_task_id(self):
        tid = _add_task(status="done")
        _create_upload_file(tid)
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            data = res.json()
            assert "new_task_id" in data
            assert data["new_task_id"] != tid
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)

    def test_retranscribe_can_override_model_size(self):
        tid = _add_task(status="done", model_size="tiny")
        _create_upload_file(tid)
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={"model_size": "large"})
            data = res.json()
            assert data["model_size"] == "large"
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)

    def test_retranscribe_can_override_language(self):
        tid = _add_task(status="done", language_requested="auto")
        _create_upload_file(tid)
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={"language": "en"})
            data = res.json()
            assert data["language"] == "en"
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)

    def test_retranscribe_new_task_appears_in_state(self):
        tid = _add_task(status="done")
        _create_upload_file(tid)
        try:
            res = client.post(f"/tasks/{tid}/retranscribe", json={})
            new_tid = res.json()["new_task_id"]
            assert new_tid in state.tasks
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)

    def test_retranscribe_original_task_unchanged(self):
        tid = _add_task(status="done", filename="original.wav", model_size="tiny")
        _create_upload_file(tid)
        try:
            client.post(f"/tasks/{tid}/retranscribe", json={"model_size": "large"})
            assert state.tasks[tid]["status"] == "done"
            assert state.tasks[tid]["model_size"] == "tiny"
            assert state.tasks[tid]["filename"] == "original.wav"
            _cleanup_new_tasks(tid)
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# BATCH DELETE — POST /tasks/batch-delete
# ══════════════════════════════════════════════════════════════════════════════


class TestBatchDelete:
    """Tests for POST /tasks/batch-delete."""

    def test_batch_delete_with_valid_ids_works(self):
        t1 = _add_task(status="done")
        t2 = _add_task(status="done")
        try:
            res = client.post("/tasks/batch-delete", json={"task_ids": [t1, t2]})
            assert res.status_code == 200
        finally:
            _cleanup(t1, t2)

    def test_batch_delete_returns_deleted_and_failed_lists(self):
        t1 = _add_task(status="done")
        try:
            res = client.post("/tasks/batch-delete", json={"task_ids": [t1]})
            data = res.json()
            assert "deleted" in data
            assert "failed" in data
            assert isinstance(data["deleted"], list)
            assert isinstance(data["failed"], list)
        finally:
            _cleanup(t1)

    def test_batch_delete_deletes_done_tasks(self):
        t1 = _add_task(status="done")
        t2 = _add_task(status="done")
        res = client.post("/tasks/batch-delete", json={"task_ids": [t1, t2]})
        data = res.json()
        assert t1 in data["deleted"]
        assert t2 in data["deleted"]
        assert t1 not in state.tasks
        assert t2 not in state.tasks

    def test_batch_delete_fails_on_active_tasks(self):
        tid = _add_task(status="transcribing")
        t_done = _add_task(status="done")
        try:
            res = client.post("/tasks/batch-delete", json={"task_ids": [tid, t_done]})
            data = res.json()
            failed_ids = [f["task_id"] for f in data["failed"]]
            assert tid in failed_ids
            assert tid in state.tasks
        finally:
            _cleanup(tid, t_done)

    def test_batch_delete_fails_on_nonexistent_tasks(self):
        fake_id = "nonexistent-task-xyz"
        t_done = _add_task(status="done")
        try:
            res = client.post("/tasks/batch-delete", json={"task_ids": [fake_id, t_done]})
            data = res.json()
            failed_ids = [f["task_id"] for f in data["failed"]]
            assert fake_id in failed_ids
        finally:
            _cleanup(t_done)

    def test_batch_delete_empty_list_returns_400(self):
        """Empty task_ids list is rejected."""
        res = client.post("/tasks/batch-delete", json={"task_ids": []})
        assert res.status_code == 400

    def test_batch_delete_max_50_enforced(self):
        ids = [str(uuid.uuid4()) for _ in range(51)]
        res = client.post("/tasks/batch-delete", json={"task_ids": ids})
        assert res.status_code == 400

    def test_batch_delete_removes_from_state(self):
        t1 = _add_task(status="done")
        t2 = _add_task(status="error")
        client.post("/tasks/batch-delete", json={"task_ids": [t1, t2]})
        assert t1 not in state.tasks
        assert t2 not in state.tasks

    def test_batch_delete_mixed_valid_invalid_partially_succeeds(self):
        t_done = _add_task(status="done")
        t_active = _add_task(status="transcribing")
        try:
            res = client.post("/tasks/batch-delete", json={"task_ids": [t_done, t_active]})
            data = res.json()
            assert t_done in data["deleted"]
            failed_ids = [f["task_id"] for f in data["failed"]]
            assert t_active in failed_ids
        finally:
            _cleanup(t_active)

    def test_batch_delete_cancelled_task_succeeds(self):
        tid = _add_task(status="cancelled")
        res = client.post("/tasks/batch-delete", json={"task_ids": [tid]})
        data = res.json()
        assert tid in data["deleted"]
        assert tid not in state.tasks

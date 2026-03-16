"""Phase Lumen L41-L44 — Subtitle search and single-segment edit tests.

Tests GET /search/{task_id} (subtitle text search) and
PUT /subtitles/{task_id}/{segment_index} (single-segment edit).
— Scout (QA Lead)
"""

import json
import uuid

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app

client = TestClient(app, base_url="https://testserver")

# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_task_with_output(task_id, segments=None):
    """Create a done task with JSON/SRT/VTT output files."""
    if segments is None:
        segments = [
            {"start": 0, "end": 1, "text": "Hello world"},
            {"start": 1, "end": 2, "text": "Testing search"},
            {"start": 2, "end": 3, "text": "Another segment"},
        ]
    state.tasks[task_id] = {
        "status": "done",
        "filename": "test.mp4",
        "session_id": "",
        "created_at": "2026-01-01T00:00:00",
    }
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


def _cleanup_task(task_id):
    """Remove task from state and clean up output files."""
    state.tasks.pop(task_id, None)
    for ext in ("json", "srt", "vtt"):
        path = OUTPUT_DIR / f"{task_id}.{ext}"
        if path.exists():
            path.unlink()


def _tid():
    return str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH ENDPOINT — GET /search/{task_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestSearchEndpoint:
    """Tests for GET /search/{task_id}?q=..."""

    def test_search_returns_200_for_done_task(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=Hello")
            assert res.status_code == 200
        finally:
            _cleanup_task(tid)

    def test_search_returns_404_for_nonexistent_task(self):
        res = client.get("/search/nonexistent-task-id?q=hello")
        assert res.status_code == 404

    def test_search_returns_400_for_active_task(self):
        tid = _tid()
        state.tasks[tid] = {
            "status": "transcribing",
            "filename": "t.mp4",
            "session_id": "",
            "created_at": "2026-01-01T00:00:00",
        }
        try:
            res = client.get(f"/search/{tid}?q=hello")
            assert res.status_code == 400
        finally:
            state.tasks.pop(tid, None)

    def test_search_response_has_required_keys(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=Hello")
            data = res.json()
            assert "query" in data
            assert "total_matches" in data
            assert "matches" in data
        finally:
            _cleanup_task(tid)

    def test_search_matches_contain_segment_fields(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=Hello")
            data = res.json()
            assert data["total_matches"] >= 1
            match = data["matches"][0]
            assert "start" in match
            assert "end" in match
            assert "text" in match
        finally:
            _cleanup_task(tid)

    def test_search_case_insensitive(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=hello")
            data = res.json()
            assert data["total_matches"] >= 1
            assert "Hello" in data["matches"][0]["text"]
        finally:
            _cleanup_task(tid)

    def test_search_empty_query_returns_422(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=")
            assert res.status_code == 422
        finally:
            _cleanup_task(tid)

    def test_search_missing_query_param_returns_422(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}")
            assert res.status_code == 422
        finally:
            _cleanup_task(tid)

    def test_search_limit_default_is_20(self):
        tid = _tid()
        segments = [{"start": i, "end": i + 1, "text": f"word {i}"} for i in range(30)]
        _create_task_with_output(tid, segments)
        try:
            res = client.get(f"/search/{tid}?q=word")
            data = res.json()
            assert data["total_matches"] == 30
            assert len(data["matches"]) == 20
        finally:
            _cleanup_task(tid)

    def test_search_limit_parameter_works(self):
        tid = _tid()
        segments = [{"start": i, "end": i + 1, "text": f"word {i}"} for i in range(10)]
        _create_task_with_output(tid, segments)
        try:
            res = client.get(f"/search/{tid}?q=word&limit=5")
            data = res.json()
            assert data["total_matches"] == 10
            assert len(data["matches"]) == 5
        finally:
            _cleanup_task(tid)

    def test_search_limit_1_returns_single_match(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=Hello&limit=1")
            data = res.json()
            assert len(data["matches"]) == 1
        finally:
            _cleanup_task(tid)

    def test_search_no_matches_returns_empty(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=nonexistentword")
            data = res.json()
            assert data["total_matches"] == 0
            assert data["matches"] == []
        finally:
            _cleanup_task(tid)

    def test_search_in_long_text(self):
        tid = _tid()
        segments = [{"start": 0, "end": 60, "text": "This is a very long segment with many words " * 20}]
        _create_task_with_output(tid, segments)
        try:
            res = client.get(f"/search/{tid}?q=long+segment")
            data = res.json()
            assert data["total_matches"] == 1
        finally:
            _cleanup_task(tid)

    def test_search_special_characters_handled(self):
        tid = _tid()
        segments = [{"start": 0, "end": 1, "text": "Hello, world! (test) [brackets] & more"}]
        _create_task_with_output(tid, segments)
        try:
            res = client.get(f"/search/{tid}?q=(test)")
            data = res.json()
            assert data["total_matches"] == 1
        finally:
            _cleanup_task(tid)

    def test_search_query_echoed_in_response(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.get(f"/search/{tid}?q=Hello")
            assert res.json()["query"] == "Hello"
        finally:
            _cleanup_task(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EDIT ENDPOINT — PUT /subtitles/{task_id}/{segment_index}
# ══════════════════════════════════════════════════════════════════════════════


class TestEditSubtitleSegment:
    """Tests for PUT /subtitles/{task_id}/{segment_index}."""

    def test_edit_segment_returns_200(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/0", json={"text": "Updated text"})
            assert res.status_code == 200
        finally:
            _cleanup_task(tid)

    def test_edit_returns_404_for_nonexistent_task(self):
        res = client.put("/subtitles/nonexistent-task/0", json={"text": "Updated"})
        assert res.status_code == 404

    def test_edit_returns_400_for_active_task(self):
        tid = _tid()
        state.tasks[tid] = {
            "status": "transcribing",
            "filename": "t.mp4",
            "session_id": "",
            "created_at": "2026-01-01T00:00:00",
        }
        try:
            res = client.put(f"/subtitles/{tid}/0", json={"text": "Updated"})
            assert res.status_code == 400
        finally:
            state.tasks.pop(tid, None)

    def test_edit_returns_400_for_empty_text(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/0", json={"text": ""})
            assert res.status_code == 400
        finally:
            _cleanup_task(tid)

    def test_edit_returns_400_for_whitespace_only_text(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/0", json={"text": "   "})
            assert res.status_code == 400
        finally:
            _cleanup_task(tid)

    def test_edit_returns_400_for_out_of_range_index(self):
        tid = _tid()
        _create_task_with_output(tid)  # 3 segments (0, 1, 2)
        try:
            res = client.put(f"/subtitles/{tid}/99", json={"text": "Updated"})
            assert res.status_code == 400
        finally:
            _cleanup_task(tid)

    def test_edit_response_includes_old_and_new_text(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/0", json={"text": "New text"})
            data = res.json()
            assert "old_text" in data
            assert "new_text" in data
            assert data["old_text"] == "Hello world"
            assert data["new_text"] == "New text"
        finally:
            _cleanup_task(tid)

    def test_edit_persists_in_json_file(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            client.put(f"/subtitles/{tid}/0", json={"text": "Persisted edit"})
            # Verify by reading the JSON file
            json_path = OUTPUT_DIR / f"{tid}.json"
            segments = json.loads(json_path.read_text())
            assert segments[0]["text"] == "Persisted edit"
        finally:
            _cleanup_task(tid)

    def test_edit_regenerates_srt_file(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            client.put(f"/subtitles/{tid}/0", json={"text": "Updated SRT"})
            srt_content = (OUTPUT_DIR / f"{tid}.srt").read_text()
            assert "Updated SRT" in srt_content
        finally:
            _cleanup_task(tid)

    def test_edit_regenerates_vtt_file(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            client.put(f"/subtitles/{tid}/0", json={"text": "Updated VTT"})
            vtt_content = (OUTPUT_DIR / f"{tid}.vtt").read_text()
            assert "Updated VTT" in vtt_content
        finally:
            _cleanup_task(tid)

    def test_edit_negative_index_returns_400(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/-1", json={"text": "Updated"})
            assert res.status_code == 400
        finally:
            _cleanup_task(tid)

    def test_edit_very_long_text_accepted(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            long_text = "A" * 5000
            res = client.put(f"/subtitles/{tid}/0", json={"text": long_text})
            assert res.status_code == 200
            assert res.json()["new_text"] == long_text
        finally:
            _cleanup_task(tid)

    def test_edit_second_segment(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            res = client.put(f"/subtitles/{tid}/1", json={"text": "Edited second"})
            assert res.status_code == 200
            assert res.json()["old_text"] == "Testing search"
            assert res.json()["new_text"] == "Edited second"
        finally:
            _cleanup_task(tid)

    def test_edit_last_segment(self):
        tid = _tid()
        _create_task_with_output(tid)  # 3 segments
        try:
            res = client.put(f"/subtitles/{tid}/2", json={"text": "Edited last"})
            assert res.status_code == 200
            assert res.json()["old_text"] == "Another segment"
        finally:
            _cleanup_task(tid)

    def test_edit_preserves_other_segments(self):
        tid = _tid()
        _create_task_with_output(tid)
        try:
            client.put(f"/subtitles/{tid}/0", json={"text": "Changed first"})
            json_path = OUTPUT_DIR / f"{tid}.json"
            segments = json.loads(json_path.read_text())
            assert segments[0]["text"] == "Changed first"
            assert segments[1]["text"] == "Testing search"
            assert segments[2]["text"] == "Another segment"
        finally:
            _cleanup_task(tid)

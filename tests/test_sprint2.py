"""Tests for Sprint 2 features: subtitle editor, task queue, batch, responsive."""

import pytest
from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app
from app.routes.subtitles import _parse_srt, _parse_timestamp
from app.utils.srt import segments_to_srt, segments_to_vtt

client = TestClient(app, base_url="https://testserver")

SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": "Hello world"},
    {"start": 3.0, "end": 5.5, "text": "How are you"},
    {"start": 6.0, "end": 8.0, "text": "Goodbye"},
]


# ── S2-1: Subtitle Editor API ──


class TestSubtitlesGet:
    def test_unknown_task_404(self):
        assert client.get("/subtitles/nonexistent").status_code == 404

    def test_not_done_returns_400(self):
        original = state.tasks.copy()
        state.tasks["test-edit-001"] = {"status": "transcribing"}
        try:
            assert client.get("/subtitles/test-edit-001").status_code == 400
        finally:
            state.tasks.clear()
            state.tasks.update(original)

    def test_done_task_returns_segments(self):
        original = state.tasks.copy()
        task_id = "test-edit-002"
        state.tasks[task_id] = {"status": "done", "filename": "test.mp4"}
        srt_path = OUTPUT_DIR / f"{task_id}.srt"
        OUTPUT_DIR.mkdir(exist_ok=True)
        srt_path.write_text(segments_to_srt(SAMPLE_SEGMENTS), encoding="utf-8")
        try:
            res = client.get(f"/subtitles/{task_id}")
            assert res.status_code == 200
            data = res.json()
            assert len(data["segments"]) == 3
            assert data["segments"][0]["text"] == "Hello world"
        finally:
            srt_path.unlink(missing_ok=True)
            state.tasks.clear()
            state.tasks.update(original)


class TestSubtitlesPut:
    def test_update_regenerates_files(self):
        original = state.tasks.copy()
        task_id = "test-edit-003"
        state.tasks[task_id] = {"status": "done", "filename": "test.mp4", "segments": 3}
        OUTPUT_DIR.mkdir(exist_ok=True)
        srt_path = OUTPUT_DIR / f"{task_id}.srt"
        vtt_path = OUTPUT_DIR / f"{task_id}.vtt"
        srt_path.write_text(segments_to_srt(SAMPLE_SEGMENTS), encoding="utf-8")
        vtt_path.write_text(segments_to_vtt(SAMPLE_SEGMENTS), encoding="utf-8")
        try:
            edited = [
                {"start": 0.0, "end": 3.0, "text": "Edited text"},
                {"start": 4.0, "end": 6.0, "text": "Second segment"},
            ]
            res = client.put(f"/subtitles/{task_id}", json={"segments": edited})
            assert res.status_code == 200
            assert res.json()["segments"] == 2

            # Verify files were regenerated
            new_srt = srt_path.read_text(encoding="utf-8")
            assert "Edited text" in new_srt
            new_vtt = vtt_path.read_text(encoding="utf-8")
            assert "Edited text" in new_vtt
            assert new_vtt.startswith("WEBVTT")
        finally:
            srt_path.unlink(missing_ok=True)
            vtt_path.unlink(missing_ok=True)
            state.tasks.clear()
            state.tasks.update(original)

    def test_update_unknown_task_404(self):
        res = client.put("/subtitles/nonexistent", json={"segments": []})
        assert res.status_code == 404


class TestSrtParser:
    def test_parse_simple_srt(self):
        srt = segments_to_srt(SAMPLE_SEGMENTS)
        segments = _parse_srt(srt)
        assert len(segments) == 3
        assert segments[0]["text"] == "Hello world"
        assert segments[2]["text"] == "Goodbye"

    def test_parse_timestamp(self):
        assert _parse_timestamp("00:01:30,500") == 90.5
        assert _parse_timestamp("01:00:00,000") == 3600.0
        assert _parse_timestamp("00:00:00,000") == 0.0

    def test_parse_timestamp_dot_format(self):
        assert _parse_timestamp("00:01:30.500") == 90.5

    def test_parse_empty_srt(self):
        assert _parse_srt("") == []

    def test_roundtrip(self):
        """Generate SRT, parse it, regenerate - text should match."""
        srt1 = segments_to_srt(SAMPLE_SEGMENTS)
        parsed = _parse_srt(srt1)
        segments_to_srt(parsed)
        # Text content should be identical
        for orig, parsed_seg in zip(SAMPLE_SEGMENTS, parsed):
            assert orig["text"] == parsed_seg["text"]


# ── S2-6: Task Queue API ──


class TestTasksEndpoint:
    def test_returns_tasks_list(self):
        res = client.get("/tasks")
        assert res.status_code == 200
        data = res.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_includes_task_fields(self):
        original = state.tasks.copy()
        state.tasks["test-queue-001"] = {
            "status": "done",
            "percent": 100,
            "filename": "video.mp4",
            "message": "Done!",
            "model_size": "large",
            "device": "CUDA",
            "language": "en",
            "segments": 10,
        }
        try:
            res = client.get("/tasks")
            tasks = res.json()["tasks"]
            t = next(t for t in tasks if t["task_id"] == "test-queue-001")
            assert t["status"] == "done"
            assert t["filename"] == "video.mp4"
            assert t["segments"] == 10
        finally:
            state.tasks.clear()
            state.tasks.update(original)

    def test_empty_when_no_tasks(self):
        original = state.tasks.copy()
        state.tasks.clear()
        try:
            res = client.get("/tasks")
            assert res.json()["tasks"] == []
        finally:
            state.tasks.clear()
            state.tasks.update(original)


# ── S2-4: Mobile Responsive (template check) ──


class TestResponsiveTemplate:
    def test_template_contains_viewport_meta(self):
        res = client.get("/")
        assert 'name="viewport"' in res.text

    @pytest.mark.skip(reason="Frontend migrated to React")
    def test_template_contains_media_queries(self):
        res = client.get("/")
        assert "@media" in res.text
        assert "max-width: 600px" in res.text

    @pytest.mark.skip(reason="Frontend migrated to React")
    def test_template_has_batch_support(self):
        res = client.get("/")
        assert "multiple" in res.text
        assert "handleBatch" in res.text


# ── S2-5: Drag-and-Drop ──


@pytest.mark.skip(reason="Frontend migrated to React")
class TestDragDropFeedback:
    def test_template_has_drag_counter(self):
        res = client.get("/")
        assert "dragCounter" in res.text

    def test_template_has_file_preview(self):
        res = client.get("/")
        assert "drop-zone-file-preview" in res.text


# ── S2-1: Editor in template ──


@pytest.mark.skip(reason="Frontend migrated to React")
class TestEditorTemplate:
    def test_template_has_editor_section(self):
        res = client.get("/")
        assert "editorSection" in res.text
        assert "Edit Subtitles" in res.text

    def test_template_has_save_edits(self):
        res = client.get("/")
        assert "saveEdits" in res.text


# ── S2-2: Video preview in template ──


@pytest.mark.skip(reason="Frontend migrated to React")
class TestVideoPreviewTemplate:
    def test_template_has_video_player(self):
        res = client.get("/")
        assert "videoPlayer" in res.text
        assert "subtitleTrack" in res.text

    def test_template_has_preview_button(self):
        res = client.get("/")
        assert "Preview with Video" in res.text

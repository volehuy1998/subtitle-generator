"""Phase Lumen L16 — Advanced download, preview, and bulk ZIP tests.

Tests GET /preview/{task_id}, GET /download/{task_id}/all, and
download completeness across SRT/VTT/JSON formats.
— Scout (QA Lead)
"""

import json
import uuid
import zipfile
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.config import OUTPUT_DIR
from app.main import app

client = TestClient(app, base_url="https://testserver")

# Sample subtitle content
SRT_CONTENT = "1\n00:00:00,000 --> 00:00:01,000\nTest\n\n"
VTT_CONTENT = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nTest\n\n"
JSON_CONTENT_LIST = [{"start": 0, "end": 1, "text": "Test"}]
JSON_CONTENT = json.dumps(JSON_CONTENT_LIST)

MULTI_SEGMENT_JSON = json.dumps([{"start": i, "end": i + 1, "text": f"Segment {i + 1}"} for i in range(20)])


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
        for ext in ("srt", "vtt", "json"):
            f = OUTPUT_DIR / f"{tid}.{ext}"
            if f.exists():
                f.unlink()


def _create_done_task_with_output(task_id=None, filename="test_video.mp4"):
    """Create a done task with all three output files."""
    tid = _add_task(task_id=task_id, status="done", filename=filename)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / f"{tid}.srt").write_text(SRT_CONTENT, encoding="utf-8")
    (OUTPUT_DIR / f"{tid}.vtt").write_text(VTT_CONTENT, encoding="utf-8")
    (OUTPUT_DIR / f"{tid}.json").write_text(JSON_CONTENT, encoding="utf-8")
    return tid


def _create_output_file(task_id, fmt, content):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{task_id}.{fmt}"
    path.write_text(content, encoding="utf-8")
    return path


# ══════════════════════════════════════════════════════════════════════════════
# PREVIEW ENDPOINT — GET /preview/{task_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestPreviewEndpoint:
    """Test GET /preview/{task_id} for subtitle preview."""

    def test_preview_returns_200_for_done_task(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/preview/{tid}")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_preview_returns_404_for_nonexistent_task(self):
        res = client.get("/preview/nonexistent-task-id")
        assert res.status_code == 404

    def test_preview_returns_400_for_active_task(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.get(f"/preview/{tid}")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_preview_response_has_total_segments_key(self):
        tid = _create_done_task_with_output()
        try:
            data = client.get(f"/preview/{tid}").json()
            assert "total_segments" in data
        finally:
            _cleanup(tid)

    def test_preview_response_has_preview_limit_key(self):
        tid = _create_done_task_with_output()
        try:
            data = client.get(f"/preview/{tid}").json()
            assert "preview_limit" in data
        finally:
            _cleanup(tid)

    def test_preview_response_has_segments_key(self):
        tid = _create_done_task_with_output()
        try:
            data = client.get(f"/preview/{tid}").json()
            assert "segments" in data
        finally:
            _cleanup(tid)

    def test_preview_segments_is_array(self):
        tid = _create_done_task_with_output()
        try:
            data = client.get(f"/preview/{tid}").json()
            assert isinstance(data["segments"], list)
        finally:
            _cleanup(tid)

    def test_preview_default_limit_is_10(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            data = client.get(f"/preview/{tid}").json()
            assert data["preview_limit"] == 10
            assert len(data["segments"]) == 10
        finally:
            _cleanup(tid)

    def test_preview_custom_limit_5(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            data = client.get(f"/preview/{tid}?limit=5").json()
            assert data["preview_limit"] == 5
            assert len(data["segments"]) == 5
        finally:
            _cleanup(tid)

    def test_preview_limit_1_returns_single_segment(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            data = client.get(f"/preview/{tid}?limit=1").json()
            assert len(data["segments"]) == 1
        finally:
            _cleanup(tid)

    def test_preview_limit_100_is_accepted(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            res = client.get(f"/preview/{tid}?limit=100")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_preview_segments_have_required_fields(self):
        tid = _create_done_task_with_output()
        try:
            data = client.get(f"/preview/{tid}").json()
            for seg in data["segments"]:
                assert "start" in seg
                assert "end" in seg
                assert "text" in seg
        finally:
            _cleanup(tid)

    def test_preview_respects_limit(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            data = client.get(f"/preview/{tid}?limit=3").json()
            assert len(data["segments"]) <= 3
        finally:
            _cleanup(tid)

    def test_preview_total_segments_count_accurate(self):
        tid = _add_task(status="done")
        _create_output_file(tid, "json", MULTI_SEGMENT_JSON)
        try:
            data = client.get(f"/preview/{tid}?limit=5").json()
            assert data["total_segments"] == 20
        finally:
            _cleanup(tid)

    def test_preview_no_json_file_returns_404(self):
        tid = _add_task(status="done")
        # Don't create any output files
        try:
            res = client.get(f"/preview/{tid}")
            assert res.status_code == 404
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# BULK DOWNLOAD — GET /download/{task_id}/all
# ══════════════════════════════════════════════════════════════════════════════


class TestBulkDownload:
    """Test GET /download/{task_id}/all for ZIP archive download."""

    def test_bulk_returns_200_for_done_task(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}/all")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_bulk_returns_404_for_nonexistent_task(self):
        res = client.get("/download/nonexistent-task-id/all")
        assert res.status_code == 404

    def test_bulk_returns_400_for_active_task(self):
        tid = _add_task(status="transcribing")
        try:
            res = client.get(f"/download/{tid}/all")
            assert res.status_code == 400
        finally:
            _cleanup(tid)

    def test_bulk_content_type_is_zip(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}/all")
            assert "application/zip" in res.headers["content-type"]
        finally:
            _cleanup(tid)

    def test_bulk_content_disposition_has_filename(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}/all")
            cd = res.headers.get("content-disposition", "")
            assert "filename=" in cd
        finally:
            _cleanup(tid)

    def test_bulk_filename_contains_original_stem(self):
        tid = _create_done_task_with_output(filename="my_lecture.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            cd = res.headers.get("content-disposition", "")
            assert "my_lecture" in cd
        finally:
            _cleanup(tid)

    def test_bulk_zip_contains_srt(self):
        tid = _create_done_task_with_output(filename="video.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            names = zf.namelist()
            assert any(n.endswith(".srt") for n in names)
        finally:
            _cleanup(tid)

    def test_bulk_zip_contains_vtt(self):
        tid = _create_done_task_with_output(filename="video.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            names = zf.namelist()
            assert any(n.endswith(".vtt") for n in names)
        finally:
            _cleanup(tid)

    def test_bulk_zip_contains_json(self):
        tid = _create_done_task_with_output(filename="video.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            names = zf.namelist()
            assert any(n.endswith(".json") for n in names)
        finally:
            _cleanup(tid)

    def test_bulk_zip_is_valid(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            # testzip returns None if all files are OK
            assert zf.testzip() is None
        finally:
            _cleanup(tid)

    def test_bulk_zip_files_use_original_stem(self):
        tid = _create_done_task_with_output(filename="interview.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            names = zf.namelist()
            assert "interview.srt" in names
            assert "interview.vtt" in names
            assert "interview.json" in names
        finally:
            _cleanup(tid)

    def test_bulk_zip_srt_content_valid(self):
        tid = _create_done_task_with_output(filename="clip.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            srt_data = zf.read("clip.srt").decode("utf-8")
            assert "Test" in srt_data
        finally:
            _cleanup(tid)

    def test_bulk_zip_json_content_valid(self):
        tid = _create_done_task_with_output(filename="clip.mp4")
        try:
            res = client.get(f"/download/{tid}/all")
            zf = zipfile.ZipFile(BytesIO(res.content))
            json_data = json.loads(zf.read("clip.json").decode("utf-8"))
            assert isinstance(json_data, list)
            assert json_data[0]["text"] == "Test"
        finally:
            _cleanup(tid)

    def test_bulk_returns_404_when_no_output_files(self):
        tid = _add_task(status="done")
        try:
            res = client.get(f"/download/{tid}/all")
            assert res.status_code == 404
        finally:
            _cleanup(tid)

    def test_bulk_partial_files_still_works(self):
        """If only SRT exists (no VTT/JSON), ZIP should still be created."""
        tid = _add_task(status="done", filename="partial.mp4")
        _create_output_file(tid, "srt", SRT_CONTENT)
        try:
            res = client.get(f"/download/{tid}/all")
            assert res.status_code == 200
            zf = zipfile.ZipFile(BytesIO(res.content))
            assert len(zf.namelist()) >= 1
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD COMPLETENESS
# ══════════════════════════════════════════════════════════════════════════════


class TestDownloadCompleteness:
    """Test that all formats are downloadable and correct after task completes."""

    def test_all_three_formats_available(self):
        tid = _create_done_task_with_output()
        try:
            for fmt in ("srt", "vtt", "json"):
                res = client.get(f"/download/{tid}?format={fmt}")
                assert res.status_code == 200, f"Format {fmt} returned {res.status_code}"
        finally:
            _cleanup(tid)

    def test_srt_download_content_type(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}?format=srt")
            ct = res.headers["content-type"]
            assert "text/plain" in ct or "text/srt" in ct
        finally:
            _cleanup(tid)

    def test_vtt_download_content_type(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            ct = res.headers["content-type"]
            assert "text/vtt" in ct or "text/plain" in ct
        finally:
            _cleanup(tid)

    def test_json_download_content_type(self):
        tid = _create_done_task_with_output()
        try:
            res = client.get(f"/download/{tid}?format=json")
            ct = res.headers["content-type"]
            assert "application/json" in ct
        finally:
            _cleanup(tid)

    def test_download_nonexistent_task_returns_404(self):
        fake_id = str(uuid.uuid4())
        for fmt in ("srt", "vtt", "json"):
            res = client.get(f"/download/{fake_id}?format={fmt}")
            assert res.status_code == 404, f"Format {fmt} should 404 for missing task"

    def test_concurrent_downloads_dont_interfere(self):
        tid1 = _create_done_task_with_output(filename="file_a.mp4")
        tid2 = _create_done_task_with_output(filename="file_b.mp4")
        try:
            res1 = client.get(f"/download/{tid1}?format=srt")
            res2 = client.get(f"/download/{tid2}?format=srt")
            assert res1.status_code == 200
            assert res2.status_code == 200
            cd1 = res1.headers.get("content-disposition", "")
            cd2 = res2.headers.get("content-disposition", "")
            assert "file_a.srt" in cd1
            assert "file_b.srt" in cd2
        finally:
            _cleanup(tid1, tid2)

    def test_download_filename_derives_from_original(self):
        tid = _create_done_task_with_output(filename="podcast_episode_42.mp3")
        try:
            for fmt in ("srt", "vtt", "json"):
                res = client.get(f"/download/{tid}?format={fmt}")
                cd = res.headers.get("content-disposition", "")
                assert f"podcast_episode_42.{fmt}" in cd, f"Filename mismatch for {fmt}"
        finally:
            _cleanup(tid)

    def test_empty_transcription_produces_valid_srt(self):
        tid = _add_task(status="done", filename="empty.mp4")
        _create_output_file(tid, "srt", "")
        try:
            res = client.get(f"/download/{tid}?format=srt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_empty_transcription_produces_valid_vtt(self):
        tid = _add_task(status="done", filename="empty.mp4")
        _create_output_file(tid, "vtt", "WEBVTT\n\n")
        try:
            res = client.get(f"/download/{tid}?format=vtt")
            assert res.status_code == 200
        finally:
            _cleanup(tid)

    def test_empty_transcription_produces_valid_json(self):
        tid = _add_task(status="done", filename="empty.mp4")
        _create_output_file(tid, "json", "[]")
        try:
            res = client.get(f"/download/{tid}?format=json")
            assert res.status_code == 200
            data = json.loads(res.text)
            assert data == []
        finally:
            _cleanup(tid)

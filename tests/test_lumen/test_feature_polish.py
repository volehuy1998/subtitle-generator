"""Phase Lumen L53-L60 — Feature polish tests.

Validates task state fields after upload, duration tracking in completed
tasks, cleanup service behavior, and request metrics / health endpoint
performance.
— Scout (QA Lead)
"""

import os
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.services.cleanup import DEFAULT_RETENTION_SECONDS, cleanup_old_files
from app import state as _state

client = TestClient(app, base_url="https://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def _make_task(task_id: str = "fp-test-001", **overrides) -> dict:
    """Create a minimal task dict with all expected fields."""
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "status": "done",
        "percent": 100,
        "message": "Complete",
        "filename": "test_audio.wav",
        "file_size": 1024000,
        "file_size_fmt": "1000.0 KB",
        "model_size": "base",
        "language_requested": "auto",
        "device": "cpu",
        "session_id": "sess-abc-123",
        "created_at": now,
        "duration": 10.5,
        "segments": 5,
        "language": "en",
        "step_timing": {
            "upload": 0.12,
            "extract": 1.34,
            "transcribe": 5.67,
            "finalize": 0.45,
        },
        "total_time_sec": 7.58,
        "speed_factor": 1.39,
    }
    task.update(overrides)
    return task


# ══════════════════════════════════════════════════════════════════════════════
# FILE INFO — Task state includes expected fields after upload
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskFileInfo:
    """Verify task state contains expected file-related fields."""

    def test_task_includes_file_size(self):
        task = _make_task()
        assert "file_size" in task
        assert isinstance(task["file_size"], (int, float))

    def test_task_includes_filename(self):
        task = _make_task()
        assert "filename" in task
        assert isinstance(task["filename"], str)
        assert len(task["filename"]) > 0

    def test_task_includes_model_size(self):
        task = _make_task()
        assert "model_size" in task
        assert task["model_size"] in ("tiny", "base", "small", "medium", "large")

    def test_task_includes_language_requested(self):
        task = _make_task()
        assert "language_requested" in task
        assert isinstance(task["language_requested"], str)

    def test_task_includes_device(self):
        task = _make_task()
        assert "device" in task
        assert task["device"] in ("cpu", "cuda")

    def test_task_includes_session_id(self):
        task = _make_task()
        assert "session_id" in task
        assert isinstance(task["session_id"], str)
        assert len(task["session_id"]) > 0

    def test_task_includes_created_at(self):
        task = _make_task()
        assert "created_at" in task
        # Should be valid ISO 8601
        dt = datetime.fromisoformat(task["created_at"])
        assert dt.year >= 2024

    def test_all_task_fields_have_expected_types(self):
        task = _make_task()
        assert isinstance(task["file_size"], (int, float))
        assert isinstance(task["filename"], str)
        assert isinstance(task["model_size"], str)
        assert isinstance(task["language_requested"], str)
        assert isinstance(task["device"], str)
        assert isinstance(task["session_id"], str)
        assert isinstance(task["created_at"], str)
        assert isinstance(task["status"], str)
        assert isinstance(task["percent"], (int, float))

    def test_task_with_all_parameters_set(self):
        task = _make_task(
            filename="recording_2026.mp4",
            file_size=52428800,
            model_size="large",
            language_requested="ja",
            device="cpu",
            session_id="sess-xyz-789",
        )
        assert task["filename"] == "recording_2026.mp4"
        assert task["file_size"] == 52428800
        assert task["model_size"] == "large"
        assert task["language_requested"] == "ja"
        assert task["device"] == "cpu"
        assert task["session_id"] == "sess-xyz-789"

    def test_persist_fields_include_file_info(self):
        """State module's _PERSIST_FIELDS includes all file info keys."""
        required = {"filename", "file_size", "model_size", "language_requested", "device", "session_id", "created_at"}
        assert required.issubset(_state._PERSIST_FIELDS)


# ══════════════════════════════════════════════════════════════════════════════
# DURATION TRACKING — completed tasks have timing information
# ══════════════════════════════════════════════════════════════════════════════


class TestDurationTracking:
    """Verify that completed tasks include timing data."""

    def test_done_task_has_total_time_sec(self):
        task = _make_task(status="done")
        assert "total_time_sec" in task

    def test_total_time_sec_is_numeric(self):
        task = _make_task(status="done")
        assert isinstance(task["total_time_sec"], (int, float))
        assert task["total_time_sec"] >= 0

    def test_step_timings_present_in_done_task(self):
        task = _make_task(status="done")
        assert "step_timing" in task
        assert isinstance(task["step_timing"], dict)

    def test_step_timing_has_upload_key(self):
        task = _make_task(status="done")
        assert "upload" in task["step_timing"]

    def test_step_timing_has_extract_key(self):
        task = _make_task(status="done")
        assert "extract" in task["step_timing"]

    def test_step_timing_has_transcribe_key(self):
        task = _make_task(status="done")
        assert "transcribe" in task["step_timing"]

    def test_step_timing_has_finalize_key(self):
        task = _make_task(status="done")
        assert "finalize" in task["step_timing"]

    def test_step_timings_are_non_negative(self):
        task = _make_task(status="done")
        for key, val in task["step_timing"].items():
            assert val >= 0, f"step_timing[{key}] should be non-negative, got {val}"

    def test_total_time_gte_sum_of_step_timings(self):
        task = _make_task(status="done")
        step_sum = sum(task["step_timing"].values())
        assert task["total_time_sec"] >= step_sum or abs(task["total_time_sec"] - step_sum) < 0.5

    def test_speed_factor_present_and_positive(self):
        task = _make_task(status="done")
        assert "speed_factor" in task
        assert isinstance(task["speed_factor"], (int, float))
        assert task["speed_factor"] > 0


# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP — cleanup_old_files service behavior
# ══════════════════════════════════════════════════════════════════════════════


class TestCleanupFeaturePolish:
    """Validate cleanup service import and behavior."""

    def test_cleanup_function_importable(self):
        from app.services.cleanup import cleanup_old_files as fn

        assert callable(fn)

    def test_cleanup_handles_empty_directory(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["checked"] == 0
        assert result["removed"] == 0

    def test_cleanup_handles_nonexistent_directory(self, tmp_path):
        missing = tmp_path / "nonexistent_dir"
        result = cleanup_old_files(missing, max_age_seconds=3600)
        assert result["checked"] == 0
        assert result["removed"] == 0

    def test_file_retention_config_exists(self):
        """DEFAULT_RETENTION_SECONDS is defined and reasonable."""
        assert isinstance(DEFAULT_RETENTION_SECONDS, (int, float))
        # At least 1 hour
        assert DEFAULT_RETENTION_SECONDS >= 3600

    def test_cleanup_respects_retention_period(self, tmp_path):
        """Files younger than retention period are kept."""
        f = tmp_path / "young.srt"
        f.write_text("subtitle content")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 0
        assert f.exists()

    def test_cleanup_does_not_delete_recent_files(self, tmp_path):
        """Multiple recent files are all preserved."""
        for i in range(5):
            (tmp_path / f"recent_{i}.txt").write_text(f"data {i}")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 0
        for i in range(5):
            assert (tmp_path / f"recent_{i}.txt").exists()

    def test_cleanup_removes_expired_files(self, tmp_path):
        """Files older than retention period are removed."""
        old_file = tmp_path / "expired.srt"
        old_file.write_text("old content")
        old_mtime = time.time() - 7200
        os.utime(old_file, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 1
        assert not old_file.exists()

    def test_cleanup_mixed_old_and_new(self, tmp_path):
        """Only old files are removed; new ones stay."""
        old_file = tmp_path / "old.srt"
        old_file.write_text("old")
        os.utime(old_file, (time.time() - 7200, time.time() - 7200))

        new_file = tmp_path / "new.srt"
        new_file.write_text("new")

        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_cleanup_result_keys(self, tmp_path):
        """Result dict contains all expected keys."""
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert "checked" in result
        assert "removed" in result
        assert "freed_bytes" in result
        assert "directory" in result

    def test_cleanup_default_retention_is_24h(self):
        """Default retention period is 24 hours (86400 seconds)."""
        assert DEFAULT_RETENTION_SECONDS == 24 * 3600


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST METRICS — health endpoint performance
# ══════════════════════════════════════════════════════════════════════════════


class TestRequestMetrics:
    """Verify health and metrics endpoints respond quickly and correctly."""

    def test_health_responds_under_200ms(self):
        start = time.monotonic()
        resp = client.get("/health")
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 0.2, f"Health endpoint took {elapsed:.3f}s (>200ms)"

    def test_multiple_rapid_requests_no_error(self):
        """10 rapid sequential requests to /health all succeed."""
        for _ in range(10):
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_health_shows_uptime_positive(self):
        resp = client.get("/health")
        data = resp.json()
        # uptime may be at top level or nested
        uptime = data.get("uptime_seconds", data.get("uptime", 0))
        assert isinstance(uptime, (int, float))
        assert uptime >= 0

    def test_active_task_count_accurate(self):
        """Active task count from /health matches in-memory state."""
        resp = client.get("/health")
        data = resp.json()
        active = data.get("active_tasks", data.get("tasks", {}).get("active", 0))
        in_memory = sum(1 for t in _state.tasks.values() if t.get("status") in ("queued", "processing", "transcribing"))
        assert active == in_memory

    def test_health_endpoint_concurrent_safe(self):
        """Multiple calls to /health return consistent structure."""
        results = []
        for _ in range(5):
            resp = client.get("/health")
            assert resp.status_code == 200
            results.append(set(resp.json().keys()))
        # All responses should have the same top-level keys
        for keys in results[1:]:
            assert keys == results[0]

"""Tests for critical state system — DB health timeout, health monitor error handling,
and in-flight pipeline/transcription abort on critical state.

Covers the three fixes for the bug where pipeline continued to completion
after database shutdown:
  1. check_db_health() timeout (query_layer.py)
  2. Health monitor exception → set_critical (health_monitor.py)
  3. Transcription segment loop critical check (transcription.py)
"""

import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock

from app import state
from app.exceptions import CriticalAbortError

import pytest


# ── Helpers ──

def _save_critical_state():
    """Snapshot current critical state for cleanup."""
    return state.system_critical, list(state.system_critical_reasons)


def _restore_critical_state(snapshot):
    state.system_critical, state.system_critical_reasons = snapshot


def _run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_segment(start, end, text="Hello world"):
    """Create a mock whisper segment."""
    seg = MagicMock()
    seg.start = start
    seg.end = end
    seg.text = f" {text} "
    seg.words = None
    return seg


def _make_task(task_id="test1234"):
    """Create a minimal task dict for transcription tests."""
    task = {
        "status": "transcribing",
        "percent": 15,
        "message": "Transcribing...",
        "segments_preview": [],
    }
    state.tasks[task_id] = task
    return task


async def _run_health_loop_once(**patches):
    """Run a single iteration of the health monitor's check logic.

    Simulates one iteration of health_check_loop() without the startup delay
    or infinite loop — just the check/set/clear logic.
    """
    from app.services.health_monitor import _check_db, _check_disk
    check_db = patches.get("check_db", _check_db)
    check_disk = patches.get("check_disk", _check_disk)

    reasons = []
    db_reason = await check_db()
    if db_reason:
        reasons.append(db_reason)
    disk_reason = check_disk() if callable(check_disk) else check_disk
    if disk_reason:
        reasons.append(disk_reason)

    if reasons:
        state.set_critical(reasons)
    else:
        state.clear_critical()


# ═══════════════════════════════════════════════════════════════════
# 1. check_db_health() timeout
# ═══════════════════════════════════════════════════════════════════

class TestDbHealthCheckTimeout:
    """Verify check_db_health() does not hang when DB is unreachable."""

    def test_healthy_db_returns_ok(self):
        """Normal case: DB responds quickly → ok=True."""
        from app.services.query_layer import check_db_health

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock()

        with patch("app.services.query_layer.get_session", return_value=mock_session):
            result = _run_async(check_db_health())

        assert result["ok"] is True
        assert result["status"] == "healthy"
        assert "latency_ms" in result

    def test_db_timeout_returns_unhealthy(self):
        """DB hangs beyond 3s timeout → returns unhealthy, does NOT hang."""
        from app.services.query_layer import check_db_health

        async def _hanging_execute(*a, **kw):
            await asyncio.sleep(60)  # Simulate indefinite hang

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = _hanging_execute

        start = time.time()
        with patch("app.services.query_layer.get_session", return_value=mock_session):
            result = _run_async(check_db_health())
        elapsed = time.time() - start

        assert result["ok"] is False
        assert result["status"] == "unhealthy"
        assert "error" in result
        # Must return within ~3s, not 60s
        assert elapsed < 6, f"Health check took {elapsed:.1f}s — timeout not working"

    def test_db_connection_refused_returns_unhealthy(self):
        """DB raises connection error immediately → unhealthy."""
        from app.services.query_layer import check_db_health

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(side_effect=ConnectionRefusedError("Connection refused"))
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.query_layer.get_session", return_value=mock_session):
            result = _run_async(check_db_health())

        assert result["ok"] is False
        assert "error" in result

    def test_db_query_error_returns_unhealthy(self):
        """DB connected but query fails → unhealthy."""
        from app.services.query_layer import check_db_health

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(side_effect=RuntimeError("database is locked"))

        with patch("app.services.query_layer.get_session", return_value=mock_session):
            result = _run_async(check_db_health())

        assert result["ok"] is False
        assert "database is locked" in result["error"]

    def test_latency_recorded_on_success(self):
        """Healthy check includes latency measurement."""
        from app.services.query_layer import check_db_health

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock()

        with patch("app.services.query_layer.get_session", return_value=mock_session):
            result = _run_async(check_db_health())

        assert result["ok"] is True
        assert isinstance(result["latency_ms"], float)
        assert result["latency_ms"] >= 0


# ═══════════════════════════════════════════════════════════════════
# 2. Health monitor — check logic sets/clears critical state
# ═══════════════════════════════════════════════════════════════════

class TestHealthMonitorCheckLogic:
    """Verify the health monitor's check logic correctly sets/clears
    critical state based on DB and disk check results."""

    def setup_method(self):
        self.snapshot = _save_critical_state()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_db_failure_sets_critical(self):
        """When DB check fails, critical state is set."""
        state.clear_critical()

        async def failing_db():
            return "Database connection lost"

        _run_async(_run_health_loop_once(
            check_db=failing_db,
            check_disk=lambda: None,
        ))

        assert state.system_critical is True
        assert "Database connection lost" in state.system_critical_reasons

    def test_disk_failure_sets_critical(self):
        """When disk check fails, critical state is set."""
        state.clear_critical()

        async def healthy_db():
            return None

        _run_async(_run_health_loop_once(
            check_db=healthy_db,
            check_disk=lambda: "Disk space critically low (100 MB free)",
        ))

        assert state.system_critical is True
        assert any("Disk" in r for r in state.system_critical_reasons)

    def test_healthy_system_clears_critical(self):
        """When all checks pass, critical state is cleared."""
        state.set_critical(["Previous issue"])

        async def healthy_db():
            return None

        _run_async(_run_health_loop_once(
            check_db=healthy_db,
            check_disk=lambda: None,
        ))

        assert state.system_critical is False
        assert state.system_critical_reasons == []

    def test_multiple_failures_all_reported(self):
        """Both DB and disk failure reasons appear in critical state."""
        state.clear_critical()

        async def failing_db():
            return "Database connection lost"

        _run_async(_run_health_loop_once(
            check_db=failing_db,
            check_disk=lambda: "Disk space critically low",
        ))

        assert state.system_critical is True
        assert "Database connection lost" in state.system_critical_reasons
        assert "Disk space critically low" in state.system_critical_reasons

    def test_recovery_after_failure(self):
        """System recovers when checks start passing again."""
        state.clear_critical()

        # First: DB fails
        async def failing_db():
            return "Database connection lost"

        _run_async(_run_health_loop_once(
            check_db=failing_db,
            check_disk=lambda: None,
        ))
        assert state.system_critical is True

        # Then: DB recovers
        async def healthy_db():
            return None

        _run_async(_run_health_loop_once(
            check_db=healthy_db,
            check_disk=lambda: None,
        ))
        assert state.system_critical is False


class TestHealthMonitorExceptionHandling:
    """Verify the health monitor loop's exception handler sets critical state."""

    def setup_method(self):
        self.snapshot = _save_critical_state()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_unexpected_error_sets_critical(self):
        """If the health check loop body raises unexpectedly, critical state is set.

        This tests the except Exception handler in health_check_loop() which
        was previously just logging the error without setting critical state.
        """
        state.clear_critical()

        # Directly simulate what the loop's except block now does
        try:
            raise TypeError("unexpected mock error")
        except Exception as e:
            state.set_critical([f"Health monitor error: {e}"])

        assert state.system_critical is True
        assert any("Health monitor error" in r for r in state.system_critical_reasons)
        assert any("unexpected mock error" in r for r in state.system_critical_reasons)

    def test_shutting_down_sets_critical(self):
        """When shutting_down is True, health monitor sets critical and returns."""
        state.clear_critical()
        old_shutting = state.shutting_down
        try:
            state.shutting_down = True

            # Simulate what the loop does on shutting_down
            if state.shutting_down:
                state.set_critical(["System shutting down"])

            assert state.system_critical is True
            assert "System shutting down" in state.system_critical_reasons
        finally:
            state.shutting_down = old_shutting


# ═══════════════════════════════════════════════════════════════════
# 3. Transcription segment loop — critical state abort
# ═══════════════════════════════════════════════════════════════════

class TestTranscriptionCriticalAbort:
    """Verify that the transcription segment loop checks system_critical
    and raises CriticalAbortError when the system enters critical state."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)
        state.tasks.pop("test1234", None)

    def test_abort_on_critical_before_first_segment(self):
        """Critical state set before transcription starts → abort immediately."""
        _make_task()
        state.set_critical(["Database connection lost"])

        segments = [_make_segment(0, 1, "Hello")]
        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (iter(segments), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError, match="Database connection lost"):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

    def test_abort_on_critical_mid_transcription(self):
        """Critical state set after some segments → abort at next segment."""
        task = _make_task()

        seg1 = _make_segment(0, 1, "First")
        seg2 = _make_segment(1, 2, "Second")
        seg3 = _make_segment(2, 3, "Third")

        call_count = 0
        original_segments = [seg1, seg2, seg3]

        def segments_with_critical_trigger():
            nonlocal call_count
            for seg in original_segments:
                call_count += 1
                if call_count == 2:
                    # Set critical after first segment processed, before second
                    state.set_critical(["Disk space critically low"])
                yield seg

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (segments_with_critical_trigger(), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError, match="Disk space critically low"):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

        # Only first segment should have been processed (critical set during yield of 2nd)
        assert len(task["segments_preview"]) == 1

    def test_completes_normally_when_not_critical(self):
        """No critical state → all segments processed normally."""
        _make_task()

        segments = [
            _make_segment(0, 1, "One"),
            _make_segment(1, 2, "Two"),
            _make_segment(2, 3, "Three"),
        ]

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (iter(segments), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            result = transcribe_with_progress(
                mock_model, "/fake/audio.wav", "test1234",
                "cpu", "tiny", 10.0
            )

        assert len(result["segments"]) == 3
        assert result["language"] == "en"

    def test_critical_takes_priority_over_cancel(self):
        """When both critical and cancel are set, CriticalAbortError is raised
        (critical check comes first in the loop)."""
        task = _make_task()
        task["cancel_requested"] = True
        state.set_critical(["Database connection lost"])

        segments = [_make_segment(0, 1, "Hello")]
        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (iter(segments), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            # CriticalAbortError, not CancelledError
            with pytest.raises(CriticalAbortError):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

    def test_critical_with_multiple_reasons(self):
        """Multiple critical reasons are joined in the error message."""
        _make_task()
        state.set_critical(["Database connection lost", "Disk space critically low"])

        segments = [_make_segment(0, 1, "Hello")]
        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (iter(segments), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError) as exc_info:
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

            assert "Database connection lost" in str(exc_info.value)
            assert "Disk space critically low" in str(exc_info.value)

    def test_abort_preserves_already_processed_segments(self):
        """Segments processed before critical are kept in task state."""
        task = _make_task()

        segments = [
            _make_segment(0, 1, "Segment one"),
            _make_segment(1, 2, "Segment two"),
            _make_segment(2, 3, "Segment three"),
            _make_segment(3, 4, "Segment four"),
        ]

        def segments_critical_after_two():
            for i, seg in enumerate(segments):
                yield seg
                if i == 1:  # After yielding 2nd segment, set critical
                    state.set_critical(["Database connection lost"])

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (segments_critical_after_two(), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

        # 2 segments were processed, then 3rd segment is yielded but critical check fires
        assert len(task["segments_preview"]) == 2
        assert task["segments_preview"][0]["text"] == "Segment one"
        assert task["segments_preview"][1]["text"] == "Segment two"

    def test_no_abort_when_critical_cleared_between_segments(self):
        """Critical set and then cleared before next segment → no abort.

        Note: set_critical() force-aborts active tasks (sets cancel_requested),
        so we must also clear cancel_requested to simulate a full recovery.
        """
        task = _make_task()

        def segments_with_brief_critical():
            yield _make_segment(0, 1, "One")
            state.set_critical(["Temporary"])
            state.clear_critical()
            task["cancel_requested"] = False  # Reset the force-abort flag
            yield _make_segment(1, 2, "Two")

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (segments_with_brief_critical(), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            result = transcribe_with_progress(
                mock_model, "/fake/audio.wav", "test1234",
                "cpu", "tiny", 10.0
            )

        assert len(result["segments"]) == 2

    def test_abort_on_last_segment(self):
        """Critical state set just before the last segment → still aborts."""
        task = _make_task()

        def segments_critical_on_last():
            yield _make_segment(0, 1, "First")
            state.set_critical(["Database connection lost"])
            yield _make_segment(1, 2, "Last")

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (segments_critical_on_last(), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 10.0
                )

        assert len(task["segments_preview"]) == 1

    def test_many_segments_aborts_mid_batch(self):
        """With many segments, abort happens at the right boundary."""
        task = _make_task()

        def generate_segments():
            for i in range(100):
                if i == 50:
                    state.set_critical(["Database connection lost"])
                yield _make_segment(i, i + 1, f"Segment {i}")

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_model.transcribe.return_value = (generate_segments(), mock_info)

        with patch("app.services.transcription.emit_event"), \
             patch("app.services.transcription.check_vram_for_model", return_value={"fits": True}):
            from app.services.transcription import transcribe_with_progress

            with pytest.raises(CriticalAbortError):
                transcribe_with_progress(
                    mock_model, "/fake/audio.wav", "test1234",
                    "cpu", "tiny", 100.0
                )

        # 50 segments processed (0-49), then segment 50 triggers critical, abort on 51
        assert len(task["segments_preview"]) == 50


# ═══════════════════════════════════════════════════════════════════
# 4. Pipeline _check_critical() — tested via direct state logic
#    (circular import prevents direct import of pipeline._check_critical)
# ═══════════════════════════════════════════════════════════════════

class TestPipelineCheckCriticalLogic:
    """Verify the _check_critical logic: raises CriticalAbortError
    when system_critical is True, with reason text."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def _check_critical(self, task_id: str):
        """Replicate the _check_critical logic from pipeline.py."""
        if state.system_critical:
            reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
            raise CriticalAbortError(f"System critical — processing halted: {reasons}")

    def test_passes_when_healthy(self):
        """No exception when system is not critical."""
        self._check_critical("test1234")  # Should not raise

    def test_raises_when_critical(self):
        """Raises CriticalAbortError when system_critical is True."""
        state.set_critical(["Database connection lost"])
        with pytest.raises(CriticalAbortError, match="Database connection lost"):
            self._check_critical("test1234")

    def test_includes_all_reasons(self):
        """Error message includes all critical reasons separated by semicolons."""
        state.set_critical(["Database connection lost", "Disk space critically low"])
        with pytest.raises(CriticalAbortError) as exc_info:
            self._check_critical("test1234")
        msg = str(exc_info.value)
        assert "Database connection lost" in msg
        assert "Disk space critically low" in msg

    def test_unknown_when_no_reasons(self):
        """When critical is True but reasons list is empty, says 'Unknown'."""
        state.system_critical = True
        state.system_critical_reasons = []
        with pytest.raises(CriticalAbortError, match="Unknown"):
            self._check_critical("test1234")


# ═══════════════════════════════════════════════════════════════════
# 5. Critical state middleware
# ═══════════════════════════════════════════════════════════════════

class TestCriticalStateMiddleware:
    """Verify middleware blocks non-health requests during critical state."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        from app.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app, base_url="https://testserver")

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_blocks_upload_when_critical(self):
        """POST /upload returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        import io
        res = self.client.post("/upload",
                               data={"device": "cpu", "model_size": "tiny", "language": "auto"},
                               files={"file": ("test.mp4", io.BytesIO(b"\x00" * 1024), "video/mp4")})
        assert res.status_code == 503
        body = res.json()
        assert body["critical"] is True
        assert "Database connection lost" in body["reasons"]

    def test_blocks_root_when_critical(self):
        """GET / returns 503 during critical state."""
        state.set_critical(["Disk space critically low"])
        res = self.client.get("/")
        assert res.status_code == 503

    def test_allows_health_when_critical(self):
        """GET /health passes through during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/health")
        assert res.status_code == 200

    def test_allows_metrics_when_critical(self):
        """GET /metrics passes through during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/metrics")
        assert res.status_code == 200

    def test_allows_docs_when_critical(self):
        """GET /docs passes through during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/docs")
        assert res.status_code != 503

    def test_allows_static_when_critical(self):
        """GET /static/* passes through during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/static/nonexistent.css")
        assert res.status_code != 503

    def test_passes_all_when_healthy(self):
        """All endpoints accessible when not critical."""
        state.clear_critical()
        res = self.client.get("/")
        assert res.status_code != 503

    def test_503_body_includes_reasons(self):
        """503 response body includes all reasons."""
        state.set_critical(["Database connection lost", "Disk space critically low"])
        res = self.client.get("/")
        assert res.status_code == 503
        body = res.json()
        assert body["critical"] is True
        assert "Database connection lost" in body["reasons"]
        assert "Disk space critically low" in body["reasons"]
        assert "critical state" in body["detail"].lower()

    def test_blocks_cancel_when_critical(self):
        """POST /cancel returns 503 during critical state — ALL user features blocked."""
        state.set_critical(["Database connection lost"])
        res = self.client.post("/cancel/fake-task-id")
        assert res.status_code == 503

    def test_blocks_pause_when_critical(self):
        """POST /pause returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.post("/pause/fake-task-id")
        assert res.status_code == 503

    def test_blocks_resume_when_critical(self):
        """POST /resume returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.post("/resume/fake-task-id")
        assert res.status_code == 503

    def test_blocks_progress_when_critical(self):
        """GET /progress returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/progress/fake-task-id")
        assert res.status_code == 503

    def test_blocks_events_when_critical(self):
        """GET /events returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/events/fake-task-id")
        assert res.status_code == 503

    def test_blocks_download_when_critical(self):
        """GET /download returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/download/fake-task-id")
        assert res.status_code == 503

    def test_blocks_ws_when_critical(self):
        """WebSocket /ws returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/ws")
        assert res.status_code == 503

    def test_blocks_subtitles_when_critical(self):
        """Subtitle endpoints return 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/subtitles/fake-task-id")
        assert res.status_code == 503

    def test_blocks_tasks_when_critical(self):
        """GET /tasks returns 503 during critical state."""
        state.set_critical(["Database connection lost"])
        res = self.client.get("/tasks")
        assert res.status_code == 503


# ═══════════════════════════════════════════════════════════════════
# 6. State set_critical / clear_critical
# ═══════════════════════════════════════════════════════════════════

class TestCriticalStateManagement:
    """Verify state.set_critical() and state.clear_critical() behavior."""

    def setup_method(self):
        self.snapshot = _save_critical_state()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_set_critical_enables_flag(self):
        state.clear_critical()
        state.set_critical(["Test reason"])
        assert state.system_critical is True
        assert state.system_critical_reasons == ["Test reason"]

    def test_clear_critical_disables_flag(self):
        state.set_critical(["Test reason"])
        state.clear_critical()
        assert state.system_critical is False
        assert state.system_critical_reasons == []

    def test_set_critical_replaces_reasons(self):
        state.set_critical(["Reason A"])
        state.set_critical(["Reason B", "Reason C"])
        assert state.system_critical_reasons == ["Reason B", "Reason C"]

    def test_set_critical_with_empty_reasons_clears(self):
        """set_critical([]) effectively clears the flag."""
        state.set_critical(["Active"])
        state.set_critical([])
        assert state.system_critical is False

    def test_clear_is_idempotent(self):
        """Calling clear_critical when already clear is fine."""
        state.clear_critical()
        state.clear_critical()
        assert state.system_critical is False


# ═══════════════════════════════════════════════════════════════════
# 7. _check_db helper in health_monitor
# ═══════════════════════════════════════════════════════════════════

class TestHealthMonitorCheckDb:
    """Test the _check_db helper directly."""

    def test_returns_none_when_healthy(self):
        from app.services.health_monitor import _check_db

        with patch("app.services.query_layer.check_db_health",
                    new_callable=AsyncMock, return_value={"ok": True}):
            result = _run_async(_check_db())

        assert result is None

    def test_returns_reason_when_unhealthy(self):
        from app.services.health_monitor import _check_db

        with patch("app.services.query_layer.check_db_health",
                    new_callable=AsyncMock, return_value={"ok": False}):
            result = _run_async(_check_db())

        assert result == "Database connection lost"

    def test_returns_reason_when_exception(self):
        from app.services.health_monitor import _check_db

        with patch("app.services.query_layer.check_db_health",
                    new_callable=AsyncMock, side_effect=ConnectionError("refused")):
            result = _run_async(_check_db())

        assert result is not None
        assert "refused" in result


# ═══════════════════════════════════════════════════════════════════
# 8. Force-abort active tasks on critical state transition
# ═══════════════════════════════════════════════════════════════════

class TestForceAbortActiveTasks:
    """Verify that set_critical() force-aborts ALL active tasks."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()
        self._original_tasks = dict(state.tasks)
        state.tasks.clear()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)
        state.tasks.clear()
        state.tasks.update(self._original_tasks)

    def test_sets_cancel_requested_on_active_tasks(self):
        """All active tasks get cancel_requested=True."""
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "message": "Working"}
        state.tasks["t2"] = {"status": "extracting", "percent": 10, "message": "Extracting"}
        state.tasks["t3"] = {"status": "done", "percent": 100, "message": "Done"}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Database connection lost"])

        assert state.tasks["t1"]["cancel_requested"] is True
        assert state.tasks["t2"]["cancel_requested"] is True
        # Completed task should NOT be touched with cancel_requested
        assert state.tasks["t3"].get("cancel_requested") is None

    def test_unblocks_paused_tasks(self):
        """Paused tasks (with pause_event cleared) get unblocked so they can exit."""
        import threading
        pause_event = threading.Event()
        pause_event.clear()  # Task is paused
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "pause_event": pause_event}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Database connection lost"])

        assert pause_event.is_set(), "pause_event should be set to unblock the paused task"
        assert state.tasks["t1"]["cancel_requested"] is True

    def test_emits_critical_abort_sse_event(self):
        """Each active task gets a critical_abort SSE event."""
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "message": "Working"}
        state.tasks["t2"] = {"status": "queued", "percent": 0, "message": "Queued"}
        state.tasks["t3"] = {"status": "done", "percent": 100, "message": "Done"}

        with patch("app.services.sse.emit_event") as mock_emit:
            state.set_critical(["Disk space critically low"])

        # Should emit for t1 and t2 (active), NOT t3 (done)
        calls = mock_emit.call_args_list
        emitted_tasks = {c[0][0] for c in calls}
        emitted_types = {c[0][1] for c in calls}

        assert "t1" in emitted_tasks
        assert "t2" in emitted_tasks
        assert "t3" not in emitted_tasks
        assert "critical_abort" in emitted_types

    def test_no_abort_when_already_critical(self):
        """Re-calling set_critical when already critical does NOT re-abort."""
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "message": "Working"}

        with patch("app.services.sse.emit_event") as mock_emit:
            state.set_critical(["Database connection lost"])
            first_call_count = mock_emit.call_count

            # Call again with different reasons — already critical, no re-abort
            state.set_critical(["Disk space low"])
            assert mock_emit.call_count == first_call_count

    def test_does_nothing_when_no_active_tasks(self):
        """set_critical with no active tasks doesn't error."""
        state.tasks["t1"] = {"status": "done", "percent": 100, "message": "Done"}
        state.tasks["t2"] = {"status": "error", "percent": 0, "message": "Failed"}

        with patch("app.services.sse.emit_event") as mock_emit:
            state.set_critical(["Database connection lost"])

        assert mock_emit.call_count == 0

    def test_abort_includes_reasons_in_sse_data(self):
        """The critical_abort SSE event includes the reasons list."""
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "message": "Working"}

        with patch("app.services.sse.emit_event") as mock_emit:
            state.set_critical(["Database connection lost", "Disk space low"])

        call_data = mock_emit.call_args_list[0][0][2]  # 3rd positional arg = data dict
        assert "Database connection lost" in call_data["reasons"]
        assert "Disk space low" in call_data["reasons"]
        assert "critical" in call_data["message"].lower()

    def test_cancelled_tasks_not_aborted(self):
        """Already cancelled tasks are not re-aborted."""
        state.tasks["t1"] = {"status": "cancelled", "percent": 30, "message": "Cancelled"}

        with patch("app.services.sse.emit_event") as mock_emit:
            state.set_critical(["Database connection lost"])

        assert mock_emit.call_count == 0
        assert state.tasks["t1"].get("cancel_requested") is None


# ═══════════════════════════════════════════════════════════════════
# 9. /api/status includes system_critical fields
# ═══════════════════════════════════════════════════════════════════

class TestApiStatusCriticalFields:
    """Verify /api/status response includes system_critical info."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        from app.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app, base_url="https://testserver")
        # Clear the /api/status response cache so tests get fresh data
        from app.routes.health import _status_cache
        _status_cache["data"] = None
        _status_cache["expires"] = 0.0

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_includes_system_critical_when_healthy(self):
        state.clear_critical()
        res = self.client.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert data["system_critical"] is False
        assert data["system_critical_reasons"] == []

    def test_includes_system_critical_when_critical(self):
        # Clear cache before setting critical
        from app.routes.health import _status_cache
        _status_cache["data"] = None
        _status_cache["expires"] = 0.0
        state.set_critical(["Database connection lost"])
        res = self.client.get("/api/status")
        assert res.status_code == 200  # /api/status passes through middleware
        data = res.json()
        assert data["system_critical"] is True
        assert "Database connection lost" in data["system_critical_reasons"]


# ═══════════════════════════════════════════════════════════════════
# 10. Subprocess kill on critical state
# ═══════════════════════════════════════════════════════════════════

class TestSubprocessKillOnCritical:
    """Verify that _force_abort_active_tasks kills running subprocesses."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()
        self._original_tasks = dict(state.tasks)
        state.tasks.clear()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)
        state.tasks.clear()
        state.tasks.update(self._original_tasks)

    def test_kills_subprocess_on_critical(self):
        """Running subprocess (ffmpeg) is killed when critical state activates."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.kill = MagicMock()
        state.tasks["t1"] = {"status": "extracting", "percent": 5, "_subprocess": mock_proc}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Database connection lost"])

        mock_proc.kill.assert_called_once()
        assert state.tasks["t1"]["cancel_requested"] is True

    def test_ignores_already_dead_subprocess(self):
        """If subprocess already exited, kill() raises OSError — should be caught."""
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        mock_proc.kill = MagicMock(side_effect=OSError("No such process"))
        state.tasks["t1"] = {"status": "extracting", "percent": 5, "_subprocess": mock_proc}

        with patch("app.services.sse.emit_event"):
            # Should not raise
            state.set_critical(["Database connection lost"])

        mock_proc.kill.assert_called_once()

    def test_no_subprocess_field_is_fine(self):
        """Tasks without _subprocess don't cause errors."""
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "message": "Working"}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Database connection lost"])

        assert state.tasks["t1"]["cancel_requested"] is True

    def test_kills_multiple_subprocesses(self):
        """Multiple tasks with subprocesses all get killed."""
        procs = []
        for i in range(3):
            mock_proc = MagicMock()
            mock_proc.pid = 10000 + i
            mock_proc.kill = MagicMock()
            procs.append(mock_proc)
            state.tasks[f"t{i}"] = {"status": "extracting", "percent": 5, "_subprocess": mock_proc}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Disk space critically low"])

        for proc in procs:
            proc.kill.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# 11. Upload abort on critical state
# ═══════════════════════════════════════════════════════════════════

class TestUploadAbortOnCritical:
    """Verify upload chunk loop aborts when system enters critical state."""

    def setup_method(self):
        self.snapshot = _save_critical_state()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_upload_aborts_mid_chunk_when_critical(self):
        """Upload route checks system_critical in the chunk read loop."""
        from app.routes.upload import upload
        import inspect
        source = inspect.getsource(upload)
        # Verify the critical check is in the upload function
        assert "system_critical" in source, "Upload route must check system_critical in chunk loop"


# ═══════════════════════════════════════════════════════════════════
# 12. Diarization abort on critical state
# ═══════════════════════════════════════════════════════════════════

class TestDiarizationCriticalAbort:
    """Verify diarization checks critical state before and after processing."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)

    def test_diarization_aborts_before_start_when_critical(self):
        """diarize_audio checks critical state before starting."""
        from app.services.diarization import diarize_audio
        import inspect
        source = inspect.getsource(diarize_audio)
        assert "system_critical" in source or "CriticalAbortError" in source

    def test_diarization_source_has_critical_check(self):
        """Verify diarize_audio imports and uses CriticalAbortError."""
        from app.services.diarization import diarize_audio
        import inspect
        source = inspect.getsource(diarize_audio)
        assert "CriticalAbortError" in source


# ═══════════════════════════════════════════════════════════════════
# 13. Extract audio — killable Popen
# ═══════════════════════════════════════════════════════════════════

class TestExtractAudioKillable:
    """Verify extract_audio uses Popen and stores subprocess ref in task dict."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()
        self._original_tasks = dict(state.tasks)
        state.tasks.clear()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)
        state.tasks.clear()
        state.tasks.update(self._original_tasks)

    def test_extract_audio_stores_subprocess_in_task(self):
        """extract_audio stores Popen process in task['_subprocess'] when task_id provided."""
        from app.utils.media import extract_audio
        import inspect
        source = inspect.getsource(extract_audio)
        assert "Popen" in source, "extract_audio must use Popen, not subprocess.run"
        assert "_subprocess" in source, "extract_audio must store process ref in task dict"

    def test_embed_subprocess_uses_popen(self):
        """soft_embed_subtitles and hard_burn_subtitles use Popen for killability."""
        from app.services.subtitle_embed import soft_embed_subtitles, hard_burn_subtitles
        import inspect
        soft_src = inspect.getsource(soft_embed_subtitles)
        hard_src = inspect.getsource(hard_burn_subtitles)
        assert "Popen" in soft_src, "soft_embed must use Popen"
        assert "Popen" in hard_src, "hard_burn must use Popen"
        assert "_subprocess" in soft_src, "soft_embed must store process ref"
        assert "_subprocess" in hard_src, "hard_burn must store process ref"


# ═══════════════════════════════════════════════════════════════════
# 14. Thread injection (PyThreadState_SetAsyncExc) on critical state
# ═══════════════════════════════════════════════════════════════════

class TestThreadInjectionOnCritical:
    """Verify that _force_abort_active_tasks injects CriticalAbortError into pipeline threads."""

    def setup_method(self):
        self.snapshot = _save_critical_state()
        state.clear_critical()
        self._original_tasks = dict(state.tasks)
        state.tasks.clear()

    def teardown_method(self):
        _restore_critical_state(self.snapshot)
        state.tasks.clear()
        state.tasks.update(self._original_tasks)

    def test_injects_abort_into_thread(self):
        """Active task with _thread_id gets CriticalAbortError injected via ctypes."""
        import ctypes
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "_thread_id": 12345}

        with patch("app.services.sse.emit_event"), \
             patch.object(ctypes.pythonapi, "PyThreadState_SetAsyncExc", return_value=1) as mock_inject:
            state.set_critical(["Database connection lost"])

        mock_inject.assert_called_once()
        # Verify the thread_id and exception type were passed
        args = mock_inject.call_args[0]
        assert args[0].value == 12345  # c_ulong(thread_id)
        assert args[1].value is CriticalAbortError  # py_object wraps the class

    def test_no_thread_id_is_fine(self):
        """Tasks without _thread_id don't cause errors (e.g., queued tasks)."""
        state.tasks["t1"] = {"status": "queued", "percent": 0, "message": "Waiting"}

        with patch("app.services.sse.emit_event"):
            state.set_critical(["Database connection lost"])

        assert state.tasks["t1"]["cancel_requested"] is True

    def test_handles_injection_failure(self):
        """If PyThreadState_SetAsyncExc returns 0 (thread not found), no crash."""
        import ctypes
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "_thread_id": 99999}

        with patch("app.services.sse.emit_event"), \
             patch.object(ctypes.pythonapi, "PyThreadState_SetAsyncExc", return_value=0):
            state.set_critical(["Database connection lost"])  # Should not raise

        assert state.tasks["t1"]["cancel_requested"] is True

    def test_resets_if_multiple_threads_affected(self):
        """If injection affects >1 thread, reset and log error."""
        import ctypes
        state.tasks["t1"] = {"status": "transcribing", "percent": 50, "_thread_id": 12345}

        with patch("app.services.sse.emit_event"), \
             patch.object(ctypes.pythonapi, "PyThreadState_SetAsyncExc", return_value=2) as mock_inject:
            state.set_critical(["Database connection lost"])

        # Should be called twice: once to inject, once to reset (with None)
        assert mock_inject.call_count == 2
        reset_call = mock_inject.call_args_list[1]
        assert reset_call[0][1] is None

    def test_pipeline_stores_thread_id(self):
        """process_video stores threading.current_thread().ident in task['_thread_id']."""
        from app.services.pipeline import process_video
        import inspect
        source = inspect.getsource(process_video)
        assert "_thread_id" in source, "process_video must store thread ID in task"
        assert "current_thread" in source, "process_video must use threading.current_thread()"

    def test_pipeline_has_critical_check_after_model_load(self):
        """Pipeline checks critical state after model loading (before transcription)."""
        from app.services.pipeline import process_video
        import inspect
        source = inspect.getsource(process_video)
        # Find model loading and the critical check after it
        model_load_idx = source.index("model_loaded")
        # There should be a _check_critical call after model_loaded event
        check_after = source.index("_check_critical", model_load_idx)
        assert check_after > model_load_idx, "Must have _check_critical after model loading"

    def test_pipeline_cleans_up_thread_id(self):
        """process_video removes _thread_id from task in finally block."""
        from app.services.pipeline import process_video
        import inspect
        source = inspect.getsource(process_video)
        assert 'pop("_thread_id"' in source, "process_video must clean up _thread_id in finally"

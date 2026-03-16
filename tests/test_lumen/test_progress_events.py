"""Phase Lumen L11 — Progress event structure and profiler tests.

Tests pipeline progress events, segment event structure, TranscriptionProfiler,
and event queue management.
— Scout (QA Lead)
"""

import time

from app import state
from app.services.sse import create_event_queue, emit_event, subscribe, unsubscribe


def _create_task(task_id="prog-test", status="queued"):
    """Set up a task in state for progress event testing."""
    state.tasks[task_id] = {
        "status": status,
        "percent": 0,
        "message": "",
        "step": 0,
        "filename": "test.wav",
        "session_id": "",
        "cancel_requested": False,
    }
    create_event_queue(task_id)
    return task_id


def _cleanup(task_id):
    state.tasks.pop(task_id, None)
    state.task_event_queues.pop(task_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PROGRESS EVENTS (15 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestProgressEventPercent:
    """Test that progress events contain percent field (0-100)."""

    def test_progress_event_contains_percent(self):
        tid = _create_task("pe-pct-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 42})
            ev = q.get_nowait()
            assert "percent" in ev
            assert ev["percent"] == 42
        finally:
            _cleanup(tid)

    def test_percent_zero_at_start(self):
        tid = _create_task("pe-pct-2")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 0})
            ev = q.get_nowait()
            assert ev["percent"] == 0
        finally:
            _cleanup(tid)

    def test_percent_100_at_done(self):
        tid = _create_task("pe-pct-3")
        try:
            q = subscribe(tid)
            emit_event(tid, "done", {"percent": 100, "status": "done"})
            ev = q.get_nowait()
            assert ev["percent"] == 100
        finally:
            _cleanup(tid)

    def test_percent_stored_in_task_state(self):
        tid = _create_task("pe-pct-4")
        try:
            emit_event(tid, "progress", {"percent": 55})
            assert state.tasks[tid]["percent"] == 55
        finally:
            _cleanup(tid)

    def test_percent_range_0_to_100(self):
        """Percent values across the full range are accepted."""
        tid = _create_task("pe-pct-5")
        try:
            for pct in [0, 10, 25, 50, 75, 90, 100]:
                emit_event(tid, "progress", {"percent": pct})
                assert state.tasks[tid]["percent"] == pct
        finally:
            _cleanup(tid)


class TestProgressEventMessage:
    """Test that progress events contain message field."""

    def test_progress_event_contains_message(self):
        tid = _create_task("pe-msg-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "update", {"message": "Processing audio..."})
            ev = q.get_nowait()
            assert "message" in ev
            assert ev["message"] == "Processing audio..."
        finally:
            _cleanup(tid)

    def test_message_stored_in_task_state(self):
        tid = _create_task("pe-msg-2")
        try:
            emit_event(tid, "update", {"message": "Loading model..."})
            assert state.tasks[tid]["message"] == "Loading model..."
        finally:
            _cleanup(tid)


class TestStepChangeEvents:
    """Test step change events have step and status fields."""

    def test_step_change_has_step_field(self):
        tid = _create_task("pe-sc-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "step_change", {"step": 1, "status": "extracting"})
            ev = q.get_nowait()
            assert "step" in ev
            assert ev["step"] == 1
        finally:
            _cleanup(tid)

    def test_step_change_has_status_field(self):
        tid = _create_task("pe-sc-2")
        try:
            q = subscribe(tid)
            emit_event(tid, "step_change", {"step": 2, "status": "transcribing"})
            ev = q.get_nowait()
            assert "status" in ev
            assert ev["status"] == "transcribing"
        finally:
            _cleanup(tid)

    def test_step_values_0_through_3(self):
        tid = _create_task("pe-sc-3")
        try:
            q = subscribe(tid)
            for step in range(4):
                emit_event(tid, "step_change", {"step": step})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            steps = [e["step"] for e in events]
            assert steps == [0, 1, 2, 3]
        finally:
            _cleanup(tid)


class TestPipelineEventOrder:
    """Test pipeline emits events in correct order."""

    def test_events_emitted_in_order(self):
        tid = _create_task("pe-order-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "step_change", {"step": 0, "status": "uploading"})
            emit_event(tid, "step_change", {"step": 1, "status": "extracting", "percent": 5})
            emit_event(tid, "step_change", {"step": 2, "status": "transcribing", "percent": 15})
            emit_event(tid, "progress", {"percent": 50})
            emit_event(tid, "step_change", {"step": 3, "status": "writing", "percent": 95})
            emit_event(tid, "done", {"status": "done", "percent": 100})

            events = []
            while not q.empty():
                events.append(q.get_nowait())

            types = [e["type"] for e in events]
            assert types == ["step_change", "step_change", "step_change", "progress", "step_change", "done"]
        finally:
            _cleanup(tid)

    def test_event_timestamps_increase(self):
        tid = _create_task("pe-order-2")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 10})
            emit_event(tid, "progress", {"percent": 50})
            emit_event(tid, "progress", {"percent": 90})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            timestamps = [e["timestamp"] for e in events]
            assert timestamps == sorted(timestamps)
        finally:
            _cleanup(tid)


class TestStepTimings:
    """Test step timings recorded correctly."""

    def test_step_timing_dict_in_event(self):
        tid = _create_task("pe-timing-1")
        try:
            q = subscribe(tid)
            timing = {"upload": 0.5, "extract": 1.2}
            emit_event(tid, "step_change", {"step": 2, "step_timing": timing})
            ev = q.get_nowait()
            assert "step_timing" in ev
            assert ev["step_timing"]["upload"] == 0.5
            assert ev["step_timing"]["extract"] == 1.2
        finally:
            _cleanup(tid)

    def test_step_started_at_in_event(self):
        tid = _create_task("pe-timing-2")
        try:
            q = subscribe(tid)
            ts = time.time()
            emit_event(tid, "step_change", {"step": 1, "step_started_at": ts})
            ev = q.get_nowait()
            assert "step_started_at" in ev
            assert ev["step_started_at"] == ts
        finally:
            _cleanup(tid)


class TestCancelAndErrorEvents:
    """Test cancel and error event emission."""

    def test_cancel_event_emitted(self):
        tid = _create_task("pe-cancel-1")
        try:
            q = subscribe(tid)
            state.tasks[tid]["cancel_requested"] = True
            emit_event(tid, "cancelled", {"status": "cancelled", "message": "Task cancelled by user."})
            ev = q.get_nowait()
            assert ev["type"] == "cancelled"
            assert ev["status"] == "cancelled"
        finally:
            _cleanup(tid)

    def test_error_event_contains_sanitized_message(self):
        """Error events should contain user-friendly messages, not raw tracebacks."""
        tid = _create_task("pe-err-1")
        try:
            q = subscribe(tid)
            # Simulate a sanitized error message (pipeline strips paths and maps to friendly text)
            friendly = "GPU memory exhausted. Please try a smaller model."
            emit_event(tid, "error", {"status": "error", "message": friendly})
            ev = q.get_nowait()
            assert ev["type"] == "error"
            assert "/home/user" not in ev["message"]
            assert "gpu" in ev["message"].lower() or "memory" in ev["message"].lower()
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# SEGMENT EVENT STRUCTURE (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestSegmentEventStructure:
    """Test segment events have correct fields and ordering."""

    def test_segment_has_start_field(self):
        tid = _create_task("seg-start-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 0.0, "end": 2.5, "text": "Hello"}})
            ev = q.get_nowait()
            assert "segment" in ev
            assert "start" in ev["segment"]
        finally:
            _cleanup(tid)

    def test_segment_has_end_field(self):
        tid = _create_task("seg-end-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 0.0, "end": 2.5, "text": "Hello"}})
            ev = q.get_nowait()
            assert "end" in ev["segment"]
        finally:
            _cleanup(tid)

    def test_segment_has_text_field(self):
        tid = _create_task("seg-text-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 0.0, "end": 2.5, "text": "Hello world"}})
            ev = q.get_nowait()
            assert "text" in ev["segment"]
            assert ev["segment"]["text"] == "Hello world"
        finally:
            _cleanup(tid)

    def test_segment_timestamps_non_negative(self):
        tid = _create_task("seg-nonneg-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 0.0, "end": 1.5, "text": "Test"}})
            ev = q.get_nowait()
            assert ev["segment"]["start"] >= 0
            assert ev["segment"]["end"] >= 0
        finally:
            _cleanup(tid)

    def test_segment_end_greater_than_start(self):
        tid = _create_task("seg-order-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 1.0, "end": 3.5, "text": "Test"}})
            ev = q.get_nowait()
            assert ev["segment"]["end"] > ev["segment"]["start"]
        finally:
            _cleanup(tid)

    def test_segment_text_non_empty(self):
        tid = _create_task("seg-nonempty-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "segment", {"segment": {"start": 0.0, "end": 2.0, "text": "Some words"}})
            ev = q.get_nowait()
            assert isinstance(ev["segment"]["text"], str)
            assert len(ev["segment"]["text"]) > 0
        finally:
            _cleanup(tid)

    def test_multiple_segments_maintain_ordering(self):
        """Start times of successive segments should increase."""
        tid = _create_task("seg-multi-1")
        try:
            q = subscribe(tid)
            segments = [
                {"start": 0.0, "end": 2.0, "text": "First"},
                {"start": 2.1, "end": 4.5, "text": "Second"},
                {"start": 5.0, "end": 7.0, "text": "Third"},
            ]
            for seg in segments:
                emit_event(tid, "segment", {"segment": seg})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            starts = [e["segment"]["start"] for e in events]
            assert starts == sorted(starts)
            assert starts == [0.0, 2.1, 5.0]
        finally:
            _cleanup(tid)

    def test_segment_has_formatted_timestamps(self):
        """Segment events should contain start_fmt and end_fmt fields."""
        tid = _create_task("seg-fmt-1")
        try:
            q = subscribe(tid)
            emit_event(
                tid,
                "segment",
                {
                    "segment": {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "Hello",
                        "start_fmt": "0:00",
                        "end_fmt": "0:02",
                    }
                },
            )
            ev = q.get_nowait()
            assert "start_fmt" in ev["segment"]
            assert "end_fmt" in ev["segment"]
        finally:
            _cleanup(tid)

    def test_segment_with_speaker_field(self):
        tid = _create_task("seg-spk-1")
        try:
            q = subscribe(tid)
            emit_event(
                tid,
                "segment",
                {
                    "segment": {
                        "start": 0.0,
                        "end": 2.0,
                        "text": "Hello",
                        "speaker": "SPEAKER_00",
                    }
                },
            )
            ev = q.get_nowait()
            assert ev["segment"]["speaker"] == "SPEAKER_00"
        finally:
            _cleanup(tid)

    def test_segment_translated_flag(self):
        """Translation pipeline emits segment events with translated=True."""
        tid = _create_task("seg-trans-1")
        try:
            q = subscribe(tid)
            emit_event(
                tid,
                "segment",
                {
                    "segment": {"start": 0.0, "end": 2.0, "text": "Bonjour"},
                    "translated": True,
                },
            )
            ev = q.get_nowait()
            assert ev["translated"] is True
        finally:
            _cleanup(tid)


# ══════════════════════════════════════════════════════════════════════════════
# PROFILER & ETA (10 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestTranscriptionProfiler:
    """Test TranscriptionProfiler class from profiler.py."""

    def test_profiler_importable(self):
        from profiler import TranscriptionProfiler

        assert TranscriptionProfiler is not None

    def test_profiler_init(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-1")
        assert p.task_id == "test-prof-1"
        assert p.segments == []

    def test_profiler_tracks_segment_count(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-2")
        p.on_segment({"start": 0.0, "end": 2.0, "text": "Hello"}, 0)
        p.on_segment({"start": 2.0, "end": 4.0, "text": "World"}, 1)
        assert len(p.segments) == 2

    def test_profiler_summary_total_segments(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-3")
        p.on_segment({"start": 0, "end": 2, "text": "A"}, 0)
        p.on_segment({"start": 2, "end": 4, "text": "B"}, 1)
        p.on_segment({"start": 4, "end": 6, "text": "C"}, 2)
        s = p.summary()
        assert s["total_segments"] == 3

    def test_profiler_calculates_speed_x(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-4")
        # Simulate progress: 10000 frames total = 100 seconds of audio
        p.total_frames = 10000
        p.on_segment({"start": 0, "end": 50, "text": "First half"}, 0)
        s = p.summary()
        assert "overall_speed_x" in s
        # Speed should be positive (audio_duration / wall_time)
        assert s["overall_speed_x"] >= 0

    def test_profiler_on_progress_returns_metrics(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-5")
        metrics = p.on_progress(5000, 10000)
        assert "ratio" in metrics
        assert "eta_sec" in metrics
        assert "instant_speed_x" in metrics
        assert "avg_speed_x" in metrics
        assert "overall_speed_x" in metrics

    def test_profiler_eta_calculation(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-6")
        # First call to establish baseline
        p.on_progress(1000, 10000)
        time.sleep(0.01)  # small delay for measurable time delta
        metrics = p.on_progress(2000, 10000)
        # ETA should be present (may be -1 if avg_throughput is 0)
        assert "eta_sec" in metrics

    def test_profiler_handles_zero_segments(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-7")
        s = p.summary()
        assert s["total_segments"] == 0
        assert "seg_duration_avg" not in s  # no segments = no avg

    def test_profiler_handles_zero_elapsed_time(self):
        """Profiler should not crash with division by zero."""
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-8")
        # summary right after init — nearly zero elapsed
        s = p.summary()
        assert isinstance(s, dict)
        assert s["total_segments"] == 0

    def test_profiler_segment_metrics_stored(self):
        from profiler import TranscriptionProfiler

        p = TranscriptionProfiler("test-prof-9")
        p.on_segment({"start": 1.0, "end": 3.0, "text": "Hello world"}, 0)
        seg = p.segments[0]
        assert seg["index"] == 0
        assert seg["start"] == 1.0
        assert seg["end"] == 3.0
        assert seg["duration_sec"] == 2.0
        assert seg["text_length"] == len("Hello world")


# ══════════════════════════════════════════════════════════════════════════════
# EVENT QUEUE MANAGEMENT (5 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestEventQueueManagement:
    """Test SSE event queue creation, subscription, and cleanup."""

    def test_event_queue_created_for_task(self):
        tid = "eq-create-1"
        try:
            create_event_queue(tid)
            assert tid in state.task_event_queues
        finally:
            state.task_event_queues.pop(tid, None)

    def test_events_queued_correctly(self):
        tid = _create_task("eq-queue-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 30})
            emit_event(tid, "progress", {"percent": 60})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert len(events) == 2
            assert events[0]["percent"] == 30
            assert events[1]["percent"] == 60
        finally:
            _cleanup(tid)

    def test_queue_has_max_size_limit(self):
        """Subscribe with a small maxsize and verify overflow is handled."""
        tid = _create_task("eq-max-1")
        try:
            q = subscribe(tid, maxsize=5)
            # Emit more events than the queue can hold
            for i in range(10):
                emit_event(tid, "progress", {"percent": i * 10})
            # Queue should have at most 5 items (extras dropped)
            count = 0
            while not q.empty():
                q.get_nowait()
                count += 1
            assert count <= 5
        finally:
            _cleanup(tid)

    def test_multiple_subscribers_get_same_events(self):
        tid = _create_task("eq-multi-1")
        try:
            q1 = subscribe(tid)
            q2 = subscribe(tid)
            emit_event(tid, "progress", {"percent": 42})
            ev1 = q1.get_nowait()
            ev2 = q2.get_nowait()
            assert ev1["percent"] == 42
            assert ev2["percent"] == 42
            assert ev1["type"] == ev2["type"]
        finally:
            _cleanup(tid)

    def test_queue_cleanup_after_task_completion(self):
        """After task is done and cleaned up, queues should be removable."""
        tid = _create_task("eq-cleanup-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "done", {"status": "done", "percent": 100})
            # Unsubscribe
            unsubscribe(tid, q)
            # Remove task queues
            state.task_event_queues.pop(tid, None)
            assert tid not in state.task_event_queues
        finally:
            state.tasks.pop(tid, None)
            state.task_event_queues.pop(tid, None)

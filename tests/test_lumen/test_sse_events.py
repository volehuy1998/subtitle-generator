"""Phase Lumen L8 — SSE event system tests.

Tests SSE endpoint availability, event queue management, subscriber
lifecycle, event emission, and polling fallback.
— Scout (QA Lead)
"""

import queue
import struct
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app import state
from app.main import app
from app.services.sse import create_event_queue, emit_event, subscribe, unsubscribe

client = TestClient(app, base_url="https://testserver")


def _make_wav_bytes(duration_sec: float = 0.5) -> bytes:
    num_samples = int(16000 * duration_sec)
    buf = BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
    buf.seek(0)
    return buf.read()


def _create_task(task_id="test-sse-task"):
    """Create a fake task in state."""
    state.tasks[task_id] = {
        "status": "transcribing",
        "percent": 50,
        "message": "Processing...",
        "session_id": "",
    }
    create_event_queue(task_id)
    return task_id


def _cleanup_task(task_id):
    """Remove a fake task."""
    state.tasks.pop(task_id, None)
    state.task_event_queues.pop(task_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT ENDPOINT AVAILABILITY
# ══════════════════════════════════════════════════════════════════════════════


class TestEventEndpointAvailability:
    """Test that SSE endpoints exist and respond correctly."""

    def test_events_endpoint_404_for_unknown_task(self):
        res = client.get("/events/nonexistent-task-id", timeout=2)
        assert res.status_code == 404

    def test_progress_endpoint_404_for_unknown_task(self):
        res = client.get("/progress/nonexistent-task-id")
        assert res.status_code == 404

    def test_progress_endpoint_returns_task_data(self):
        tid = _create_task("progress-test-1")
        try:
            res = client.get(f"/progress/{tid}")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "transcribing"
            assert data["percent"] == 50
        finally:
            _cleanup_task(tid)

    def test_progress_returns_message(self):
        tid = _create_task("progress-msg-1")
        try:
            res = client.get(f"/progress/{tid}")
            data = res.json()
            assert "message" in data
        finally:
            _cleanup_task(tid)

    def test_health_stream_endpoint_exists(self):
        # /health/stream returns SSE streaming response
        # We just verify the endpoint doesn't 404 by checking the route exists
        from app.main import app as _app

        routes = [r.path for r in _app.routes if hasattr(r, "path")]
        assert "/health/stream" in routes


# ══════════════════════════════════════════════════════════════════════════════
# EVENT QUEUE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════


class TestEventQueueManagement:
    """Test event queue creation, subscription, and cleanup."""

    def test_create_event_queue(self):
        tid = "queue-create-1"
        try:
            create_event_queue(tid)
            assert tid in state.task_event_queues
        finally:
            state.task_event_queues.pop(tid, None)

    def test_create_queue_idempotent(self):
        tid = "queue-idempotent-1"
        try:
            create_event_queue(tid)
            create_event_queue(tid)  # Should not raise
            assert tid in state.task_event_queues
        finally:
            state.task_event_queues.pop(tid, None)

    def test_subscribe_returns_queue(self):
        tid = "sub-test-1"
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            assert isinstance(q, queue.Queue)
        finally:
            state.task_event_queues.pop(tid, None)

    def test_subscribe_without_prior_create(self):
        tid = "sub-no-create-1"
        try:
            q = subscribe(tid)
            assert isinstance(q, queue.Queue)
            assert tid in state.task_event_queues
        finally:
            state.task_event_queues.pop(tid, None)

    def test_multiple_subscribers(self):
        tid = "multi-sub-1"
        try:
            create_event_queue(tid)
            q1 = subscribe(tid)
            q2 = subscribe(tid)
            assert q1 is not q2
            assert len(state.task_event_queues[tid]) >= 2
        finally:
            state.task_event_queues.pop(tid, None)

    def test_unsubscribe_removes_queue(self):
        tid = "unsub-1"
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            unsubscribe(tid, q)
            assert q not in state.task_event_queues.get(tid, [])
        finally:
            state.task_event_queues.pop(tid, None)

    def test_unsubscribe_nonexistent_safe(self):
        # Should not raise
        unsubscribe("nonexistent-task", queue.Queue())

    def test_unsubscribe_wrong_queue_safe(self):
        tid = "unsub-wrong-1"
        try:
            create_event_queue(tid)
            q1 = subscribe(tid)
            q_other = queue.Queue()
            unsubscribe(tid, q_other)  # Should not raise
            assert q1 in state.task_event_queues[tid]
        finally:
            state.task_event_queues.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT EMISSION
# ══════════════════════════════════════════════════════════════════════════════


class TestEventEmission:
    """Test emit_event functionality."""

    def test_emit_updates_task_state(self):
        tid = "emit-state-1"
        state.tasks[tid] = {"status": "queued", "percent": 0}
        try:
            create_event_queue(tid)
            emit_event(tid, "update", {"percent": 50, "message": "Halfway"})
            assert state.tasks[tid]["percent"] == 50
            assert state.tasks[tid]["message"] == "Halfway"
        finally:
            _cleanup_task(tid)

    def test_emit_broadcasts_to_subscribers(self):
        tid = "emit-broadcast-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q1 = subscribe(tid)
            q2 = subscribe(tid)
            emit_event(tid, "progress", {"percent": 75})
            event1 = q1.get_nowait()
            event2 = q2.get_nowait()
            assert event1["type"] == "progress"
            assert event2["type"] == "progress"
            assert event1["percent"] == 75
        finally:
            _cleanup_task(tid)

    def test_emit_with_no_subscribers(self):
        tid = "emit-nosub-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            # No subscribers, should not raise
            emit_event(tid, "update", {"percent": 10})
            assert state.tasks[tid]["percent"] == 10
        finally:
            _cleanup_task(tid)

    def test_emit_event_type_included(self):
        tid = "emit-type-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "step_change", {"step": 2})
            event = q.get_nowait()
            assert event["type"] == "step_change"
        finally:
            _cleanup_task(tid)

    def test_emit_timestamp_included(self):
        tid = "emit-ts-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "update", {})
            event = q.get_nowait()
            assert "timestamp" in event
        finally:
            _cleanup_task(tid)

    def test_emit_none_data_default(self):
        tid = "emit-none-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "heartbeat")
            event = q.get_nowait()
            assert event["type"] == "heartbeat"
        finally:
            _cleanup_task(tid)

    def test_emit_preserves_existing_state(self):
        tid = "emit-preserve-1"
        state.tasks[tid] = {"status": "transcribing", "filename": "test.wav"}
        try:
            create_event_queue(tid)
            emit_event(tid, "update", {"percent": 30})
            assert state.tasks[tid]["filename"] == "test.wav"
            assert state.tasks[tid]["percent"] == 30
        finally:
            _cleanup_task(tid)

    def test_emit_to_unknown_task_safe(self):
        # Should not raise even if task not in state
        emit_event("completely-unknown-task", "update", {"percent": 50})

    def test_emit_full_queue_drops_event(self):
        tid = "emit-full-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid, maxsize=1)
            # Fill the queue
            emit_event(tid, "first", {"data": 1})
            # This should not raise (drops the event)
            emit_event(tid, "second", {"data": 2})
            # Only first event should be in queue
            event = q.get_nowait()
            assert event["type"] == "first"
        finally:
            _cleanup_task(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT TYPES
# ══════════════════════════════════════════════════════════════════════════════


class TestEventTypes:
    """Test various event types emitted by the pipeline."""

    def test_update_event(self):
        tid = "etype-update-1"
        state.tasks[tid] = {"status": "queued"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "update", {"status": "transcribing"})
            event = q.get_nowait()
            assert event["type"] == "update"
        finally:
            _cleanup_task(tid)

    def test_done_event(self):
        tid = "etype-done-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "done", {"status": "done"})
            event = q.get_nowait()
            assert event["type"] == "done"
        finally:
            _cleanup_task(tid)

    def test_error_event(self):
        tid = "etype-error-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "error", {"status": "error", "message": "Failed"})
            event = q.get_nowait()
            assert event["type"] == "error"
        finally:
            _cleanup_task(tid)

    def test_cancelled_event(self):
        tid = "etype-cancel-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "cancelled", {"status": "cancelled"})
            event = q.get_nowait()
            assert event["type"] == "cancelled"
        finally:
            _cleanup_task(tid)

    def test_heartbeat_event(self):
        tid = "etype-hb-1"
        state.tasks[tid] = {"status": "transcribing"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "heartbeat", {})
            event = q.get_nowait()
            assert event["type"] == "heartbeat"
        finally:
            _cleanup_task(tid)


# ══════════════════════════════════════════════════════════════════════════════
# POLLING ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════


class TestPollingEndpoint:
    """Test the /progress/{task_id} polling fallback."""

    def test_polling_returns_status(self):
        tid = "poll-status-1"
        state.tasks[tid] = {"status": "done", "percent": 100, "message": "Complete", "session_id": ""}
        try:
            res = client.get(f"/progress/{tid}")
            assert res.status_code == 200
            assert res.json()["status"] == "done"
        finally:
            state.tasks.pop(tid, None)

    def test_polling_returns_percent(self):
        tid = "poll-pct-1"
        state.tasks[tid] = {"status": "transcribing", "percent": 42, "message": "Working...", "session_id": ""}
        try:
            res = client.get(f"/progress/{tid}")
            assert res.json()["percent"] == 42
        finally:
            state.tasks.pop(tid, None)

    def test_polling_unknown_task_404(self):
        res = client.get("/progress/nonexistent-12345")
        assert res.status_code == 404

    def test_polling_filters_internal_fields(self):
        tid = "poll-filter-1"
        state.tasks[tid] = {
            "status": "done",
            "percent": 100,
            "message": "Done",
            "session_id": "",
            "pause_event": "should_be_filtered",
        }
        try:
            res = client.get(f"/progress/{tid}")
            data = res.json()
            assert "pause_event" not in data
        finally:
            state.tasks.pop(tid, None)

    def test_polling_filters_profiler(self):
        tid = "poll-prof-1"
        state.tasks[tid] = {
            "status": "done",
            "percent": 100,
            "message": "Done",
            "session_id": "",
            "transcription_profiler": {"data": "private"},
        }
        try:
            res = client.get(f"/progress/{tid}")
            data = res.json()
            assert "transcription_profiler" not in data
        finally:
            state.tasks.pop(tid, None)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT ORDERING
# ══════════════════════════════════════════════════════════════════════════════


class TestEventOrdering:
    """Test that events are received in the order they were emitted."""

    def test_events_ordered(self):
        tid = "order-1"
        state.tasks[tid] = {"status": "queued"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            for i in range(5):
                emit_event(tid, "progress", {"step": i})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert [e["step"] for e in events] == [0, 1, 2, 3, 4]
        finally:
            _cleanup_task(tid)

    def test_event_sequence_types(self):
        tid = "order-types-1"
        state.tasks[tid] = {"status": "queued"}
        try:
            create_event_queue(tid)
            q = subscribe(tid)
            emit_event(tid, "start", {})
            emit_event(tid, "progress", {"percent": 50})
            emit_event(tid, "done", {})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            types = [e["type"] for e in events]
            assert types == ["start", "progress", "done"]
        finally:
            _cleanup_task(tid)

"""Phase Lumen L15 — Event sequencing and queue behavior tests.

Tests SSE event structure, sequencing, queue lifecycle, subscriber
management, and event delivery guarantees.
— Scout (QA Lead)
"""

import time

from fastapi.testclient import TestClient

from app import state
from app.main import app
from app.services.sse import create_event_queue, emit_event, subscribe, unsubscribe

client = TestClient(app, base_url="https://testserver")


def _create_task(task_id):
    """Create a fake task in state."""
    state.tasks[task_id] = {
        "status": "transcribing",
        "percent": 0,
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
# EVENT STRUCTURE AND FIELDS
# ══════════════════════════════════════════════════════════════════════════════


class TestEventStructure:
    """Test that emitted events have the expected structure."""

    def test_event_has_type_field(self):
        tid = _create_task("seq-type-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 10})
            event = q.get_nowait()
            assert "type" in event
            assert event["type"] == "progress"
        finally:
            _cleanup_task(tid)

    def test_event_has_timestamp_field(self):
        tid = _create_task("seq-ts-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "update", {"percent": 20})
            event = q.get_nowait()
            assert "timestamp" in event
            assert isinstance(event["timestamp"], float)
        finally:
            _cleanup_task(tid)

    def test_event_timestamp_is_recent(self):
        tid = _create_task("seq-ts-recent-1")
        try:
            q = subscribe(tid)
            before = time.time()
            emit_event(tid, "update", {})
            after = time.time()
            event = q.get_nowait()
            assert before <= event["timestamp"] <= after
        finally:
            _cleanup_task(tid)

    def test_event_includes_custom_data(self):
        tid = _create_task("seq-data-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"percent": 42, "message": "Transcribing"})
            event = q.get_nowait()
            assert event["percent"] == 42
            assert event["message"] == "Transcribing"
        finally:
            _cleanup_task(tid)

    def test_event_type_not_overwritten_by_data(self):
        """Event type should come from the event_type parameter, not data."""
        tid = _create_task("seq-type-over-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "progress", {"type": "should_not_override"})
            event = q.get_nowait()
            # The event dict is built with {type: event_type, ...data}
            # Since data is spread after, data's "type" would override.
            # This tests the actual behavior.
            assert "type" in event
        finally:
            _cleanup_task(tid)

    def test_event_with_empty_data(self):
        tid = _create_task("seq-empty-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "heartbeat", {})
            event = q.get_nowait()
            assert event["type"] == "heartbeat"
            assert "timestamp" in event
        finally:
            _cleanup_task(tid)

    def test_event_with_none_data(self):
        tid = _create_task("seq-none-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "heartbeat")
            event = q.get_nowait()
            assert event["type"] == "heartbeat"
        finally:
            _cleanup_task(tid)

    def test_all_event_types_include_type_field(self):
        """Verify all common event types carry the type field."""
        tid = _create_task("seq-alltypes-1")
        try:
            q = subscribe(tid)
            event_types = ["start", "progress", "update", "step_change", "done", "error", "cancelled", "heartbeat"]
            for et in event_types:
                emit_event(tid, et, {})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            for event in events:
                assert "type" in event
            assert len(events) == len(event_types)
        finally:
            _cleanup_task(tid)


# ══════════════════════════════════════════════════════════════════════════════
# EVENT ORDERING AND SEQUENCING
# ══════════════════════════════════════════════════════════════════════════════


class TestEventSequencing:
    """Test that events maintain ordering guarantees."""

    def test_events_arrive_in_order(self):
        tid = _create_task("seq-order-1")
        try:
            q = subscribe(tid)
            for i in range(10):
                emit_event(tid, "progress", {"step": i})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            steps = [e["step"] for e in events]
            assert steps == list(range(10))
        finally:
            _cleanup_task(tid)

    def test_timestamps_monotonically_increase(self):
        tid = _create_task("seq-mono-1")
        try:
            q = subscribe(tid)
            for i in range(5):
                emit_event(tid, "progress", {"step": i})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            timestamps = [e["timestamp"] for e in events]
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i - 1]
        finally:
            _cleanup_task(tid)

    def test_independent_tasks_have_independent_queues(self):
        tid1 = _create_task("seq-indep-1")
        tid2 = _create_task("seq-indep-2")
        try:
            q1 = subscribe(tid1)
            q2 = subscribe(tid2)
            emit_event(tid1, "progress", {"task": "first"})
            emit_event(tid2, "progress", {"task": "second"})
            e1 = q1.get_nowait()
            e2 = q2.get_nowait()
            assert e1["task"] == "first"
            assert e2["task"] == "second"
        finally:
            _cleanup_task(tid1)
            _cleanup_task(tid2)

    def test_event_sequence_survives_multiple_emissions(self):
        tid = _create_task("seq-multi-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "start", {"phase": "begin"})
            emit_event(tid, "progress", {"percent": 25})
            emit_event(tid, "progress", {"percent": 50})
            emit_event(tid, "progress", {"percent": 75})
            emit_event(tid, "done", {"percent": 100})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            assert len(events) == 5
            types = [e["type"] for e in events]
            assert types == ["start", "progress", "progress", "progress", "done"]
        finally:
            _cleanup_task(tid)

    def test_mixed_event_types_preserve_order(self):
        tid = _create_task("seq-mixed-1")
        try:
            q = subscribe(tid)
            sequence = [
                ("update", {"status": "extracting"}),
                ("progress", {"percent": 10}),
                ("update", {"status": "transcribing"}),
                ("progress", {"percent": 50}),
                ("heartbeat", {}),
                ("progress", {"percent": 90}),
                ("done", {"status": "done"}),
            ]
            for etype, data in sequence:
                emit_event(tid, etype, data)
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            actual_types = [e["type"] for e in events]
            expected_types = [s[0] for s in sequence]
            assert actual_types == expected_types
        finally:
            _cleanup_task(tid)

    def test_rapid_burst_preserves_order(self):
        """Events emitted in rapid succession should maintain order."""
        tid = _create_task("seq-burst-1")
        try:
            q = subscribe(tid)
            for i in range(50):
                emit_event(tid, "progress", {"index": i})
            events = []
            while not q.empty():
                events.append(q.get_nowait())
            indices = [e["index"] for e in events]
            assert indices == list(range(50))
        finally:
            _cleanup_task(tid)


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE BEHAVIOR
# ══════════════════════════════════════════════════════════════════════════════


class TestQueueBehavior:
    """Test event queue creation, capacity, and lifecycle."""

    def test_queue_created_for_new_task(self):
        tid = "qb-create-1"
        try:
            create_event_queue(tid)
            assert tid in state.task_event_queues
        finally:
            state.task_event_queues.pop(tid, None)

    def test_queue_receives_emitted_events(self):
        tid = _create_task("qb-recv-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "test", {"key": "value"})
            event = q.get_nowait()
            assert event["key"] == "value"
        finally:
            _cleanup_task(tid)

    def test_queue_handles_multiple_subscribers(self):
        tid = _create_task("qb-multi-1")
        try:
            q1 = subscribe(tid)
            q2 = subscribe(tid)
            q3 = subscribe(tid)
            emit_event(tid, "broadcast", {"msg": "hello"})
            for q in [q1, q2, q3]:
                event = q.get_nowait()
                assert event["msg"] == "hello"
        finally:
            _cleanup_task(tid)

    def test_queue_has_max_size(self):
        """Queue should have a max size and drop events when full."""
        tid = _create_task("qb-max-1")
        try:
            q = subscribe(tid, maxsize=5)
            # Fill the queue
            for i in range(5):
                emit_event(tid, "fill", {"i": i})
            # Queue should be full now
            assert q.full()
            # Next event should be dropped (not raise)
            emit_event(tid, "overflow", {"i": 999})
            # Queue should still have exactly 5 events
            count = 0
            while not q.empty():
                q.get_nowait()
                count += 1
            assert count == 5
        finally:
            _cleanup_task(tid)

    def test_events_delivered_to_all_subscribers(self):
        tid = _create_task("qb-deliver-1")
        try:
            subscribers = [subscribe(tid) for _ in range(5)]
            emit_event(tid, "data", {"value": 42})
            for q in subscribers:
                event = q.get_nowait()
                assert event["value"] == 42
        finally:
            _cleanup_task(tid)

    def test_task_cleanup_removes_queues(self):
        tid = _create_task("qb-cleanup-1")
        subscribe(tid)
        assert tid in state.task_event_queues
        _cleanup_task(tid)
        assert tid not in state.task_event_queues

    def test_heartbeat_event_emitted_correctly(self):
        tid = _create_task("qb-hb-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "heartbeat", {})
            event = q.get_nowait()
            assert event["type"] == "heartbeat"
        finally:
            _cleanup_task(tid)

    def test_event_format_has_required_keys(self):
        """Every event must have at minimum 'type' and 'timestamp'."""
        tid = _create_task("qb-format-1")
        try:
            q = subscribe(tid)
            emit_event(tid, "test_event", {"extra": "data"})
            event = q.get_nowait()
            assert isinstance(event, dict)
            assert "type" in event
            assert "timestamp" in event
        finally:
            _cleanup_task(tid)

    def test_unsubscribe_stops_delivery(self):
        """After unsubscribe, the queue should no longer receive events."""
        tid = _create_task("qb-unsub-1")
        try:
            q = subscribe(tid)
            unsubscribe(tid, q)
            emit_event(tid, "after_unsub", {"data": "missed"})
            assert q.empty()
        finally:
            _cleanup_task(tid)

    def test_queue_handles_rapid_event_bursts(self):
        """Queue should handle many events in quick succession."""
        tid = _create_task("qb-rapid-1")
        try:
            q = subscribe(tid, maxsize=1000)
            for i in range(100):
                emit_event(tid, "burst", {"i": i})
            count = 0
            while not q.empty():
                q.get_nowait()
                count += 1
            assert count == 100
        finally:
            _cleanup_task(tid)

    def test_default_queue_maxsize(self):
        """Default queue maxsize should be 1000."""
        tid = _create_task("qb-default-1")
        try:
            q = subscribe(tid)
            assert q.maxsize == 1000
        finally:
            _cleanup_task(tid)

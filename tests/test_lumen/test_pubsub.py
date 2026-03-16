"""Phase Lumen L63 — Redis Pub/Sub tests.

Tests publish_event, subscribe_events, channel naming, error handling,
terminal event detection, heartbeat, and cleanup.
— Scout (QA Lead)
"""

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock redis modules so app.services.redis_client can be imported
if "redis" not in sys.modules:
    _redis_mock = MagicMock()
    sys.modules["redis"] = _redis_mock
    sys.modules["redis.asyncio"] = _redis_mock.asyncio


def _run(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ══════════════════════════════════════════════════════════════════════════════
# CHANNEL NAME
# ══════════════════════════════════════════════════════════════════════════════


class TestChannelName:
    """Test _channel_name helper."""

    def test_channel_name_format(self):
        from app.services.pubsub import _channel_name

        assert _channel_name("abc123") == "events:abc123"

    def test_channel_name_with_long_id(self):
        from app.services.pubsub import _channel_name

        task_id = "a" * 36
        assert _channel_name(task_id) == f"events:{task_id}"


# ══════════════════════════════════════════════════════════════════════════════
# PUBLISH EVENT
# ══════════════════════════════════════════════════════════════════════════════


class TestPublishEvent:
    """Test publish_event function."""

    @patch("app.services.redis_client.get_sync_redis")
    def test_publish_calls_redis_with_correct_channel_and_json(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        from app.services.pubsub import publish_event

        publish_event("task123", "step_change", {"status": "extracting"})

        mock_redis.publish.assert_called_once()
        channel, payload = mock_redis.publish.call_args[0]
        assert channel == "events:task123"

        data = json.loads(payload)
        assert data["type"] == "step_change"
        assert "timestamp" in data
        assert data["status"] == "extracting"

    @patch("app.services.redis_client.get_sync_redis")
    def test_publish_with_none_data(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        from app.services.pubsub import publish_event

        publish_event("task123", "progress")

        payload = json.loads(mock_redis.publish.call_args[0][1])
        assert payload["type"] == "progress"
        assert "timestamp" in payload

    @patch("app.services.redis_client.get_sync_redis")
    def test_publish_swallows_redis_exception(self, mock_get_redis):
        mock_get_redis.side_effect = RuntimeError("Redis down")

        from app.services.pubsub import publish_event

        # Should not raise
        publish_event("task123", "step_change")


# ══════════════════════════════════════════════════════════════════════════════
# SUBSCRIBE EVENTS
# ══════════════════════════════════════════════════════════════════════════════


async def _collect_events(task_id):
    """Helper to collect all events from subscribe_events."""
    from app.services.pubsub import subscribe_events

    events = []
    async for event in subscribe_events(task_id):
        events.append(event)
    return events


class TestSubscribeEvents:
    """Test subscribe_events async generator."""

    @patch("app.services.redis_client.get_async_redis")
    def test_non_terminal_event_yielded(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "progress", "percent": 50})},
                {"type": "message", "data": json.dumps({"type": "done"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 2
        assert events[0]["type"] == "progress"
        assert events[0]["percent"] == 50
        assert events[1]["type"] == "done"

    @patch("app.services.redis_client.get_async_redis")
    def test_terminal_done_breaks_loop(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "done"})},
                {"type": "message", "data": json.dumps({"type": "should_not_reach"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 1
        assert events[0]["type"] == "done"

    @patch("app.services.redis_client.get_async_redis")
    def test_terminal_error_breaks_loop(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "error"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 1
        assert events[0]["type"] == "error"

    @patch("app.services.redis_client.get_async_redis")
    def test_terminal_cancelled_breaks_loop(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "cancelled"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 1
        assert events[0]["type"] == "cancelled"

    @patch("app.services.redis_client.get_async_redis")
    def test_terminal_embed_done_breaks_loop(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "embed_done"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 1
        assert events[0]["type"] == "embed_done"

    @patch("app.services.redis_client.get_async_redis")
    def test_terminal_embed_error_breaks_loop(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "embed_error"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 1
        assert events[0]["type"] == "embed_error"

    @patch("app.services.redis_client.get_async_redis")
    def test_malformed_json_skipped(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": "not valid json{{{"},
                {"type": "message", "data": json.dumps({"type": "done"})},
            ]
        )

        events = _run(_collect_events("task1"))

        # Malformed JSON is skipped, only "done" is yielded
        assert len(events) == 1
        assert events[0]["type"] == "done"

    @patch("app.services.redis_client.get_async_redis")
    def test_timeout_yields_heartbeat(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                None,  # timeout — no message
                {"type": "message", "data": json.dumps({"type": "done"})},
            ]
        )

        events = _run(_collect_events("task1"))

        assert len(events) == 2
        assert events[0]["type"] == "heartbeat"
        assert events[1]["type"] == "done"

    @patch("app.services.redis_client.get_async_redis")
    def test_finally_calls_unsubscribe_and_aclose(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub

        mock_pubsub.get_message = AsyncMock(
            side_effect=[
                {"type": "message", "data": json.dumps({"type": "done"})},
            ]
        )

        _run(_collect_events("task1"))

        mock_pubsub.unsubscribe.assert_awaited_once_with("events:task1")
        mock_pubsub.aclose.assert_awaited_once()

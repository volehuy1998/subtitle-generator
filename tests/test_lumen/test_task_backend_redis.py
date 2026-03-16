"""Phase Lumen L63 — Redis task backend tests.

Tests RedisTaskBackend: serialization, CRUD, bulk operations,
field updates, and edge cases.
— Scout (QA Lead)
"""

import json
import sys
from unittest.mock import MagicMock, patch

# Mock redis modules so app.services.redis_client can be imported
if "redis" not in sys.modules:
    _redis_mock = MagicMock()
    sys.modules["redis"] = _redis_mock
    sys.modules["redis.asyncio"] = _redis_mock.asyncio


from app.services.task_backend_redis import _SKIP_FIELDS, _deserialize, _serialize

# ══════════════════════════════════════════════════════════════════════════════
# SERIALIZATION
# ══════════════════════════════════════════════════════════════════════════════


class TestSerialize:
    """Test _serialize and _deserialize helpers."""

    def test_serialize_strips_skip_fields(self):
        data = {
            "status": "done",
            "percent": 100,
            "pause_event": object(),
            "transcription_profiler": object(),
            "_subprocess": object(),
            "_thread_id": 12345,
        }
        result = json.loads(_serialize(data))
        assert "status" in result
        assert "percent" in result
        for field in _SKIP_FIELDS:
            assert field not in result

    def test_serialize_returns_valid_json(self):
        data = {"status": "processing", "message": "extracting audio"}
        raw = _serialize(data)
        parsed = json.loads(raw)
        assert parsed["status"] == "processing"

    def test_deserialize_round_trips_correctly(self):
        original = {"status": "done", "percent": 100, "segments": [{"text": "hello"}]}
        raw = _serialize(original)
        restored = _deserialize(raw)
        assert restored == original

    def test_serialize_handles_non_json_types_via_default_str(self):
        """Non-serializable values are converted to strings via default=str."""
        from pathlib import Path

        data = {"path": Path("/tmp/test.srt")}
        raw = _serialize(data)
        parsed = json.loads(raw)
        assert parsed["path"] == "/tmp/test.srt"


# ══════════════════════════════════════════════════════════════════════════════
# REDIS TASK BACKEND CRUD
# ══════════════════════════════════════════════════════════════════════════════


def _make_redis_backend():
    """Create a RedisTaskBackend with a mock Redis client."""
    mock_redis = MagicMock()
    with patch("app.services.redis_client.get_sync_redis", return_value=mock_redis):
        from app.services.task_backend_redis import RedisTaskBackend

        backend = RedisTaskBackend()
    # Ensure the mock is what's used (in case init already ran)
    backend._redis = mock_redis
    return backend, mock_redis


class TestRedisTaskBackendCRUD:
    """Test RedisTaskBackend get/set/delete."""

    def test_get_returns_none_when_redis_returns_none(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.get.return_value = None

        result = backend.get("nonexistent")

        assert result is None
        mock_redis.get.assert_called_once_with("task:nonexistent")

    def test_get_returns_deserialized_dict_when_exists(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.get.return_value = json.dumps({"status": "done", "percent": 100})

        result = backend.get("task123")

        assert result == {"status": "done", "percent": 100}

    def test_set_calls_redis_set_with_key_and_ttl(self):
        backend, mock_redis = _make_redis_backend()

        backend.set("task123", {"status": "processing", "percent": 50})

        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args
        assert args[0] == "task:task123"
        payload = json.loads(args[1])
        assert payload["status"] == "processing"
        assert kwargs["ex"] == 86400 * 7  # 7-day TTL

    def test_delete_calls_redis_delete(self):
        backend, mock_redis = _make_redis_backend()

        backend.delete("task123")

        mock_redis.delete.assert_called_once_with("task:task123")


# ══════════════════════════════════════════════════════════════════════════════
# REDIS TASK BACKEND BULK OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestRedisTaskBackendBulk:
    """Test items, contains, update_field."""

    def test_items_paginates_through_scan_pages(self):
        backend, mock_redis = _make_redis_backend()

        # Simulate two scan pages: first returns cursor=42, second returns cursor=0
        mock_redis.scan.side_effect = [
            (42, ["task:id1"]),
            (0, ["task:id2"]),
        ]
        mock_redis.get.side_effect = [
            json.dumps({"status": "done"}),
            json.dumps({"status": "error"}),
        ]

        result = backend.items()

        assert len(result) == 2
        assert result[0] == ("id1", {"status": "done"})
        assert result[1] == ("id2", {"status": "error"})

    def test_contains_returns_true_when_exists(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.exists.return_value = 1

        assert backend.contains("task123") is True
        mock_redis.exists.assert_called_once_with("task:task123")

    def test_contains_returns_false_when_not_exists(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.exists.return_value = 0

        assert backend.contains("task123") is False

    def test_update_field_updates_single_field(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.get.return_value = json.dumps({"status": "processing", "percent": 50})

        backend.update_field("task123", "percent", 75)

        # Should have called set with updated data
        mock_redis.set.assert_called_once()
        args = mock_redis.set.call_args[0]
        payload = json.loads(args[1])
        assert payload["percent"] == 75
        assert payload["status"] == "processing"  # Not clobbered

    def test_update_field_noops_when_task_not_found(self):
        backend, mock_redis = _make_redis_backend()
        mock_redis.get.return_value = None

        backend.update_field("nonexistent", "percent", 75)

        mock_redis.set.assert_not_called()

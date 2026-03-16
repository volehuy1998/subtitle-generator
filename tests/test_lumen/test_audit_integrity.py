"""Phase Lumen L62 — Audit integrity and PostgreSQL audit tests.

Tests HMAC-signed audit entries (create, verify, reject tampered)
and async PostgreSQL audit operations (persist, query, cleanup).
— Scout (QA Lead)
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.security_infra import (
    create_signed_audit_entry,
    verify_audit_entry,
)


def _run(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ══════════════════════════════════════════════════════════════════════════════
# SIGNED AUDIT ENTRY
# ══════════════════════════════════════════════════════════════════════════════


class TestSignedAuditEntry:
    """Test create_signed_audit_entry / verify_audit_entry."""

    def test_create_signed_entry_has_hmac(self):
        """create_signed_audit_entry with empty kwargs produces valid hmac field."""
        entry = create_signed_audit_entry("test_event")
        assert "hmac" in entry
        assert isinstance(entry["hmac"], str)
        assert len(entry["hmac"]) == 64  # SHA-256 hex digest

    def test_create_signed_entry_has_required_fields(self):
        entry = create_signed_audit_entry("login_attempt", ip="1.2.3.4")
        assert entry["event_type"] == "login_attempt"
        assert entry["ip"] == "1.2.3.4"
        assert "timestamp" in entry
        assert "hmac" in entry

    def test_verify_valid_entry(self):
        entry = create_signed_audit_entry("test_event")
        sig = entry.pop("hmac")
        assert verify_audit_entry(entry, sig) is True

    def test_verify_rejects_corrupt_signature(self):
        """verify_audit_entry returns False for wrong-length/corrupt signature string."""
        entry = create_signed_audit_entry("test_event")
        entry.pop("hmac")
        assert verify_audit_entry(entry, "deadbeef") is False
        assert verify_audit_entry(entry, "") is False
        assert verify_audit_entry(entry, "x" * 64) is False

    def test_signature_key_mismatch(self):
        """Signature produced with key A rejected under key B."""
        entry = create_signed_audit_entry("test_event")
        original_sig = entry.pop("hmac")

        # Re-sign with a different key
        with patch("app.utils.security_infra._AUDIT_HMAC_KEY", "totally_different_key"):
            assert verify_audit_entry(entry, original_sig) is False

    def test_entry_timestamp_is_iso8601_utc(self):
        """Entry timestamp is ISO-8601 formatted UTC string."""
        entry = create_signed_audit_entry("test_event")
        ts = entry["timestamp"]
        # Should parse without error
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None  # timezone-aware
        assert parsed.tzinfo == timezone.utc or "+00:00" in ts


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT PG UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════


def _mock_get_session(mock_session):
    """Create a mock context manager for get_session."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class TestAuditPgUnit:
    """Test audit_pg functions with mocked DB sessions."""

    def test_persist_audit_event_writes_row(self):
        """persist_audit_event writes AuditLog row with correct fields."""
        from app.services.audit_pg import persist_audit_event

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        cm = _mock_get_session(mock_session)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            _run(persist_audit_event("login_attempt", ip="10.0.0.1", path="/api/auth"))

        mock_session.add.assert_called_once()
        row = mock_session.add.call_args[0][0]
        assert row.event_type == "login_attempt"
        assert row.ip == "10.0.0.1"
        assert row.path == "/api/auth"

    def test_persist_audit_event_no_ip_path(self):
        """persist_audit_event with no ip/path stores None."""
        from app.services.audit_pg import persist_audit_event

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        cm = _mock_get_session(mock_session)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            _run(persist_audit_event("system_start"))

        row = mock_session.add.call_args[0][0]
        assert row.ip is None
        assert row.path is None

    def test_persist_audit_event_absorbs_exception(self):
        """persist_audit_event absorbs exception (fire-and-forget)."""
        from app.services.audit_pg import persist_audit_event

        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(side_effect=RuntimeError("DB down"))
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            # Should not raise
            _run(persist_audit_event("test_event", ip="1.2.3.4"))

    def test_get_recent_events_returns_chronological(self):
        """get_recent_events returns list ordered chronologically."""
        from app.services.audit_pg import get_recent_events

        ts1 = datetime(2026, 1, 1, 10, 0, 0)
        ts2 = datetime(2026, 1, 1, 11, 0, 0)

        row1 = MagicMock()
        row1.timestamp = ts1
        row1.event_type = "event_a"
        row1.ip = None
        row1.path = None
        row1.details = None

        row2 = MagicMock()
        row2.timestamp = ts2
        row2.event_type = "event_b"
        row2.ip = None
        row2.path = None
        row2.details = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        # order_by desc means row2 first, row1 second
        mock_scalars.all.return_value = [row2, row1]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        cm = _mock_get_session(mock_session)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            events = _run(get_recent_events(limit=10))

        # reversed to chronological: event_a first
        assert len(events) == 2
        assert events[0]["event"] == "event_a"
        assert events[1]["event"] == "event_b"

    def test_get_recent_events_empty_on_exception(self):
        """get_recent_events returns empty list on DB exception."""
        from app.services.audit_pg import get_recent_events

        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(side_effect=RuntimeError("DB fail"))
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            events = _run(get_recent_events())

        assert events == []

    def test_cleanup_old_events_deletes_old_rows(self):
        """cleanup_old_events deletes rows older than retention_days."""
        from app.services.audit_pg import cleanup_old_events

        mock_session = AsyncMock()
        mock_exec_result = MagicMock()
        mock_exec_result.rowcount = 5
        mock_session.execute = AsyncMock(return_value=mock_exec_result)

        cm = _mock_get_session(mock_session)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            count = _run(cleanup_old_events(retention_days=30))

        assert count == 5
        mock_session.execute.assert_called_once()

    def test_cleanup_old_events_returns_0_on_exception(self):
        """cleanup_old_events returns 0 on DB exception."""
        from app.services.audit_pg import cleanup_old_events

        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(side_effect=RuntimeError("DB fail"))
        cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.audit_pg.get_session", return_value=cm):
            count = _run(cleanup_old_events())

        assert count == 0

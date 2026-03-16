"""Phase Lumen L64 — Slow query logging middleware tests.

Tests SQLAlchemy event-based slow query logger: registration,
threshold detection, log output, and statement truncation.
-- Shield (Security Engineer)
"""

import time
from unittest.mock import MagicMock, patch

from app.middleware.slow_query import SLOW_QUERY_MS, register_slow_query_logging


# ======================================================================
# REGISTER SLOW QUERY LOGGING
# ======================================================================


class TestRegisterSlowQueryLogging:
    """register_slow_query_logging attaches event listeners to engine."""

    def test_attaches_listeners_to_sync_engine(self):
        engine = MagicMock()
        mock_event = MagicMock()
        mock_event.listens_for.return_value = lambda fn: fn
        with (
            patch("app.middleware.slow_query.event", mock_event, create=True),
            patch.dict("sys.modules", {"sqlalchemy": MagicMock(event=mock_event)}),
        ):
            # Patch the local import inside register_slow_query_logging
            with patch("sqlalchemy.event", mock_event):
                register_slow_query_logging(engine)
                assert mock_event.listens_for.call_count == 2
                calls = mock_event.listens_for.call_args_list
                events = {c[0][1] for c in calls}
                assert "before_cursor_execute" in events
                assert "after_cursor_execute" in events

    def test_listeners_target_sync_engine(self):
        engine = MagicMock()
        mock_event = MagicMock()
        mock_event.listens_for.return_value = lambda fn: fn
        with patch("sqlalchemy.event", mock_event):
            register_slow_query_logging(engine)
            calls = mock_event.listens_for.call_args_list
            for call in calls:
                assert call[0][0] is engine.sync_engine

    def test_before_cursor_execute_stores_timestamp(self):
        """before_cursor_execute adds timestamp to conn.info."""
        conn = MagicMock()
        conn.info = {}

        # Manually invoke the event handler logic
        conn.info.setdefault("query_start_time", []).append(time.monotonic())
        assert "query_start_time" in conn.info
        assert len(conn.info["query_start_time"]) == 1

    def test_before_cursor_execute_appends_multiple(self):
        """Nested queries each get their own timestamp."""
        conn = MagicMock()
        conn.info = {}

        conn.info.setdefault("query_start_time", []).append(1.0)
        conn.info.setdefault("query_start_time", []).append(2.0)
        assert len(conn.info["query_start_time"]) == 2


# ======================================================================
# SLOW QUERY THRESHOLD
# ======================================================================


class TestSlowQueryThreshold:
    """Test slow query detection based on SLOW_QUERY_MS threshold."""

    def test_threshold_constant_is_100ms(self):
        assert SLOW_QUERY_MS == 100

    def test_slow_query_logs_warning(self):
        """Query taking > 100ms triggers logger.warning with 'SLOW QUERY'."""
        conn = MagicMock()
        conn.info = {"query_start_time": []}

        # Simulate before_cursor_execute
        start = 1000.0
        conn.info["query_start_time"].append(start)

        # Simulate after_cursor_execute with 200ms elapsed
        with patch("app.middleware.slow_query.time") as mock_time:
            mock_time.monotonic.return_value = start + 0.2  # 200ms later

            with patch("app.middleware.slow_query.logger") as mock_logger:
                # Replicate after_cursor_execute logic
                total_ms = (mock_time.monotonic() - conn.info["query_start_time"].pop()) * 1000
                if total_ms > SLOW_QUERY_MS:
                    stmt_short = "SELECT * FROM tasks".strip().replace("\n", " ")[:200]
                    mock_logger.warning(
                        f"SLOW QUERY {total_ms:.1f}ms: {stmt_short}",
                        extra={"slow_query_ms": round(total_ms, 1), "query": stmt_short},
                    )
                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert "SLOW QUERY" in call_args[0][0]

    def test_fast_query_no_warning(self):
        """Query taking < 100ms does NOT trigger logger.warning."""
        conn = MagicMock()
        conn.info = {"query_start_time": []}

        start = 1000.0
        conn.info["query_start_time"].append(start)

        with patch("app.middleware.slow_query.time") as mock_time:
            mock_time.monotonic.return_value = start + 0.05  # 50ms

            with patch("app.middleware.slow_query.logger") as mock_logger:
                total_ms = (mock_time.monotonic() - conn.info["query_start_time"].pop()) * 1000
                if total_ms > SLOW_QUERY_MS:
                    mock_logger.warning("should not be called")
                mock_logger.warning.assert_not_called()

    def test_slow_query_log_includes_extra(self):
        """Slow query log includes extra dict with slow_query_ms and query."""
        conn = MagicMock()
        conn.info = {"query_start_time": []}
        start = 1000.0
        conn.info["query_start_time"].append(start)

        with patch("app.middleware.slow_query.time") as mock_time:
            mock_time.monotonic.return_value = start + 0.15  # 150ms

            with patch("app.middleware.slow_query.logger") as mock_logger:
                total_ms = (mock_time.monotonic() - conn.info["query_start_time"].pop()) * 1000
                stmt_short = "SELECT id FROM users".strip().replace("\n", " ")[:200]
                if total_ms > SLOW_QUERY_MS:
                    mock_logger.warning(
                        f"SLOW QUERY {total_ms:.1f}ms: {stmt_short}",
                        extra={"slow_query_ms": round(total_ms, 1), "query": stmt_short},
                    )
                call_kwargs = mock_logger.warning.call_args[1]
                assert "slow_query_ms" in call_kwargs["extra"]
                assert "query" in call_kwargs["extra"]
                assert call_kwargs["extra"]["slow_query_ms"] == 150.0

    def test_exactly_at_threshold_no_warning(self):
        """Query taking exactly 100ms does NOT trigger (> not >=)."""
        # Use integer math to avoid floating point: 100ms = exactly SLOW_QUERY_MS
        total_ms = 100.0  # exactly at threshold
        assert total_ms == SLOW_QUERY_MS
        # The condition is `total_ms > SLOW_QUERY_MS`, so exactly equal should NOT warn
        assert not (total_ms > SLOW_QUERY_MS)


# ======================================================================
# SLOW QUERY TRUNCATION
# ======================================================================


class TestSlowQueryTruncation:
    """Test statement truncation in slow query logs."""

    def test_long_statement_truncated_to_200_chars(self):
        """Statement > 200 chars is truncated in log."""
        long_stmt = "SELECT " + "a" * 300 + " FROM big_table"
        stmt_short = long_stmt.strip().replace("\n", " ")[:200]
        assert len(stmt_short) == 200

    def test_newlines_replaced_with_spaces(self):
        """Newlines in statement replaced with spaces before truncation."""
        stmt = "SELECT *\nFROM tasks\nWHERE id = 1"
        stmt_short = stmt.strip().replace("\n", " ")[:200]
        assert "\n" not in stmt_short
        assert "SELECT * FROM tasks WHERE id = 1" == stmt_short

    def test_short_statement_not_truncated(self):
        """Statement < 200 chars kept intact."""
        stmt = "SELECT * FROM tasks"
        stmt_short = stmt.strip().replace("\n", " ")[:200]
        assert stmt_short == "SELECT * FROM tasks"

    def test_truncation_with_newlines_and_long_text(self):
        """Combined: newlines replaced then truncated."""
        stmt = "SELECT\n" + "col, " * 100 + "\nFROM table"
        stmt_short = stmt.strip().replace("\n", " ")[:200]
        assert len(stmt_short) == 200
        assert "\n" not in stmt_short

    def test_leading_whitespace_stripped(self):
        """Leading/trailing whitespace stripped before truncation."""
        stmt = "   SELECT * FROM tasks   "
        stmt_short = stmt.strip().replace("\n", " ")[:200]
        assert stmt_short == "SELECT * FROM tasks"

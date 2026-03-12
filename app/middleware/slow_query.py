"""SQLAlchemy event-based slow query logger."""
import logging
import time

logger = logging.getLogger("subtitle-generator")

SLOW_QUERY_MS = 100  # Log queries slower than this


def register_slow_query_logging(engine):
    """Attach slow query logging to a SQLAlchemy async engine."""
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.monotonic())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_ms = (time.monotonic() - conn.info["query_start_time"].pop()) * 1000
        if total_ms > SLOW_QUERY_MS:
            # Truncate long queries for log readability
            stmt_short = statement.strip().replace("\n", " ")[:200]
            logger.warning(
                f"SLOW QUERY {total_ms:.1f}ms: {stmt_short}",
                extra={"slow_query_ms": round(total_ms, 1), "query": stmt_short}
            )

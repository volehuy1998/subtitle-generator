"""SQLite-backed analytics persistence.

Provides durable storage for analytics data that survives restarts.
Uses a simple SQLite database with one table per metric type.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone

from app.config import BASE_DIR

logger = logging.getLogger("subtitle-generator")
_lock = threading.Lock()

DB_PATH = BASE_DIR / "analytics.db"

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    """Get or create the SQLite connection."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_tables(_conn)
    return _conn


def _init_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            data TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_ts ON analytics_events(timestamp);

        CREATE TABLE IF NOT EXISTS analytics_daily (
            date TEXT PRIMARY KEY,
            uploads INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            total_processing_sec REAL DEFAULT 0,
            data TEXT DEFAULT '{}'
        );
    """)
    conn.commit()


def record_event(event_type: str, data: dict | None = None):
    """Record an analytics event to SQLite."""
    now = datetime.now(tz=timezone.utc).isoformat()
    payload = json.dumps(data or {}, default=str)
    with _lock:
        try:
            conn = _get_conn()
            conn.execute(
                "INSERT INTO analytics_events (timestamp, event_type, data) VALUES (?, ?, ?)",
                (now, event_type, payload),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"ANALYTICS_DB Failed to record event: {e}")


def update_daily_stats(uploads: int = 0, completed: int = 0, failed: int = 0,
                       processing_sec: float = 0):
    """Update daily aggregated stats."""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        try:
            conn = _get_conn()
            conn.execute("""
                INSERT INTO analytics_daily (date, uploads, completed, failed, total_processing_sec)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    uploads = uploads + excluded.uploads,
                    completed = completed + excluded.completed,
                    failed = failed + excluded.failed,
                    total_processing_sec = total_processing_sec + excluded.total_processing_sec
            """, (today, uploads, completed, failed, processing_sec))
            conn.commit()
        except Exception as e:
            logger.error(f"ANALYTICS_DB Failed to update daily stats: {e}")


def get_daily_stats(days: int = 30) -> list[dict]:
    """Get daily aggregated stats for the last N days."""
    with _lock:
        try:
            conn = _get_conn()
            rows = conn.execute(
                "SELECT * FROM analytics_daily ORDER BY date DESC LIMIT ?",
                (days,),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"ANALYTICS_DB Failed to get daily stats: {e}")
            return []


def get_event_count(event_type: str | None = None) -> int:
    """Get total event count, optionally filtered by type."""
    with _lock:
        try:
            conn = _get_conn()
            if event_type:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM analytics_events WHERE event_type = ?",
                    (event_type,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM analytics_events").fetchone()
            return row["cnt"] if row else 0
        except Exception as e:
            logger.error(f"ANALYTICS_DB Failed to get event count: {e}")
            return 0


def get_db_info() -> dict:
    """Get database info."""
    exists = DB_PATH.exists()
    size_kb = round(DB_PATH.stat().st_size / 1024, 1) if exists else 0
    event_count = get_event_count() if exists else 0
    return {
        "path": str(DB_PATH),
        "exists": exists,
        "size_kb": size_kb,
        "total_events": event_count,
    }


def close():
    """Close the database connection."""
    global _conn
    with _lock:
        if _conn:
            _conn.close()
            _conn = None

#!/usr/bin/env python3
"""
One-time cleanup: remove test/placeholder incidents from logs/status.db.

Deletes incidents whose titles are clearly development test entries
(IDs 2–5 created during initial setup: "Test incident", "Test", "test",
"Hello, test !!"). Real incidents (auto-detected connectivity issues,
actual latency reports) are preserved.

Safe to run multiple times — uses DELETE WHERE title IN (...) so it is
idempotent if the rows are already gone.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "logs" / "status.db"

TEST_TITLES = {
    "Test incident",
    "Test",
    "test",
    "Hello, test !!",
}

def main():
    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH} — nothing to do.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        # Find matching incident IDs first
        placeholders = ",".join("?" for _ in TEST_TITLES)
        rows = conn.execute(
            f"SELECT id, title, severity, status FROM status_incidents WHERE title IN ({placeholders})",
            list(TEST_TITLES),
        ).fetchall()

        if not rows:
            print("No test incidents found — DB is already clean.")
            return

        print(f"Found {len(rows)} test incident(s) to delete:")
        ids_to_delete = []
        for row in rows:
            print(f"  id={row[0]} title={row[1]!r} severity={row[2]} status={row[3]}")
            ids_to_delete.append(row[0])

        # Delete child updates first (FK constraint)
        id_placeholders = ",".join("?" for _ in ids_to_delete)
        updates_deleted = conn.execute(
            f"DELETE FROM status_incident_updates WHERE incident_id IN ({id_placeholders})",
            ids_to_delete,
        ).rowcount
        incidents_deleted = conn.execute(
            f"DELETE FROM status_incidents WHERE id IN ({id_placeholders})",
            ids_to_delete,
        ).rowcount

        conn.commit()
        print(f"Deleted {incidents_deleted} incident(s) and {updates_deleted} update(s).")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

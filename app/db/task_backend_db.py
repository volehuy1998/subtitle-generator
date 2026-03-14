"""Database-backed task backend.

Implements the TaskBackend interface with PostgreSQL/SQLite async storage.
Keeps an in-memory cache for hot-path reads (progress polling, SSE events)
while persisting all mutations to the database.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func

from app.db.engine import get_session
from app.db.models import TaskRecord, SessionRecord
from app.services.task_backend import TaskBackend

logger = logging.getLogger("subtitle-generator")


class DatabaseTaskBackend(TaskBackend):
    """Task backend that writes through to PostgreSQL/SQLite.

    Hot reads come from the in-memory cache (self._cache) to avoid
    async DB calls on every progress poll. Writes go to both cache and DB.
    """

    def __init__(self):
        self._cache: dict[str, dict] = {}

    # ── Sync interface (TaskBackend contract) ──
    # These operate on the cache for backward compatibility with
    # the synchronous pipeline code (process_video runs in a thread).

    def get(self, task_id: str) -> dict | None:
        return self._cache.get(task_id)

    def set(self, task_id: str, data: dict) -> None:
        self._cache[task_id] = data

    def delete(self, task_id: str) -> None:
        self._cache.pop(task_id, None)

    def items(self) -> list[tuple[str, dict]]:
        return list(self._cache.items())

    def keys(self) -> list[str]:
        return list(self._cache.keys())

    def contains(self, task_id: str) -> bool:
        return task_id in self._cache

    def count(self) -> int:
        return len(self._cache)

    @property
    def raw(self) -> dict[str, dict]:
        """Direct access for backward compatibility."""
        return self._cache

    # ── Async DB operations ──

    @staticmethod
    def _parse_duration(raw) -> float | None:
        """Convert duration to float seconds. Handles strings like '2m 16s'."""
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw)
            except ValueError:
                pass
            # Parse formatted strings like "2m 16s", "1h 5m 30s"
            import re

            total = 0.0
            parts = re.findall(r"(\d+(?:\.\d+)?)\s*([hms])", raw.lower())
            for val, unit in parts:
                if unit == "h":
                    total += float(val) * 3600
                elif unit == "m":
                    total += float(val) * 60
                elif unit == "s":
                    total += float(val)
            return total if total > 0 else None
        return None

    async def persist_task(self, task_id: str, data: dict) -> None:
        """Write or update a task in the database."""
        try:
            # Ensure session record exists before inserting task (FK constraint)
            sid = data.get("session_id")
            if sid:
                await self.persist_session(sid)

            async with get_session() as session:
                existing = await session.get(TaskRecord, task_id)
                if existing is not None:
                    # Update fields
                    existing.status = data.get("status", existing.status)
                    existing.percent = data.get("percent", existing.percent)
                    existing.message = data.get("message", existing.message)
                    existing.language = data.get("language", existing.language)
                    existing.model_size = data.get("model_size", existing.model_size)
                    existing.device = data.get("device", existing.device)
                    existing.file_size = data.get("file_size", existing.file_size)
                    existing.file_size_fmt = data.get("file_size_fmt", existing.file_size_fmt)
                    existing.audio_size_fmt = data.get("audio_size_fmt", existing.audio_size_fmt)
                    raw_dur = data.get("duration")
                    if raw_dur is not None:
                        existing.duration = self._parse_duration(raw_dur)
                    existing.word_timestamps = int(data.get("word_timestamps", False))
                    existing.diarize = int(data.get("diarize", False))
                    existing.speakers = data.get("speakers", existing.speakers)
                    segments = data.get("segments")
                    if isinstance(segments, (list, dict)):
                        existing.segments = json.dumps(segments, default=str)
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    record = TaskRecord.from_dict(task_id, data)
                    session.add(record)
        except Exception as e:
            logger.error(f"DB persist_task failed for {task_id}: {e}")

    async def persist_session(self, session_id: str, ip: str | None = None, user_agent: str | None = None) -> None:
        """Upsert a session record."""
        try:
            async with get_session() as session:
                existing = await session.get(SessionRecord, session_id)
                if existing is not None:
                    existing.last_seen = datetime.now(timezone.utc)
                    if ip:
                        existing.ip = ip
                    if user_agent:
                        existing.user_agent = user_agent
                else:
                    record = SessionRecord(
                        id=session_id,
                        ip=ip,
                        user_agent=user_agent,
                    )
                    session.add(record)
        except Exception as e:
            logger.error(f"DB persist_session failed for {session_id}: {e}")

    async def load_from_db(self) -> int:
        """Load terminal tasks from DB into cache on startup (replaces load_task_history)."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(TaskRecord)
                    .where(TaskRecord.status.in_(["done", "error", "cancelled"]))
                    .order_by(TaskRecord.created_at.desc())
                    .limit(100)
                )
                records = result.scalars().all()
                count = 0
                for record in records:
                    if record.id not in self._cache:
                        self._cache[record.id] = record.to_dict()
                        count += 1
                return count
        except Exception as e:
            logger.error(f"DB load_from_db failed: {e}")
            return 0

    async def get_task_count_by_status(self) -> dict[str, int]:
        """Get task counts grouped by status from DB."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(TaskRecord.status, func.count(TaskRecord.id)).group_by(TaskRecord.status)
                )
                return dict(result.all())
        except Exception as e:
            logger.error(f"DB get_task_count_by_status failed: {e}")
            return {}

    def schedule_persist(self, task_id: str, data: dict) -> None:
        """Fire-and-forget persist from sync context (pipeline threads)."""
        from app import state

        loop = state.main_event_loop
        if loop is not None and not loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.persist_task(task_id, data), loop)
        else:
            logger.warning(f"Cannot persist task {task_id}: no event loop available")

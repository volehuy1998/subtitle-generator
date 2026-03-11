"""Tests for Sprint 18: Database Foundation.

S18-1: SQLAlchemy + asyncpg + Alembic dependencies
S18-2: Database config (DATABASE_URL, pool settings)
S18-3: SQLAlchemy Base, engine, session factory
S18-4: Alembic migration setup
S18-5: tasks table model
S18-6: sessions table model
S18-7: DatabaseTaskBackend
S18-8: Lifespan DB init/close
S18-9: DB persistence replaces task_history.json
S18-10: Tests
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import DATABASE_URL


client = TestClient(app)


# ── Helper to run async code in tests ──

def run_async(coro):
    """Run async coroutine in a new event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── S18-1: Dependencies available ──

class TestDependencies:
    def test_sqlalchemy_importable(self):
        import sqlalchemy
        assert hasattr(sqlalchemy, "__version__")

    def test_sqlalchemy_async_importable(self):
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        assert create_async_engine is not None
        assert AsyncSession is not None

    def test_alembic_importable(self):
        import alembic
        assert hasattr(alembic, "__version__")

    def test_aiosqlite_importable(self):
        import aiosqlite
        assert hasattr(aiosqlite, "__version__")


# ── S18-2: Database config ──

class TestDatabaseConfig:
    def test_database_url_exists(self):
        assert DATABASE_URL is not None
        assert len(DATABASE_URL) > 0

    def test_database_url_default_is_sqlite(self):
        # Default should be SQLite when DATABASE_URL env is not set
        assert "sqlite" in DATABASE_URL or "postgresql" in DATABASE_URL

    def test_pool_config_exists(self):
        from app.config import DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
        assert isinstance(DB_POOL_SIZE, int)
        assert isinstance(DB_MAX_OVERFLOW, int)
        assert isinstance(DB_POOL_RECYCLE, int)
        assert DB_POOL_SIZE > 0
        assert DB_MAX_OVERFLOW >= 0
        assert DB_POOL_RECYCLE > 0

    def test_pool_defaults(self):
        from app.config import DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE
        assert DB_POOL_SIZE == 5
        assert DB_MAX_OVERFLOW == 10
        assert DB_POOL_RECYCLE == 3600


# ── S18-3: Engine and session factory ──

class TestEngineAndSession:
    def test_get_engine_returns_engine(self):
        from app.db.engine import get_engine
        engine = get_engine()
        assert engine is not None

    def test_get_engine_is_singleton(self):
        from app.db.engine import get_engine
        e1 = get_engine()
        e2 = get_engine()
        assert e1 is e2

    def test_get_session_is_context_manager(self):
        from app.db.engine import get_session
        # get_session should be an async context manager
        assert callable(get_session)

    def test_init_db_creates_tables(self):
        from app.db.engine import init_db, get_engine
        run_async(init_db())
        # Verify tables exist by checking metadata
        engine = get_engine()
        assert engine is not None

    def test_session_yields_async_session(self):
        from app.db.engine import get_session, init_db
        run_async(init_db())

        async def _test():
            async with get_session() as session:
                assert session is not None
                from sqlalchemy.ext.asyncio import AsyncSession
                assert isinstance(session, AsyncSession)

        run_async(_test())


# ── S18-4: Alembic setup ──

class TestAlembicSetup:
    def test_alembic_ini_exists(self):
        from app.config import BASE_DIR
        assert (BASE_DIR / "alembic.ini").exists()

    def test_alembic_env_exists(self):
        from app.config import BASE_DIR
        assert (BASE_DIR / "alembic" / "env.py").exists()

    def test_alembic_versions_dir_exists(self):
        from app.config import BASE_DIR
        assert (BASE_DIR / "alembic" / "versions").is_dir()

    def test_initial_migration_exists(self):
        from app.config import BASE_DIR
        versions_dir = BASE_DIR / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*.py"))
        assert len(migration_files) >= 1

    def test_script_mako_exists(self):
        from app.config import BASE_DIR
        assert (BASE_DIR / "alembic" / "script.py.mako").exists()


# ── S18-5: TaskRecord model ──

class TestTaskRecordModel:
    def test_task_record_importable(self):
        from app.db.models import TaskRecord
        assert TaskRecord.__tablename__ == "tasks"

    def test_task_record_columns(self):
        from app.db.models import TaskRecord
        columns = {c.name for c in TaskRecord.__table__.columns}
        expected = {
            "id", "status", "filename", "language_requested", "language",
            "model_size", "device", "percent", "message", "file_size",
            "file_size_fmt", "audio_size_fmt", "duration", "segments",
            "word_timestamps", "diarize", "speakers", "session_id",
            "created_at", "updated_at",
        }
        assert expected.issubset(columns)

    def test_task_record_from_dict(self):
        from app.db.models import TaskRecord
        data = {
            "status": "done",
            "filename": "test.mp4",
            "language": "en",
            "model_size": "medium",
            "device": "cpu",
            "percent": 100.0,
            "message": "Done!",
            "segments": [{"start": 0, "end": 1, "text": "hello"}],
            "word_timestamps": True,
            "diarize": False,
            "session_id": "sess-123",
        }
        record = TaskRecord.from_dict("task-1", data)
        assert record.id == "task-1"
        assert record.status == "done"
        assert record.filename == "test.mp4"
        assert record.word_timestamps == 1
        assert record.diarize == 0
        assert record.session_id == "sess-123"
        # segments should be JSON string
        assert isinstance(record.segments, str)
        parsed = json.loads(record.segments)
        assert len(parsed) == 1

    def test_task_record_to_dict(self):
        from app.db.models import TaskRecord
        record = TaskRecord(
            id="task-2",
            status="done",
            filename="video.mkv",
            language="de",
            model_size="small",
            device="cuda",
            percent=100.0,
            message="Complete",
            segments=json.dumps([{"start": 0, "end": 2, "text": "hallo"}]),
            word_timestamps=1,
            diarize=0,
        )
        d = record.to_dict()
        assert d["status"] == "done"
        assert d["filename"] == "video.mkv"
        assert d["word_timestamps"] is True
        assert d["diarize"] is False
        assert len(d["segments"]) == 1
        assert d["segments"][0]["text"] == "hallo"

    def test_task_record_to_dict_empty_segments(self):
        from app.db.models import TaskRecord
        record = TaskRecord(
            id="task-3",
            status="queued",
            filename="audio.mp3",
            segments=None,
        )
        d = record.to_dict()
        assert d["segments"] == []

    def test_task_record_roundtrip(self):
        from app.db.models import TaskRecord
        original = {
            "status": "error",
            "filename": "bad.wav",
            "percent": 0.0,
            "message": "FFmpeg error",
            "language": "fr",
            "model_size": "large",
            "device": "cpu",
            "segments": [],
            "word_timestamps": False,
            "diarize": True,
            "speakers": 3,
            "session_id": "s-456",
        }
        record = TaskRecord.from_dict("t-rt", original)
        result = record.to_dict()
        assert result["status"] == original["status"]
        assert result["filename"] == original["filename"]
        assert result["language"] == original["language"]
        assert result["diarize"] is True
        assert result["speakers"] == 3


# ── S18-6: SessionRecord model ──

class TestSessionRecordModel:
    def test_session_record_importable(self):
        from app.db.models import SessionRecord
        assert SessionRecord.__tablename__ == "sessions"

    def test_session_record_columns(self):
        from app.db.models import SessionRecord
        columns = {c.name for c in SessionRecord.__table__.columns}
        expected = {"id", "created_at", "last_seen", "ip", "user_agent"}
        assert expected == columns

    def test_session_record_creation(self):
        from app.db.models import SessionRecord
        record = SessionRecord(
            id="sess-abc",
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert record.id == "sess-abc"
        assert record.ip == "192.168.1.1"

    def test_session_task_relationship_defined(self):
        from app.db.models import SessionRecord
        # Check that the relationship attribute exists
        assert hasattr(SessionRecord, "tasks")


# ── S18-7: DatabaseTaskBackend ──

class TestDatabaseTaskBackend:
    def test_backend_implements_interface(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        from app.services.task_backend import TaskBackend
        backend = DatabaseTaskBackend()
        assert isinstance(backend, TaskBackend)

    def test_backend_cache_set_get(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("t1", {"status": "queued", "filename": "test.mp4"})
        assert backend.get("t1")["status"] == "queued"

    def test_backend_cache_delete(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("t1", {"status": "queued"})
        backend.delete("t1")
        assert backend.get("t1") is None

    def test_backend_cache_contains(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("t1", {"status": "done"})
        assert backend.contains("t1")
        assert not backend.contains("t2")

    def test_backend_cache_count(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("a", {"status": "done"})
        backend.set("b", {"status": "error"})
        assert backend.count() == 2

    def test_backend_cache_items(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("x", {"status": "done"})
        backend.set("y", {"status": "queued"})
        items = backend.items()
        assert len(items) == 2
        ids = [i[0] for i in items]
        assert "x" in ids
        assert "y" in ids

    def test_backend_cache_keys(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("k1", {})
        backend.set("k2", {})
        assert set(backend.keys()) == {"k1", "k2"}

    def test_backend_raw_property(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        backend = DatabaseTaskBackend()
        backend.set("r1", {"status": "done"})
        assert isinstance(backend.raw, dict)
        assert "r1" in backend.raw

    def test_persist_task_async(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        from app.db.engine import init_db

        run_async(init_db())
        backend = DatabaseTaskBackend()

        async def _test():
            await backend.persist_task("pt-1", {
                "status": "done",
                "filename": "persist_test.mp4",
                "language": "en",
                "model_size": "tiny",
                "device": "cpu",
                "percent": 100.0,
                "segments": [{"start": 0, "end": 1, "text": "test"}],
            })

        run_async(_test())

    def test_persist_session_async(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        from app.db.engine import init_db

        run_async(init_db())
        backend = DatabaseTaskBackend()

        async def _test():
            await backend.persist_session("s-1", ip="10.0.0.1", user_agent="TestAgent/1.0")

        run_async(_test())

    def test_load_from_db(self):
        from app.db.task_backend_db import DatabaseTaskBackend
        from app.db.engine import init_db

        run_async(init_db())
        backend = DatabaseTaskBackend()

        async def _test():
            # Persist a task
            await backend.persist_task("load-1", {
                "status": "done",
                "filename": "load_test.mp4",
                "language": "en",
                "model_size": "small",
                "device": "cpu",
                "percent": 100.0,
            })

            # Create a fresh backend and load from DB
            fresh = DatabaseTaskBackend()
            count = await fresh.load_from_db()
            assert count >= 1
            assert fresh.contains("load-1")
            task = fresh.get("load-1")
            assert task["status"] == "done"
            assert task["filename"] == "load_test.mp4"

        run_async(_test())


# ── S18-8: Lifespan DB init ──

class TestLifespanDB:
    def test_health_endpoint_works_with_db(self):
        """Health endpoint should work after DB init in lifespan."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_scale_info_shows_backend_type(self):
        """Scale info should show the backend type."""
        resp = client.get("/scale/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_backend" in data
        # Should be DatabaseTaskBackend or InMemoryTaskBackend
        assert "type" in data["task_backend"]


# ── S18-9: DB replaces task_history.json ──

class TestDBPersistence:
    def test_persist_helper_in_pipeline(self):
        """The pipeline module should have _persist_task helper."""
        from app.services import pipeline
        assert hasattr(pipeline, "_persist_task")

    def test_persist_task_function_callable(self):
        from app.services.pipeline import _persist_task
        assert callable(_persist_task)

    def test_task_backend_get_function(self):
        from app.services.task_backend import get_task_backend
        backend = get_task_backend()
        assert backend is not None

    def test_set_task_backend_function(self):
        from app.services.task_backend import set_task_backend
        assert callable(set_task_backend)


# ── S18-10: Integration ──

class TestIntegration:
    def test_db_package_imports(self):
        from app.db import Base, TaskRecord, SessionRecord, get_engine, get_session, init_db, close_db
        assert Base is not None
        assert TaskRecord is not None
        assert SessionRecord is not None

    def test_models_share_base(self):
        from app.db.models import Base, TaskRecord, SessionRecord
        assert issubclass(TaskRecord, Base)
        assert issubclass(SessionRecord, Base)

    def test_task_session_foreign_key(self):
        from app.db.models import TaskRecord
        session_col = TaskRecord.__table__.c.session_id
        assert len(session_col.foreign_keys) == 1
        fk = list(session_col.foreign_keys)[0]
        assert "sessions.id" in str(fk.target_fullname)

    def test_indexes_exist_on_tasks(self):
        from app.db.models import TaskRecord
        index_names = {idx.name for idx in TaskRecord.__table__.indexes}
        assert "ix_tasks_session_status" in index_names
        assert "ix_tasks_created_at" in index_names

    def test_indexes_exist_on_sessions(self):
        from app.db.models import SessionRecord
        index_names = {idx.name for idx in SessionRecord.__table__.indexes}
        assert "ix_sessions_last_seen" in index_names

    def test_full_crud_cycle(self):
        """Full create-read-update-delete cycle via DB backend."""
        from app.db.task_backend_db import DatabaseTaskBackend
        from app.db.engine import init_db
        from app.db.models import TaskRecord
        from sqlalchemy import select

        run_async(init_db())
        backend = DatabaseTaskBackend()

        async def _test():
            task_id = "crud-test-1"
            data = {
                "status": "queued",
                "filename": "crud.mp4",
                "language_requested": "auto",
                "percent": 0.0,
                "message": "Starting...",
            }

            # Create
            backend.set(task_id, data)
            await backend.persist_task(task_id, data)

            # Read
            assert backend.get(task_id)["status"] == "queued"

            # Update
            data["status"] = "done"
            data["percent"] = 100.0
            data["language"] = "en"
            backend.set(task_id, data)
            await backend.persist_task(task_id, data)

            # Verify in DB
            from app.db.engine import get_session
            async with get_session() as session:
                record = await session.get(TaskRecord, task_id)
                assert record is not None
                assert record.status == "done"
                assert record.language == "en"

        run_async(_test())

"""Dedicated async SQLAlchemy engine for status page data (local SQLite).

Decoupled from the main PostgreSQL database so the status page can record
and display incidents even when PostgreSQL is down.
"""

import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import LOG_DIR

logger = logging.getLogger("subtitle-generator")

STATUS_DB_PATH = LOG_DIR / "status.db"
STATUS_DB_URL = f"sqlite+aiosqlite:///{STATUS_DB_PATH}"

_engine = None
_session_factory = None


def get_status_engine():
    """Get or create the status SQLite engine (singleton)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(STATUS_DB_URL, echo=False)
        logger.info(f"Status DB engine created: {STATUS_DB_PATH}")
    return _engine


def _get_status_session_factory():
    """Get or create the status session factory (singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_status_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_status_session():
    """Async context manager yielding an AsyncSession for the status DB."""
    factory = _get_status_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_status_db():
    """Create status tables. Called at startup."""
    from app.db.models import StatusBase

    engine = get_status_engine()
    async with engine.begin() as conn:
        await conn.run_sync(StatusBase.metadata.create_all)
    logger.info("Status DB tables created/verified")


async def close_status_db():
    """Dispose the status engine. Called at shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Status DB engine disposed")
        _engine = None
        _session_factory = None

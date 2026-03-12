"""Async SQLAlchemy engine and session factory."""

import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE

logger = logging.getLogger("subtitle-generator")

_engine = None
_session_factory = None


def get_engine():
    """Get or create the async engine (singleton)."""
    global _engine
    if _engine is None:
        # SQLite doesn't support pool_size/max_overflow/pool_recycle
        is_sqlite = DATABASE_URL.startswith("sqlite")
        kwargs = {
            "echo": False,
        }
        if not is_sqlite:
            kwargs.update({
                "pool_size": DB_POOL_SIZE,
                "max_overflow": DB_MAX_OVERFLOW,
                "pool_recycle": DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            })
        _engine = create_async_engine(DATABASE_URL, **kwargs)
        logger.info(f"DB Engine created: {DATABASE_URL.split('://')[0]}")
        from app.middleware.slow_query import register_slow_query_logging
        register_slow_query_logging(_engine)
    return _engine


def _get_session_factory():
    """Get or create the session factory (singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_session():
    """Async context manager yielding an AsyncSession."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables. Used at startup."""
    from app.db.models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB Tables created/verified")


async def close_db():
    """Dispose the engine. Used at shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("DB Engine disposed")
        _engine = None
        _session_factory = None

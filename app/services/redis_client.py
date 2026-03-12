"""Redis client singleton for shared state, Pub/Sub, and caching."""

import logging

import redis.asyncio as aioredis
import redis as sync_redis

from app.config import REDIS_URL

logger = logging.getLogger("subtitle-generator")

# Async client (for web servers: SSE, routes, etc.)
_async_client: aioredis.Redis | None = None

# Sync client (for workers: pipeline runs in threads)
_sync_client: sync_redis.Redis | None = None


def get_async_redis() -> aioredis.Redis:
    """Get the async Redis client (for use in async contexts)."""
    global _async_client
    if _async_client is None:
        if not REDIS_URL:
            raise RuntimeError("REDIS_URL is not configured")
        _async_client = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
        logger.info(f"REDIS Async client connected to {REDIS_URL.split('@')[-1]}")
    return _async_client


def get_sync_redis() -> sync_redis.Redis:
    """Get the sync Redis client (for use in threads, e.g., pipeline workers)."""
    global _sync_client
    if _sync_client is None:
        if not REDIS_URL:
            raise RuntimeError("REDIS_URL is not configured")
        _sync_client = sync_redis.from_url(
            REDIS_URL,
            decode_responses=True,
            max_connections=10,
        )
        logger.info(f"REDIS Sync client connected to {REDIS_URL.split('@')[-1]}")
    return _sync_client


async def close_async_redis():
    """Close the async Redis connection."""
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None


def close_sync_redis():
    """Close the sync Redis connection."""
    global _sync_client
    if _sync_client is not None:
        _sync_client.close()
        _sync_client = None

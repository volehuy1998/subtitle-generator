"""In-memory TTL cache for async route handlers.

Provides a decorator that caches JSON-serializable responses keyed by
request path + query string.  Thread-safe via asyncio.Lock (one lock per
decorated function).  No external dependencies — just a dict + timestamps.

— Forge (Sr. Backend)
"""

import asyncio
import functools
import logging
import time
from typing import Any

logger = logging.getLogger("subtitle-generator")

# Global registry so cache_clear() can reach every decorated function's store.
_caches: dict[str, dict[str, tuple[float, Any]]] = {}
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(name: str) -> asyncio.Lock:
    """Lazily create an asyncio.Lock for *name* (safe pre-event-loop)."""
    if name not in _locks:
        _locks[name] = asyncio.Lock()
    return _locks[name]


def ttl_cache(seconds: int):
    """Decorator: cache the return value of an async route handler for *seconds*.

    The cache key is derived from the request path and query string.  The
    decorated function **must** accept ``request`` as a keyword argument or
    as the first positional argument (FastAPI injects it automatically when
    the parameter is typed ``Request``).

    Usage::

        @router.get("/languages")
        @ttl_cache(seconds=3600)
        async def languages(request: Request):
            ...
    """

    def decorator(fn):
        cache_name = f"{fn.__module__}.{fn.__qualname__}"
        store: dict[str, tuple[float, Any]] = {}
        _caches[cache_name] = store

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # Extract the Request object from args/kwargs.
            request = kwargs.get("request") or (args[0] if args else None)
            if request is None:
                # No request available — bypass cache and call directly.
                return await fn(*args, **kwargs)

            key = f"{request.url.path}?{request.url.query}"

            now = time.monotonic()

            # Fast path: check without lock (stale reads are harmless — the
            # worst case is one extra computation).
            cached = store.get(key)
            if cached is not None:
                expires, value = cached
                if now < expires:
                    return value

            # Slow path: acquire lock, recheck, compute if needed.
            lock = _get_lock(cache_name)
            async with lock:
                cached = store.get(key)
                if cached is not None:
                    expires, value = cached
                    if now < expires:
                        return value

                value = await fn(*args, **kwargs)
                store[key] = (now + seconds, value)
                return value

        # Expose per-function clear for convenience.
        wrapper.cache_store = store  # type: ignore[attr-defined]
        wrapper.cache_name = cache_name  # type: ignore[attr-defined]
        return wrapper

    return decorator


def cache_clear(prefix: str | None = None) -> int:
    """Invalidate cached entries.

    * ``prefix=None`` — clear **all** TTL caches.
    * ``prefix="/api/model"`` — clear entries whose key starts with *prefix*.

    Returns the number of entries removed.
    """
    removed = 0
    for _name, store in _caches.items():
        if prefix is None:
            removed += len(store)
            store.clear()
        else:
            keys_to_drop = [k for k in store if k.startswith(prefix)]
            for k in keys_to_drop:
                del store[k]
            removed += len(keys_to_drop)
    return removed

"""API key authentication middleware.

Supports optional API key authentication for programmatic access.
When API_KEYS environment variable is set (comma-separated), all
non-public endpoints require a valid key via X-API-Key header or
?api_key query parameter.

Public endpoints (no auth required): GET /, /health, /ready, /metrics, /system-info
"""

import logging
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.audit import log_audit_event
from app.middleware.brute_force import record_auth_failure

logger = logging.getLogger("subtitle-generator")

# Public paths that never require authentication
PUBLIC_PATHS = {"/", "/health", "/ready", "/metrics", "/system-info", "/languages",
                "/docs", "/openapi.json", "/redoc", "/dashboard", "/dashboard/data",
                "/analytics", "/analytics/summary", "/analytics/timeseries",
                "/analytics/users", "/analytics/export",
                "/security/audit", "/health/live", "/health/stream", "/scale/info",
                "/auth/register", "/auth/login", "/auth/logout", "/auth/refresh",
                "/track", "/track/batch",
                "/tasks/search", "/analytics/rollup", "/health/db",
                "/monitoring/metrics", "/monitoring/alerts", "/monitoring/dashboard",
                "/monitoring/thresholds", "/monitoring/performance",
                "/status", "/api/status/page", "/api/status/commits",
                "/api/capabilities"}

# Load API keys from environment (comma-separated)
_api_keys: Optional[set] = None


def _get_api_keys() -> Optional[set]:
    """Get configured API keys. Returns None if auth is disabled."""
    global _api_keys
    if _api_keys is not None:
        return _api_keys if _api_keys else None

    raw = os.environ.get("API_KEYS", "").strip()
    if not raw:
        _api_keys = set()
        return None

    keys = {k.strip() for k in raw.split(",") if k.strip()}
    if not keys:
        _api_keys = set()
        return None

    _api_keys = keys
    logger.info(f"AUTH Loaded {len(keys)} API key(s)")
    return _api_keys


def is_auth_enabled() -> bool:
    """Check if API key authentication is enabled."""
    return _get_api_keys() is not None


def validate_api_key(key: str) -> bool:
    """Validate an API key."""
    keys = _get_api_keys()
    if keys is None:
        return True  # Auth disabled
    return key in keys


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces API key authentication when configured."""

    async def dispatch(self, request: Request, call_next):
        keys = _get_api_keys()

        # If no keys configured, auth is disabled - pass through
        if keys is None:
            return await call_next(request)

        # Public paths don't require auth
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Static files
        if path.startswith("/static"):
            return await call_next(request)

        # Check for API key in header or query parameter
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

        client_ip = request.client.host if request.client else "unknown"

        if not api_key:
            log_audit_event("auth_failure", ip=client_ip, path=path, reason="missing_key")
            record_auth_failure(client_ip)
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required. Provide via X-API-Key header or api_key query parameter."},
            )

        if api_key not in keys:
            logger.warning(f"AUTH Invalid API key from {client_ip}")
            log_audit_event("auth_failure", ip=client_ip, path=path, reason="invalid_key")
            record_auth_failure(client_ip)
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."},
            )

        log_audit_event("auth_success", ip=client_ip, path=path)
        return await call_next(request)

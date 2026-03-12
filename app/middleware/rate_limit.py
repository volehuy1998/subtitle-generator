"""Rate limiting middleware with sliding window and IP filtering.

Enforces per-IP rate limits with proper Retry-After headers,
and checks IP allowlist/blocklist.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.rate_limiter import (
    check_rate_limit,
    get_rate_limit_headers,
    is_ip_allowed,
    DEFAULT_RATE_LIMIT,
    DEFAULT_WINDOW_SEC,
    UPLOAD_RATE_LIMIT,
)
from app.utils.access import get_client_ip

logger = logging.getLogger("subtitle-generator")

# Paths with tighter rate limits
_UPLOAD_PATHS = {"/upload"}
# Paths exempt from rate limiting
_EXEMPT_PATHS = {"/health", "/ready", "/health/live", "/health/stream", "/metrics", "/api/status"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-IP sliding window rate limits."""

    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        path = request.url.path.rstrip("/") or "/"

        # Check IP allowlist/blocklist
        ip_status = is_ip_allowed(client_ip)
        if ip_status is False:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP address blocked."},
            )
        if ip_status is True:
            # Allowlisted IPs bypass rate limits
            return await call_next(request)

        # Exempt paths
        if path in _EXEMPT_PATHS:
            return await call_next(request)

        # Determine rate limit for this path
        if path in _UPLOAD_PATHS:
            limit, window = UPLOAD_RATE_LIMIT, DEFAULT_WINDOW_SEC
            key = f"upload:{client_ip}"
        else:
            limit, window = DEFAULT_RATE_LIMIT, DEFAULT_WINDOW_SEC
            key = f"ip:{client_ip}"

        allowed, info = check_rate_limit(key, limit, window)
        headers = get_rate_limit_headers(info)

        if not allowed:
            logger.warning(f"RATE_LIMIT {client_ip} exceeded {limit}/{window}s on {path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers=headers,
            )

        response = await call_next(request)
        # Add rate limit headers to successful responses
        for k, v in headers.items():
            response.headers[k] = v
        return response

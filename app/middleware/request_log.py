"""HTTP request/response logging middleware with request ID tracing."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_setup import set_request_id
from app.services.analytics import record_request

logger = logging.getLogger("subtitle-generator")

# Paths that generate high-frequency traffic (suppress debug logs)
_QUIET_PATHS = {"/progress/", "/events/", "/tasks", "/favicon.ico", "/track"}


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Assign unique request ID for tracing
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        set_request_id(req_id)

        start = time.time()
        is_quiet = any(p in request.url.path for p in _QUIET_PATHS)
        client_ip = request.client.host if request.client else "unknown"

        # Track request for analytics (skip high-frequency paths)
        if not is_quiet:
            user_agent = request.headers.get("User-Agent", "")
            record_request(client_ip=client_ip, user_agent=user_agent)
            logger.debug(f"REQ  {request.method} {request.url.path} from {client_ip} [{req_id}]")

        # L52: Track total request count — Forge (Sr. Backend Engineer)
        from app import state as _state

        _state.total_request_count += 1
        # L56: Track request rate (RPM) — Forge (Sr. Backend Engineer)
        _state.record_request_timestamp()

        try:
            response = await call_next(request)
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            logger.error(
                f"RESP {request.method} {request.url.path} -> 500 ({elapsed_ms:.1f}ms) [{req_id}] "
                f"ERROR: {type(e).__name__}: {e}"
            )
            raise

        elapsed_ms = (time.time() - start) * 1000

        # Add request ID to response headers for client-side correlation
        response.headers["X-Request-ID"] = req_id

        if not is_quiet:
            logger.debug(
                f"RESP {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms) [{req_id}]"
            )
        elif response.status_code >= 400:
            logger.warning(
                f"RESP {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms) [{req_id}]"
            )

        # Log slow requests
        if elapsed_ms > 5000 and not is_quiet:
            logger.warning(f"SLOW {request.method} {request.url.path} took {elapsed_ms:.0f}ms [{req_id}]")

        return response

"""HTTP request/response logging middleware with request ID tracing.

Converted from BaseHTTPMiddleware to pure ASGI for performance.
Includes /health/live short-circuit (returns 200 without traversing middleware stack).
— Forge (Sr. Backend Engineer)
"""

import json
import logging
import time
import uuid

from app.logging_setup import set_request_id
from app.services.analytics import record_request

logger = logging.getLogger("subtitle-generator")

# Paths that generate high-frequency traffic (suppress debug logs)
_QUIET_PATHS = {"/progress/", "/events/", "/tasks", "/favicon.ico", "/track"}

# Pre-built /health/live response
_HEALTH_LIVE_BODY = json.dumps({"status": "ok"}).encode("utf-8")
_HEALTH_LIVE_HEADERS = [
    [b"content-type", b"application/json"],
    [b"content-length", str(len(_HEALTH_LIVE_BODY)).encode()],
]


class RequestLogMiddleware:
    """Log HTTP requests with timing, request ID tracing, and analytics.

    Pure ASGI implementation — no BaseHTTPMiddleware overhead.
    Short-circuits /health/live for zero-overhead liveness probes.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")

        # Step 2.5: Fast-path /health/live — skip ALL middleware and app processing
        if path == "/health/live":
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": _HEALTH_LIVE_HEADERS,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": _HEALTH_LIVE_BODY,
                }
            )
            return

        # Extract or generate request ID
        headers_raw = scope.get("headers", [])
        req_id = None
        for key, value in headers_raw:
            if key == b"x-request-id":
                req_id = value.decode("latin-1")
                break
        if not req_id:
            req_id = str(uuid.uuid4())[:8]

        set_request_id(req_id)

        start = time.time()
        is_quiet = any(p in path for p in _QUIET_PATHS)

        # Extract client IP from scope
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        # Extract method for logging
        method = scope.get("method", "?")

        # Track request for analytics (skip high-frequency paths)
        if not is_quiet:
            user_agent = ""
            for key, value in headers_raw:
                if key == b"user-agent":
                    user_agent = value.decode("latin-1")
                    break
            record_request(client_ip=client_ip, user_agent=user_agent)
            logger.debug(f"REQ  {method} {path} from {client_ip} [{req_id}]")

        # L52: Track total request count — Forge (Sr. Backend Engineer)
        from app import state as _state

        _state.total_request_count += 1
        # L56: Track request rate (RPM) — Forge (Sr. Backend Engineer)
        _state.record_request_timestamp()

        # Capture response status code and inject X-Request-ID header
        response_status = None

        async def send_with_request_id(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", req_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            logger.error(f"RESP {method} {path} -> 500 ({elapsed_ms:.1f}ms) [{req_id}] ERROR: {type(e).__name__}: {e}")
            raise

        elapsed_ms = (time.time() - start) * 1000

        if not is_quiet:
            logger.debug(f"RESP {method} {path} -> {response_status} ({elapsed_ms:.1f}ms) [{req_id}]")
        elif response_status is not None and response_status >= 400:
            logger.warning(f"RESP {method} {path} -> {response_status} ({elapsed_ms:.1f}ms) [{req_id}]")

        # Log slow requests
        if elapsed_ms > 5000 and not is_quiet:
            logger.warning(f"SLOW {method} {path} took {elapsed_ms:.0f}ms [{req_id}]")


# ── Legacy BaseHTTPMiddleware version (kept for rollback reference) ──
#
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
#
# class RequestLogMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
#         set_request_id(req_id)
#         start = time.time()
#         is_quiet = any(p in request.url.path for p in _QUIET_PATHS)
#         client_ip = request.client.host if request.client else "unknown"
#         if not is_quiet:
#             user_agent = request.headers.get("User-Agent", "")
#             record_request(client_ip=client_ip, user_agent=user_agent)
#             logger.debug(f"REQ  {request.method} {request.url.path} from {client_ip} [{req_id}]")
#         from app import state as _state
#         _state.total_request_count += 1
#         _state.record_request_timestamp()
#         try:
#             response = await call_next(request)
#         except Exception as e:
#             elapsed_ms = (time.time() - start) * 1000
#             logger.error(
#                 f"RESP {request.method} {request.url.path} -> 500 ({elapsed_ms:.1f}ms) [{req_id}] "
#                 f"ERROR: {type(e).__name__}: {e}"
#             )
#             raise
#         elapsed_ms = (time.time() - start) * 1000
#         response.headers["X-Request-ID"] = req_id
#         if not is_quiet:
#             logger.debug(
#                 f"RESP {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms) [{req_id}]"
#             )
#         elif response.status_code >= 400:
#             logger.warning(
#                 f"RESP {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms) [{req_id}]"
#             )
#         if elapsed_ms > 5000 and not is_quiet:
#             logger.warning(f"SLOW {request.method} {request.url.path} took {elapsed_ms:.0f}ms [{req_id}]")
#         return response

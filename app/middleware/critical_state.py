"""Critical state middleware — blocks all user-facing operations when the system is unhealthy.

When state.system_critical is True, only health/monitoring endpoints remain
accessible. Everything else returns 503 with the critical reason(s).

Browser clients receive a styled HTML page; API clients receive JSON.

This is the single enforcement point — no individual route needs its own
health checks. The background health monitor (app.services.health_monitor)
continuously evaluates system health and sets/clears the critical flag.

Converted from BaseHTTPMiddleware to pure ASGI for performance
— Forge (Sr. Backend Engineer)
"""

import json
import logging
from pathlib import Path

from app import state

logger = logging.getLogger("subtitle-generator")

# Load critical.html template at import time (cached for the process lifetime).
_TEMPLATE_PATH = Path(__file__).resolve().parent.parent.parent / "templates" / "critical.html"
try:
    _CRITICAL_TEMPLATE = _TEMPLATE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    logger.warning("templates/critical.html not found — browser clients will receive JSON fallback")
    _CRITICAL_TEMPLATE = ""

# Paths that remain accessible during critical state.
# ONLY monitoring/infrastructure — ALL user features are blocked.
_PASSTHROUGH_PREFIXES = (
    "/health",
    "/ready",
    "/status",
    "/api/status",
    "/api/capabilities",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/assets",
    "/favicon",
    "/manifest",
    "/system-info",
    "/languages",
    "/events",
)


def _wants_html_from_headers(headers: list[tuple[bytes, bytes]]) -> bool:
    """Return True if the client prefers HTML (i.e. a browser)."""
    for key, value in headers:
        if key == b"accept":
            return b"text/html" in value
    return False


def _build_critical_html(reasons: list[str]) -> str:
    """Replace {{REASONS}} placeholder with <li> items."""
    if not _CRITICAL_TEMPLATE:
        return ""
    items = "\n".join(f"<li>{reason}</li>" for reason in reasons)
    return _CRITICAL_TEMPLATE.replace("{{REASONS}}", items)


class CriticalStateMiddleware:
    """Block all user-facing requests when the system is in critical state.

    Pure ASGI implementation — no BaseHTTPMiddleware overhead.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not state.system_critical:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/").rstrip("/") or "/"

        # Allow health/monitoring endpoints through
        if any(path.startswith(prefix) for prefix in _PASSTHROUGH_PREFIXES):
            await self.app(scope, receive, send)
            return

        reasons = state.system_critical_reasons if state.system_critical_reasons else ["Unknown"]
        headers_list = scope.get("headers", [])

        # Browser clients get a styled HTML page
        if _wants_html_from_headers(headers_list) and _CRITICAL_TEMPLATE:
            html = _build_critical_html(reasons)
            body = html.encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        [b"content-type", b"text/html; charset=utf-8"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": body,
                }
            )
            return

        # API clients get JSON
        reasons_str = "; ".join(reasons)
        payload = json.dumps(
            {
                "detail": f"Service in critical state — all operations suspended. Reason: {reasons_str}",
                "critical": True,
                "reasons": list(reasons),
            }
        ).encode("utf-8")

        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(payload)).encode()],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": payload,
            }
        )


# ── Legacy BaseHTTPMiddleware version (kept for rollback reference) ──
#
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from starlette.responses import HTMLResponse, JSONResponse
#
# def _wants_html(request: Request) -> bool:
#     accept = request.headers.get("accept", "")
#     return "text/html" in accept
#
# class CriticalStateMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if not state.system_critical:
#             return await call_next(request)
#         path = request.url.path.rstrip("/") or "/"
#         if any(path.startswith(prefix) for prefix in _PASSTHROUGH_PREFIXES):
#             return await call_next(request)
#         reasons = state.system_critical_reasons if state.system_critical_reasons else ["Unknown"]
#         if _wants_html(request) and _CRITICAL_TEMPLATE:
#             html = _build_critical_html(reasons)
#             return HTMLResponse(content=html, status_code=503)
#         reasons_str = "; ".join(reasons)
#         return JSONResponse(
#             status_code=503,
#             content={
#                 "detail": f"Service in critical state — all operations suspended. Reason: {reasons_str}",
#                 "critical": True,
#                 "reasons": list(reasons),
#             },
#         )

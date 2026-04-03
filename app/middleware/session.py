"""Simple session management via cookies.

Assigns a session ID cookie to each visitor. Tasks are associated with
sessions for ownership tracking. No server-side session store (stateless).

Converted from BaseHTTPMiddleware to pure ASGI for performance
— Forge (Sr. Backend Engineer)
"""

import http.cookies
import logging
import uuid

from starlette.requests import Request

logger = logging.getLogger("subtitle-generator")

SESSION_COOKIE = "sg_session"
SESSION_MAX_AGE = 30 * 24 * 3600  # 30 days


def get_session_id(request: Request) -> str:
    """Get session ID from request cookie, or return empty string."""
    return request.cookies.get(SESSION_COOKIE, "")


def _parse_cookie_header(headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    """Extract cookies from raw ASGI headers."""
    for key, value in headers:
        if key == b"cookie":
            cookie = http.cookies.SimpleCookie(value.decode("latin-1"))
            return {k: v.value for k, v in cookie.items()}
    return {}


class SessionMiddleware:
    """Assigns a session cookie to each visitor.

    Pure ASGI implementation — no BaseHTTPMiddleware overhead.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers_raw = scope.get("headers", [])
        cookies = _parse_cookie_header(headers_raw)
        session_id = cookies.get(SESSION_COOKIE)
        is_new = False

        if not session_id:
            session_id = str(uuid.uuid4())
            is_new = True

        # Store session_id on scope state for route access via request.state.session_id
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["session_id"] = session_id

        if not is_new:
            await self.app(scope, receive, send)
            return

        # Determine if HTTPS for secure cookie flag
        scheme = scope.get("scheme", "http")
        forwarded_proto = None
        for key, value in headers_raw:
            if key == b"x-forwarded-proto":
                forwarded_proto = value.decode("latin-1").lower()
                break
        is_https = scheme == "https" or forwarded_proto == "https"

        # Build Set-Cookie header value
        cookie_parts = [
            f"{SESSION_COOKIE}={session_id}",
            f"Max-Age={SESSION_MAX_AGE}",
            "HttpOnly",
            "SameSite=lax",
            "Path=/",
        ]
        if is_https:
            cookie_parts.append("Secure")
        set_cookie_value = "; ".join(cookie_parts).encode("latin-1")

        async def send_with_cookie(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"set-cookie", set_cookie_value))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_cookie)


# ── Legacy BaseHTTPMiddleware version (kept for rollback reference) ──
#
# from starlette.middleware.base import BaseHTTPMiddleware
#
# class SessionMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         session_id = request.cookies.get(SESSION_COOKIE)
#         is_new = False
#         if not session_id:
#             session_id = str(uuid.uuid4())
#             is_new = True
#         request.state.session_id = session_id
#         response = await call_next(request)
#         if is_new:
#             is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"
#             response.set_cookie(
#                 SESSION_COOKIE,
#                 session_id,
#                 max_age=SESSION_MAX_AGE,
#                 httponly=True,
#                 samesite="lax",
#                 secure=is_https,
#             )
#         return response

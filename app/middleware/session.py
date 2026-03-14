"""Simple session management via cookies.

Assigns a session ID cookie to each visitor. Tasks are associated with
sessions for ownership tracking. No server-side session store (stateless).
"""

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("subtitle-generator")

SESSION_COOKIE = "sg_session"
SESSION_MAX_AGE = 30 * 24 * 3600  # 30 days


def get_session_id(request: Request) -> str:
    """Get session ID from request cookie, or return empty string."""
    return request.cookies.get(SESSION_COOKIE, "")


class SessionMiddleware(BaseHTTPMiddleware):
    """Assigns a session cookie to each visitor."""

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get(SESSION_COOKIE)
        is_new = False

        if not session_id:
            session_id = str(uuid.uuid4())
            is_new = True

        # Store session_id on request state for route access
        request.state.session_id = session_id

        response = await call_next(request)

        # Set cookie if new session
        if is_new:
            # Detect HTTPS (direct TLS or behind a reverse proxy that sets X-Forwarded-Proto)
            is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"
            response.set_cookie(
                SESSION_COOKIE,
                session_id,
                max_age=SESSION_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=is_https,
            )

        return response

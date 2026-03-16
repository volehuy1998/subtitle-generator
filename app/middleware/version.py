"""API version header middleware.

Adds X-API-Version header to all responses for client compatibility tracking.
Sprint L31 — Forge (Sr. Backend Engineer)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    """Injects the application version into every HTTP response."""

    def __init__(self, app, version: str = "0.0.0"):
        super().__init__(app)
        self.version = version

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-API-Version"] = self.version
        return response

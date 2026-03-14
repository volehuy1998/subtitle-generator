"""Security headers middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.config import HSTS_ENABLED, HTTPS_REDIRECT


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        # Redirect HTTP to HTTPS
        if HTTPS_REDIRECT and request.url.scheme == "http":
            url = request.url.replace(scheme="https", port=443)
            return RedirectResponse(url=str(url), status_code=301)

        response = await call_next(request)

        # HSTS header (only over HTTPS)
        if HSTS_ENABLED and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # CSP: allow inline styles/scripts for the single-page template
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "media-src 'self' blob:; "
            "font-src 'self'"
        )

        # Cache headers for static-like endpoints
        path = request.url.path
        if path in ("/languages", "/embed/presets"):
            response.headers["Cache-Control"] = "public, max-age=3600"
        elif path == "/system-info":
            response.headers["Cache-Control"] = "no-cache"
        return response

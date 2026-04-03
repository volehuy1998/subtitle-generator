"""Security headers middleware.

Converted from BaseHTTPMiddleware to pure ASGI for performance
— Forge (Sr. Backend Engineer)
"""

from app.config import HSTS_ENABLED, HTTPS_REDIRECT

# Pre-encode static security headers once at import time.
_STATIC_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    (b"x-xss-protection", b"1; mode=block"),
    (
        b"content-security-policy",
        b"default-src 'self'; "
        b"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        b"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        b"connect-src 'self'; "
        b"img-src 'self' data:; "
        b"media-src 'self' blob:; "
        b"font-src 'self' https://fonts.gstatic.com",
    ),
]

_HSTS_HEADER = (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload")

# Cache-Control path mapping
_CACHE_PUBLIC_3600 = {"/languages", "/embed/presets", "/api/capabilities"}
_CACHE_PUBLIC_5 = "/api/model-status"
_CACHE_NO_CACHE = "/system-info"


class SecurityHeadersMiddleware:
    """Add security headers to every response.

    Pure ASGI implementation — no BaseHTTPMiddleware overhead.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Determine scheme from scope
        scheme = scope.get("scheme", "http")

        # HTTPS redirect
        if HTTPS_REDIRECT and scheme == "http":
            # Build redirect URL
            headers_raw = scope.get("headers", [])
            host = None
            for key, value in headers_raw:
                if key == b"host":
                    host = value.decode("latin-1")
                    break
            if host is None:
                server = scope.get("server")
                host = f"{server[0]}:{server[1]}" if server else "localhost"
            # Strip port if present for HTTPS default (443)
            host_no_port = host.split(":")[0]
            path = scope.get("path", "/")
            qs = scope.get("query_string", b"")
            redirect_url = f"https://{host_no_port}{path}"
            if qs:
                redirect_url += f"?{qs.decode('latin-1')}"
            body = b""
            await send(
                {
                    "type": "http.response.start",
                    "status": 301,
                    "headers": [
                        [b"location", redirect_url.encode("latin-1")],
                        [b"content-length", b"0"],
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

        path = scope.get("path", "/")
        is_https = scheme == "https"

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                # Add all static security headers
                headers.extend(_STATIC_HEADERS)

                # HSTS (only over HTTPS)
                if HSTS_ENABLED and is_https:
                    headers.append(_HSTS_HEADER)

                # Cache-Control per path
                if path in _CACHE_PUBLIC_3600:
                    headers.append((b"cache-control", b"public, max-age=3600"))
                elif path == _CACHE_PUBLIC_5:
                    headers.append((b"cache-control", b"public, max-age=5"))
                elif path == _CACHE_NO_CACHE:
                    headers.append((b"cache-control", b"no-cache"))

                message = {**message, "headers": headers}

            await send(message)

        await self.app(scope, receive, send_with_security_headers)


# ── Legacy BaseHTTPMiddleware version (kept for rollback reference) ──
#
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from starlette.responses import RedirectResponse
#
# class SecurityHeadersMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if HTTPS_REDIRECT and request.url.scheme == "http":
#             url = request.url.replace(scheme="https", port=443)
#             return RedirectResponse(url=str(url), status_code=301)
#         response = await call_next(request)
#         if HSTS_ENABLED and request.url.scheme == "https":
#             response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
#         response.headers["X-Content-Type-Options"] = "nosniff"
#         response.headers["X-Frame-Options"] = "DENY"
#         response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
#         response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
#         response.headers["X-XSS-Protection"] = "1; mode=block"
#         response.headers["Content-Security-Policy"] = (
#             "default-src 'self'; "
#             "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
#             "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
#             "connect-src 'self'; "
#             "img-src 'self' data:; "
#             "media-src 'self' blob:; "
#             "font-src 'self' https://fonts.gstatic.com"
#         )
#         path = request.url.path
#         if path in ("/languages", "/embed/presets", "/api/capabilities"):
#             response.headers["Cache-Control"] = "public, max-age=3600"
#         elif path == "/api/model-status":
#             response.headers["Cache-Control"] = "public, max-age=5"
#         elif path == "/system-info":
#             response.headers["Cache-Control"] = "no-cache"
#         return response

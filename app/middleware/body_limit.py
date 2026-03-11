"""Request body size limiting middleware.

Rejects requests with Content-Length exceeding the configured maximum.
This is a fast pre-check before the body is read; actual streaming
validation happens in the upload route.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import MAX_FILE_SIZE

logger = logging.getLogger("subtitle-generator")

# General API body limit (non-upload routes): 1 MB
API_BODY_LIMIT = 1 * 1024 * 1024

# Routes that accept large file uploads get the full MAX_FILE_SIZE limit
_UPLOAD_PATHS = {"/upload"}
_UPLOAD_PREFIXES = ("/embed/",)  # /embed/{task_id} accepts video uploads


class BodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the allowed limit."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})

            path = request.url.path.rstrip("/") or "/"
            is_upload = path in _UPLOAD_PATHS or any(path.startswith(p) for p in _UPLOAD_PREFIXES)
            limit = MAX_FILE_SIZE if is_upload else API_BODY_LIMIT

            if length > limit:
                logger.warning(f"BODY_LIMIT Rejected {request.method} {path}: {length} bytes > {limit} limit")
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large ({length} bytes). Maximum: {limit} bytes."},
                )

        return await call_next(request)

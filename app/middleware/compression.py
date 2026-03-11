"""GZip response compression middleware.

Compresses JSON, HTML, SSE, and text responses when the client supports it.
Reduces bandwidth usage by 60-80% for text-heavy responses.
"""

import logging

from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware

logger = logging.getLogger("subtitle-generator")

# Re-export Starlette's GZipMiddleware with our default settings
GZipMiddleware = StarletteGZipMiddleware

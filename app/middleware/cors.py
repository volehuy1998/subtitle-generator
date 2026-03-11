"""CORS configuration.

Configurable via CORS_ORIGINS environment variable (comma-separated).
Defaults to allowing all origins (*) in development.
"""

import os


def get_cors_origins() -> list[str]:
    """Get allowed CORS origins from environment."""
    raw = os.environ.get("CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]

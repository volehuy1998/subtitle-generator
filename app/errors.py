"""Structured error codes and helpers for consistent API error responses.

Sprint L33 — Forge (Sr. Backend Engineer)

Provides typed error code constants and an `api_error()` helper that builds
a standardised error dict for JSONResponse / HTTPException detail payloads.
"""

from __future__ import annotations

from typing import Optional

# ── File validation errors ────────────────────────────────────────────────────
FILE_TOO_LARGE = "FILE_TOO_LARGE"
FILE_TOO_SMALL = "FILE_TOO_SMALL"
UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
NO_AUDIO_STREAM = "NO_AUDIO_STREAM"
DURATION_EXCEEDED = "DURATION_EXCEEDED"
MAGIC_BYTES_MISMATCH = "MAGIC_BYTES_MISMATCH"
VIRUS_DETECTED = "VIRUS_DETECTED"

# ── Task errors ───────────────────────────────────────────────────────────────
TASK_NOT_FOUND = "TASK_NOT_FOUND"
TASK_NOT_TERMINAL = "TASK_NOT_TERMINAL"
TASK_LIMIT_REACHED = "TASK_LIMIT_REACHED"

# ── System errors ─────────────────────────────────────────────────────────────
SYSTEM_CRITICAL = "SYSTEM_CRITICAL"
FFMPEG_UNAVAILABLE = "FFMPEG_UNAVAILABLE"
MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"

# ── Auth errors ───────────────────────────────────────────────────────────────
AUTH_INVALID_KEY = "AUTH_INVALID_KEY"
AUTH_RATE_LIMITED = "AUTH_RATE_LIMITED"

# ── Validation errors ─────────────────────────────────────────────────────────
INVALID_PARAMETER = "INVALID_PARAMETER"
BODY_TOO_LARGE = "BODY_TOO_LARGE"

# Collect all error codes for introspection
ALL_ERROR_CODES: list[str] = [
    FILE_TOO_LARGE,
    FILE_TOO_SMALL,
    UNSUPPORTED_FORMAT,
    NO_AUDIO_STREAM,
    DURATION_EXCEEDED,
    MAGIC_BYTES_MISMATCH,
    VIRUS_DETECTED,
    TASK_NOT_FOUND,
    TASK_NOT_TERMINAL,
    TASK_LIMIT_REACHED,
    SYSTEM_CRITICAL,
    FFMPEG_UNAVAILABLE,
    MODEL_LOAD_FAILED,
    AUTH_INVALID_KEY,
    AUTH_RATE_LIMITED,
    INVALID_PARAMETER,
    BODY_TOO_LARGE,
]


def api_error(code: str, message: str, *, request_id: Optional[str] = None) -> dict:
    """Build a structured error response dict.

    Parameters
    ----------
    code : str
        One of the error code constants defined in this module.
    message : str
        Human-readable error description.
    request_id : str, optional
        If provided, included in the response for client-side correlation.

    Returns
    -------
    dict
        ``{"code": ..., "message": ...}`` with optional ``"request_id"``.
    """
    result: dict = {"code": code, "message": message}
    if request_id is not None:
        result["request_id"] = request_id
    return result

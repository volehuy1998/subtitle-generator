"""User preferences routes — session-scoped settings persistence.

Sprint L47 — Forge (Sr. Backend Engineer)

Stores user preferences (default model, format, language, etc.) keyed by session ID.
Preferences are stored in-memory via ``state.session_preferences`` and scoped per session.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app import state

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Preferences"])

# Allowed preference keys with value validators
_ALLOWED_KEYS = {
    "default_model": lambda v: isinstance(v, str) and v in ("tiny", "base", "small", "medium", "large", "auto"),
    "default_format": lambda v: isinstance(v, str) and v in ("srt", "vtt", "json"),
    "default_language": lambda v: isinstance(v, str) and len(v) <= 10,
    "auto_copy": lambda v: isinstance(v, bool),
    "theme": lambda v: isinstance(v, str) and v in ("light", "dark"),
    "max_line_chars": lambda v: isinstance(v, int) and 20 <= v <= 120,
}


@router.get("/preferences")
async def get_preferences(request: Request):
    """Get user preferences for the current session."""
    session_id = getattr(request.state, "session_id", "")
    if not session_id:
        return {"preferences": {}}
    prefs = state.session_preferences.get(session_id, {})
    return {"preferences": prefs}


@router.put("/preferences")
async def update_preferences(request: Request):
    """Update user preferences for the current session.

    Accepts a JSON body with preference key-value pairs. Only known keys
    with valid values are stored: ``default_model``, ``default_format``,
    ``default_language``, ``auto_copy``, ``theme``, ``max_line_chars``.
    """
    session_id = getattr(request.state, "session_id", "")
    if not session_id:
        raise HTTPException(400, "No session available")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(400, "Request body must be a JSON object")

    # Validate and filter to allowed keys only
    sanitized: dict = {}
    for key, validator in _ALLOWED_KEYS.items():
        if key in body and validator(body[key]):
            sanitized[key] = body[key]

    if session_id not in state.session_preferences:
        state.session_preferences[session_id] = {}

    state.session_preferences[session_id].update(sanitized)

    logger.info(f"PREFERENCES [{session_id[:8]}] Updated: {list(sanitized.keys())}")
    return {"preferences": state.session_preferences[session_id]}

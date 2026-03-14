"""Centralized input validation utilities.

Provides strict validation for file paths, subtitle content, checksums,
and error message sanitization.
"""

import hashlib
import re
import unicodedata
from pathlib import Path

from app.config import LOG_DIR, OUTPUT_DIR, UPLOAD_DIR

# ── Allowed directories for file operations ──
_SAFE_DIRS = {
    UPLOAD_DIR.resolve(),
    OUTPUT_DIR.resolve(),
    LOG_DIR.resolve(),
}


def safe_path(path: Path | str, allowed_dir: Path = None) -> Path:
    """Resolve and validate a path is within allowed directories.

    Prevents path traversal attacks by resolving symlinks and checking prefixes.
    Raises ValueError if path escapes allowed boundaries.
    """
    p = Path(path).resolve()
    if allowed_dir:
        allowed = allowed_dir.resolve()
        if not str(p).startswith(str(allowed)):
            raise ValueError(f"Path traversal blocked: {path}")
        return p

    for safe_dir in _SAFE_DIRS:
        if str(p).startswith(str(safe_dir)):
            return p
    raise ValueError(f"Path outside allowed directories: {path}")


def compute_checksum(file_path: Path | str, algorithm: str = "sha256") -> str:
    """Compute file checksum (SHA-256 by default)."""
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(file_path: Path | str, expected: str, algorithm: str = "sha256") -> bool:
    """Verify file matches expected checksum."""
    actual = compute_checksum(file_path, algorithm)
    return actual == expected


# ── Subtitle content sanitization ──

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_TAGS = re.compile(r"<(?!/?(?:b|i|u|font)\b)[^>]+>", re.IGNORECASE)
_SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</\s*script[^>]*>", re.IGNORECASE | re.DOTALL)


def sanitize_subtitle_text(text: str) -> str:
    """Sanitize subtitle text content.

    - Strips control characters (except newlines/tabs)
    - Removes script tags and dangerous HTML
    - Preserves basic formatting tags (b, i, u, font)
    - Normalizes Unicode
    """
    if not text:
        return text
    # Remove script tags first
    text = _SCRIPT_PATTERN.sub("", text)
    # Remove dangerous HTML tags (keep b, i, u, font)
    text = _HTML_TAGS.sub("", text)
    # Remove control chars
    text = _CONTROL_CHARS.sub("", text)
    # Normalize Unicode
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def validate_subtitle_timing(start: float, end: float) -> tuple[bool, str]:
    """Validate subtitle timing values.

    Returns (valid, error_message).
    """
    if start < 0:
        return False, "Start time cannot be negative"
    if end < 0:
        return False, "End time cannot be negative"
    if end <= start:
        return False, "End time must be after start time"
    if end - start > 300:  # 5 minutes max per subtitle
        return False, "Subtitle duration exceeds maximum (300s)"
    return True, ""


# ── Error message sanitization ──

_INTERNAL_PATTERNS = [
    (re.compile(r"[A-Za-z]:[/\\][\w/\\.-]+"), "[PATH]"),  # Windows paths
    (re.compile(r"/(?:home|usr|var|tmp|opt)/[\w/.-]+"), "[PATH]"),  # Unix paths
    (re.compile(r"\b(?:sqlite|postgresql|mysql)://\S+"), "[DB_URL]"),  # DB URLs
    (re.compile(r'File ".*?", line \d+'), "Internal error"),  # Python tracebacks
    (re.compile(r"Traceback \(most recent call last\):.*", re.DOTALL), "Internal error"),
]


def sanitize_error_message(msg: str, include_details: bool = False) -> str:
    """Sanitize error messages for client responses.

    Strips internal paths, DB URLs, and stack traces.
    Set include_details=True for server-side logging.
    """
    if include_details:
        return msg
    for pattern, replacement in _INTERNAL_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg


# ── FFmpeg filter value validation ──

_FFMPEG_SAFE_CHARS = re.compile(r"^[a-zA-Z0-9 _\-.,/]+$")
_FFMPEG_ALLOWED_FONTS = {
    "Arial",
    "Helvetica",
    "Verdana",
    "Times New Roman",
    "Courier New",
    "Georgia",
    "Impact",
    "Tahoma",
    "Trebuchet MS",
    "Comic Sans MS",
    "Liberation Sans",
    "DejaVu Sans",
    "Noto Sans",
}


def validate_ffmpeg_filter_value(value: str) -> bool:
    """Validate a value used in FFmpeg filter expressions.

    Only allows safe characters to prevent filter injection.
    """
    if not value:
        return True
    return bool(_FFMPEG_SAFE_CHARS.match(value))


def validate_ffmpeg_font(font_name: str) -> str:
    """Validate and normalize FFmpeg font name. Returns safe font or Arial."""
    if not font_name:
        return "Arial"
    # Strip dangerous chars
    sanitized = re.sub(r"[^a-zA-Z0-9 _-]", "", font_name).strip()
    return sanitized if sanitized else "Arial"

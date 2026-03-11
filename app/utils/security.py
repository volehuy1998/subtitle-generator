"""Security utilities: file validation, magic bytes, filename sanitization."""

import logging
import re
from pathlib import Path

import filetype

from app.config import ALLOWED_EXTENSIONS, MIN_FILE_SIZE

logger = logging.getLogger("subtitle-generator")

# Map extensions to expected MIME type prefixes
EXTENSION_MIME_MAP = {
    ".mp4": ["video/mp4", "video/quicktime"],
    ".mkv": ["video/x-matroska"],
    ".avi": ["video/x-msvideo", "video/avi"],
    ".webm": ["video/webm"],
    ".mov": ["video/quicktime"],
    ".mp3": ["audio/mpeg"],
    ".wav": ["audio/x-wav", "audio/wav"],
    ".flac": ["audio/flac", "audio/x-flac"],
}


def validate_file_extension(filename: str) -> str | None:
    """Validate file extension. Returns extension or None if invalid."""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    return None


def validate_magic_bytes(file_path: Path) -> bool:
    """Validate file content matches a known media type via magic bytes."""
    try:
        kind = filetype.guess(str(file_path))
        if kind is None:
            logger.warning(f"SECURITY Magic bytes: unrecognized file type for {file_path.name}")
            return False
        mime = kind.mime
        if mime.startswith("video/") or mime.startswith("audio/"):
            logger.debug(f"SECURITY Magic bytes OK: {file_path.name} -> {mime}")
            return True
        logger.warning(f"SECURITY Magic bytes mismatch: {file_path.name} detected as {mime}")
        return False
    except Exception as e:
        logger.error(f"SECURITY Magic bytes check failed: {e}")
        return False


def validate_file_size(size: int) -> tuple[bool, str]:
    """Validate file is not too small (likely invalid)."""
    if size < MIN_FILE_SIZE:
        return False, f"File too small ({size} bytes). Minimum is {MIN_FILE_SIZE} bytes."
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize a user-supplied filename for safe storage/display.

    Strips path separators, null bytes, and dangerous characters.
    """
    # Remove path components
    name = Path(filename).name
    # Remove null bytes and control characters
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    # Remove characters that could cause path traversal or shell issues
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    # Fallback if nothing remains
    if not name:
        name = "unnamed_file"
    return name

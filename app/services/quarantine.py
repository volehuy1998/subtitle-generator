"""File quarantine service.

Moves suspicious uploads to a quarantine directory for review.
"""

import logging
import shutil
from pathlib import Path

from app.config import BASE_DIR
from app.services.audit import log_audit_event

logger = logging.getLogger("subtitle-generator")

QUARANTINE_DIR = BASE_DIR / "quarantine"


def quarantine_file(file_path: Path, reason: str, **kwargs) -> Path | None:
    """Move a suspicious file to quarantine.

    Returns the quarantine path, or None if the move failed.
    """
    QUARANTINE_DIR.mkdir(exist_ok=True)
    dest = QUARANTINE_DIR / file_path.name

    try:
        shutil.move(str(file_path), str(dest))
        log_audit_event(
            "file_quarantined",
            filename=file_path.name,
            reason=reason,
            quarantine_path=str(dest),
            **kwargs,
        )
        logger.warning(f"QUARANTINE Moved {file_path.name}: {reason}")
        return dest
    except Exception as e:
        logger.error(f"QUARANTINE Failed to move {file_path.name}: {e}")
        return None


def get_quarantine_count() -> int:
    """Get count of quarantined files."""
    if not QUARANTINE_DIR.exists():
        return 0
    return sum(1 for _ in QUARANTINE_DIR.iterdir() if _.is_file())

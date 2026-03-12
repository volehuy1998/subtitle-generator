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

_CLAMD_UNIX_SOCKET = "/var/run/clamav/clamd.ctl"
_CLAMD_TCP_HOST = "localhost"
_CLAMD_TCP_PORT = 3310


def scan_with_clamav(filepath: str) -> dict:
    """Scan a file with ClamAV if available.

    Tries to connect via Unix socket first, then TCP.
    Returns a dict with keys:
        scanned (bool)  — whether ClamAV was reachable and the scan ran
        clean   (bool)  — True if no threat detected (also True when not scanned)
        threat  (str|None) — threat name returned by ClamAV, or None
    """
    try:
        import clamd  # python-clamd optional dependency
    except ImportError:
        logger.warning("ClamAV not available, skipping virus scan")
        return {"scanned": False, "clean": True, "threat": None}

    cd = None

    # Try Unix socket first
    try:
        cd = clamd.ClamdUnixSocket(_CLAMD_UNIX_SOCKET)
        cd.ping()
    except Exception:
        cd = None

    # Fall back to TCP
    if cd is None:
        try:
            cd = clamd.ClamdNetworkSocket(_CLAMD_TCP_HOST, _CLAMD_TCP_PORT)
            cd.ping()
        except Exception:
            cd = None

    if cd is None:
        logger.warning("ClamAV not available, skipping virus scan")
        return {"scanned": False, "clean": True, "threat": None}

    try:
        result = cd.scan(filepath)
        # result is {filepath: ('OK', None)} or {filepath: ('FOUND', 'Eicar-Test-Signature')}
        if result is None:
            return {"scanned": True, "clean": True, "threat": None}
        status, threat = result.get(filepath, ("OK", None))
        clean = status == "OK"
        return {"scanned": True, "clean": clean, "threat": threat}
    except Exception as e:
        logger.error(f"ClamAV scan error for {filepath}: {e}")
        return {"scanned": False, "clean": True, "threat": None}


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

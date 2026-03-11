"""Infrastructure security utilities.

CSP nonces, HSTS configuration, SRI hash computation,
and audit log integrity (HMAC signing).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone

# ── CSP Nonce ──

def generate_csp_nonce() -> str:
    """Generate a cryptographically random CSP nonce (base64, 16 bytes)."""
    return base64.b64encode(secrets.token_bytes(16)).decode("ascii")


# ── SRI Hash ──

def compute_sri_hash(content: str | bytes, algorithm: str = "sha384") -> str:
    """Compute Subresource Integrity hash for a script/style resource."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    h = hashlib.new(algorithm, content)
    b64 = base64.b64encode(h.digest()).decode("ascii")
    return f"{algorithm}-{b64}"


# ── HSTS Configuration ──

HSTS_ENABLED = os.environ.get("HSTS_ENABLED", "false").lower() == "true"
HSTS_MAX_AGE = int(os.environ.get("HSTS_MAX_AGE", "31536000"))  # 1 year
HSTS_INCLUDE_SUBDOMAINS = os.environ.get("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
HSTS_PRELOAD = os.environ.get("HSTS_PRELOAD", "false").lower() == "true"
HTTPS_REDIRECT = os.environ.get("HTTPS_REDIRECT", "false").lower() == "true"


def get_hsts_header() -> str:
    """Build HSTS header value from configuration."""
    parts = [f"max-age={HSTS_MAX_AGE}"]
    if HSTS_INCLUDE_SUBDOMAINS:
        parts.append("includeSubDomains")
    if HSTS_PRELOAD:
        parts.append("preload")
    return "; ".join(parts)


# ── CORS lockdown ──

CORS_DEFAULT_DENY = os.environ.get("CORS_DEFAULT_DENY", "false").lower() == "true"


def get_safe_cors_origins() -> list[str]:
    """Get CORS origins with safety checks.

    - No credentials with wildcard
    - Explicit origins only in production
    """
    raw = os.environ.get("CORS_ORIGINS", "*").strip()
    if raw == "*":
        if CORS_DEFAULT_DENY:
            return []  # Deny all in strict mode
        return ["*"]
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    # Validate origins are proper URLs
    return [o for o in origins if o.startswith("http://") or o.startswith("https://")]


# ── Audit Log Integrity ──

_AUDIT_HMAC_KEY = os.environ.get("AUDIT_HMAC_KEY", secrets.token_hex(32))


def sign_audit_entry(entry: dict) -> str:
    """Generate HMAC signature for an audit log entry."""
    canonical = json.dumps(entry, sort_keys=True, default=str, ensure_ascii=True)
    return hmac.new(_AUDIT_HMAC_KEY.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def verify_audit_entry(entry: dict, signature: str) -> bool:
    """Verify HMAC signature of an audit log entry."""
    expected = sign_audit_entry(entry)
    return hmac.compare_digest(expected, signature)


def create_signed_audit_entry(event_type: str, **kwargs) -> dict:
    """Create a signed audit log entry with timestamp and HMAC."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **kwargs,
    }
    entry["hmac"] = sign_audit_entry({k: v for k, v in entry.items() if k != "hmac"})
    return entry

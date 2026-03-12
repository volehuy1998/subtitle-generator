"""Task access control and trusted-proxy IP resolution.

Two responsibilities:

1. **Task ownership** — when API key auth is disabled (open/public deployment),
   tasks are bound to the session that created them.  Any other session gets 403.
   Skipped when auth is enabled (all callers are already authenticated).

2. **Real client IP** — when the service runs behind nginx/haproxy/docker the
   direct peer is the proxy, not the end-user.  We trust X-Real-IP only when
   the direct connection comes from a known proxy address.
"""

import os

from fastapi import HTTPException, Request

# ── Trusted proxy addresses ────────────────────────────────────────────────────
# IPs from which we trust X-Real-IP / X-Forwarded-For.
# Extend via TRUSTED_PROXIES env var (comma-separated CIDR or IPs).
_DEFAULT_TRUSTED = {"127.0.0.1", "::1", "172.17.0.1"}  # localhost + docker bridge

def _load_trusted_proxies() -> frozenset[str]:
    raw = os.environ.get("TRUSTED_PROXIES", "")
    extra = {s.strip() for s in raw.split(",") if s.strip()}
    return frozenset(_DEFAULT_TRUSTED | extra)

_TRUSTED_PROXIES = _load_trusted_proxies()


def get_client_ip(request: Request) -> str:
    """Return the best-guess real client IP.

    Trusts X-Real-IP only when the direct peer is a known proxy.
    Never trusts X-Forwarded-For from untrusted sources (easily spoofed).
    """
    peer = request.client.host if request.client else "unknown"
    if peer in _TRUSTED_PROXIES:
        real_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if real_ip:
            return real_ip
    return peer


# ── Task ownership ─────────────────────────────────────────────────────────────

def check_task_access(task: dict, request: Request) -> None:
    """Raise HTTP 403 if the requester does not own this task.

    Ownership is determined by the session cookie assigned at upload time.
    The check is skipped when:
      - API key auth is enabled (all callers already authenticated)
      - The task pre-dates this feature (no session_id stored)
    """
    from app.middleware.auth import is_auth_enabled
    if is_auth_enabled():
        return  # API-key auth → caller is trusted

    owner = task.get("session_id", "")
    if not owner:
        return  # no ownership info → open access (backward compat)

    caller = getattr(request.state, "session_id", "")
    if caller and caller != owner:
        raise HTTPException(
            status_code=403,
            detail="Access denied — this task belongs to a different session.",
        )

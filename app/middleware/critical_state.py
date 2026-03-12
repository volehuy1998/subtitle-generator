"""Critical state middleware — blocks all user-facing operations when the system is unhealthy.

When state.system_critical is True, only health/monitoring endpoints remain
accessible. Everything else returns 503 with the critical reason(s).

This is the single enforcement point — no individual route needs its own
health checks. The background health monitor (app.services.health_monitor)
continuously evaluates system health and sets/clears the critical flag.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import state

logger = logging.getLogger("subtitle-generator")

# Paths that remain accessible during critical state.
# ONLY monitoring/infrastructure — ALL user features are blocked.
_PASSTHROUGH_PREFIXES = (
    "/health",
    "/ready",
    "/status",
    "/api/status",
    "/api/capabilities",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
)


class CriticalStateMiddleware(BaseHTTPMiddleware):
    """Block all user-facing requests when the system is in critical state."""

    async def dispatch(self, request: Request, call_next):
        if not state.system_critical:
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"

        # Allow health/monitoring endpoints through
        if any(path.startswith(prefix) for prefix in _PASSTHROUGH_PREFIXES):
            return await call_next(request)

        reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Service in critical state — all operations suspended. Reason: {reasons}",
                "critical": True,
                "reasons": state.system_critical_reasons,
            },
        )

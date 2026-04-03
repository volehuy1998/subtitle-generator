# Critical State Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock down the entire service when any critical subsystem fails — static HTML for cold visits, SPA overlay for active sessions, 8 health checks.

**Architecture:** Expand the existing health monitor with 5 new checks (FFmpeg, Redis, model, memory, output dir). Modify the critical state middleware to serve a static HTML page to browsers and pass through SPA assets. Add a React CriticalOverlay component to both branches.

**Tech Stack:** Python (FastAPI middleware, asyncio health checks, psutil), React (Zustand store, CSS overlay), HTML (static template)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `app/services/health_monitor.py` | Add 5 new check functions, wire into loop |
| Modify | `app/middleware/critical_state.py` | Serve HTML to browsers, expand passthrough |
| Create | `templates/critical.html` | Static self-contained critical state page |
| Create | `frontend/src/components/system/CriticalOverlay.tsx` | SPA full-screen overlay |
| Modify | `tests/test_critical_state.py` | Tests for new checks + middleware behavior |

---

### Task 1: Add 5 new health check functions

**Files:**
- Modify: `app/services/health_monitor.py`
- Test: `tests/test_critical_state.py`

- [ ] **Step 1: Write failing tests for each new check**

Add to `tests/test_critical_state.py`:

```python
class TestHealthCheckFunctions:
    """Test individual health check functions from health_monitor."""

    def test_check_ffmpeg_passes_when_available(self):
        from app.services.health_monitor import _check_ffmpeg
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            assert _check_ffmpeg() is None

    def test_check_ffmpeg_fails_when_missing(self):
        from app.services.health_monitor import _check_ffmpeg
        with patch("shutil.which", return_value=None):
            result = _check_ffmpeg()
            assert result is not None
            assert "FFmpeg" in result

    def test_check_memory_passes_when_sufficient(self):
        from app.services.health_monitor import _check_memory
        mock_mem = MagicMock()
        mock_mem.available = 2 * 1024 * 1024 * 1024  # 2 GB
        with patch("psutil.virtual_memory", return_value=mock_mem):
            assert _check_memory() is None

    def test_check_memory_fails_when_low(self):
        from app.services.health_monitor import _check_memory
        mock_mem = MagicMock()
        mock_mem.available = 100 * 1024 * 1024  # 100 MB
        with patch("psutil.virtual_memory", return_value=mock_mem):
            result = _check_memory()
            assert result is not None
            assert "Memory" in result

    def test_check_output_dir_passes_when_writable(self):
        from app.services.health_monitor import _check_output_dir
        with patch("os.access", return_value=True):
            assert _check_output_dir() is None

    def test_check_output_dir_fails_when_not_writable(self):
        from app.services.health_monitor import _check_output_dir
        with patch("os.access", return_value=False):
            result = _check_output_dir()
            assert result is not None
            assert "Output directory" in result

    def test_check_redis_skipped_when_no_url(self):
        from app.services.health_monitor import _check_redis
        import asyncio
        with patch("app.config.REDIS_URL", ""):
            result = asyncio.get_event_loop().run_until_complete(_check_redis())
            assert result is None

    def test_check_model_passes_when_loaded(self):
        from app.services.health_monitor import _check_model
        with patch.object(state, "loaded_models", {("large", "cpu"): object()}):
            assert _check_model() is None

    def test_check_model_skipped_during_loading(self):
        from app.services.health_monitor import _check_model
        with patch.object(state, "loaded_models", {}), \
             patch.object(state, "model_preload", {"status": "loading"}):
            assert _check_model() is None

    def test_check_model_fails_when_none_loaded(self):
        from app.services.health_monitor import _check_model
        with patch.object(state, "loaded_models", {}), \
             patch.object(state, "model_preload", {"status": "ready", "loaded": []}):
            result = _check_model()
            assert result is not None
            assert "model" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_critical_state.py::TestHealthCheckFunctions -v`
Expected: FAIL (functions don't exist yet)

- [ ] **Step 3: Implement the 5 new check functions**

Add to `app/services/health_monitor.py` after the existing `_check_disk()`:

```python
import os
import psutil


# Minimum available memory (bytes)
MIN_MEMORY_FREE_BYTES = 500 * 1024 * 1024  # 500 MB


def _check_ffmpeg() -> str | None:
    """Returns reason string if ffmpeg is not on PATH."""
    if shutil.which("ffmpeg") is None:
        return "FFmpeg not available"
    return None


def _check_memory() -> str | None:
    """Returns reason string if available memory is critically low."""
    try:
        mem = psutil.virtual_memory()
        if mem.available < MIN_MEMORY_FREE_BYTES:
            free_mb = round(mem.available / 1024 / 1024)
            return f"Memory critically low ({free_mb} MB available)"
    except Exception as e:
        return f"Memory check failed: {e}"
    return None


def _check_output_dir() -> str | None:
    """Returns reason string if output directory is not writable."""
    if not os.access(str(OUTPUT_DIR), os.W_OK):
        return "Output directory not writable"
    return None


async def _check_redis() -> str | None:
    """Returns reason string if Redis is configured but unreachable."""
    from app.config import REDIS_URL

    if not REDIS_URL:
        return None  # Redis not configured — skip check
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
    except Exception as e:
        return f"Redis unreachable: {e}"
    return None


def _check_model() -> str | None:
    """Returns reason string if no Whisper model is loaded or loadable."""
    if state.loaded_models:
        return None  # At least one model loaded
    if state.model_preload.get("status") == "loading":
        return None  # Startup grace — model is still loading
    return "No transcription model available"
```

- [ ] **Step 4: Wire new checks into health_check_loop**

Replace the check section in `health_check_loop()`:

```python
            reasons = []

            # Check database
            db_reason = await _check_db()
            if db_reason:
                reasons.append(db_reason)

            # Check disk
            disk_reason = _check_disk()
            if disk_reason:
                reasons.append(disk_reason)

            # Check FFmpeg
            ffmpeg_reason = _check_ffmpeg()
            if ffmpeg_reason:
                reasons.append(ffmpeg_reason)

            # Check Redis (if configured)
            redis_reason = await _check_redis()
            if redis_reason:
                reasons.append(redis_reason)

            # Check Whisper model availability
            model_reason = _check_model()
            if model_reason:
                reasons.append(model_reason)

            # Check available memory
            memory_reason = _check_memory()
            if memory_reason:
                reasons.append(memory_reason)

            # Check output directory writable
            output_reason = _check_output_dir()
            if output_reason:
                reasons.append(output_reason)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_critical_state.py -v --tb=short`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/health_monitor.py tests/test_critical_state.py
git commit -m "feat(health): expand critical checks — FFmpeg, Redis, model, memory, output dir"
```

---

### Task 2: Create static critical HTML page

**Files:**
- Create: `templates/critical.html`

- [ ] **Step 1: Create the template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="10">
  <title>SubForge — Service Unavailable</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      background: #FAFAF9;
      color: #18181B;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .container {
      max-width: 480px;
      width: 100%;
      text-align: center;
    }
    .icon {
      font-size: 48px;
      margin-bottom: 16px;
      opacity: 0.8;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 20px;
      letter-spacing: -0.025em;
    }
    .reasons {
      list-style: none;
      background: #FEF2F2;
      border: 1px solid #FECACA;
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 20px;
      text-align: left;
    }
    .reasons li {
      font-size: 0.875rem;
      color: #991B1B;
      padding: 4px 0;
    }
    .reasons li::before {
      content: "• ";
      color: #DC2626;
    }
    .message {
      font-size: 0.875rem;
      color: #52525B;
      margin-bottom: 8px;
    }
    .muted {
      font-size: 0.75rem;
      color: #A1A1AA;
      margin-bottom: 24px;
    }
    button {
      background: #4F46E5;
      color: white;
      border: none;
      padding: 10px 24px;
      border-radius: 6px;
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s;
    }
    button:hover { background: #4338CA; }
    .links {
      margin-top: 24px;
      font-size: 0.75rem;
      color: #A1A1AA;
    }
    .links a {
      color: #4F46E5;
      text-decoration: none;
    }
    .links a:hover { text-decoration: underline; }
    @media (prefers-color-scheme: dark) {
      body { background: #0C0A09; color: #FAFAF9; }
      .reasons { background: #1C1917; border-color: #44403C; }
      .reasons li { color: #F87171; }
      .message { color: #D6D3D1; }
      .muted { color: #78716C; }
      .links { color: #78716C; }
      .links a { color: #818CF8; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="icon">&#9888;</div>
    <h1>SubForge is temporarily unavailable</h1>
    <ul class="reasons">{{REASONS}}</ul>
    <p class="message">All operations are paused to protect your data.</p>
    <p class="muted">This page checks automatically every 10 seconds.</p>
    <button onclick="location.reload()">Retry Now</button>
    <div class="links">
      <a href="/health">Health</a> &middot; <a href="/status">Status</a>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 2: Verify template exists**

Run: `ls templates/critical.html`
Expected: file listed

- [ ] **Step 3: Commit**

```bash
git add templates/critical.html
git commit -m "feat(ui): add static critical state HTML page"
```

---

### Task 3: Update middleware to serve HTML and expand passthrough

**Files:**
- Modify: `app/middleware/critical_state.py`
- Test: `tests/test_critical_state.py`

- [ ] **Step 1: Write failing tests for middleware behavior**

Add to `tests/test_critical_state.py`:

```python
class TestCriticalStateMiddlewareResponse:
    """Test that middleware serves HTML to browsers and JSON to API clients."""

    def test_browser_gets_html_during_critical(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Database unreachable"]
        try:
            resp = client.get("/", headers={"Accept": "text/html"})
            assert resp.status_code == 503
            assert "text/html" in resp.headers.get("content-type", "")
            assert "SubForge is temporarily unavailable" in resp.text
            assert "Database unreachable" in resp.text
        finally:
            state.system_critical = False
            state.system_critical_reasons = []

    def test_api_client_gets_json_during_critical(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Disk space critically low"]
        try:
            resp = client.get("/upload", headers={"Accept": "application/json"})
            assert resp.status_code == 503
            data = resp.json()
            assert data["critical"] is True
            assert "Disk space critically low" in data["reasons"]
        finally:
            state.system_critical = False
            state.system_critical_reasons = []

    def test_assets_passthrough_during_critical(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Test"]
        try:
            resp = client.get("/assets/index.js")
            # Should NOT be 503 — assets pass through
            assert resp.status_code != 503
        finally:
            state.system_critical = False
            state.system_critical_reasons = []

    def test_health_stream_passthrough_during_critical(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Test"]
        try:
            resp = client.get("/health")
            assert resp.status_code == 200
        finally:
            state.system_critical = False
            state.system_critical_reasons = []

    def test_system_info_passthrough_during_critical(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Test"]
        try:
            resp = client.get("/system-info")
            assert resp.status_code == 200
        finally:
            state.system_critical = False
            state.system_critical_reasons = []

    def test_multiple_reasons_shown_in_html(self, client):
        state.system_critical = True
        state.system_critical_reasons = ["Database unreachable", "Disk space critically low"]
        try:
            resp = client.get("/", headers={"Accept": "text/html"})
            assert "Database unreachable" in resp.text
            assert "Disk space critically low" in resp.text
        finally:
            state.system_critical = False
            state.system_critical_reasons = []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_critical_state.py::TestCriticalStateMiddlewareResponse -v`
Expected: FAIL

- [ ] **Step 3: Implement middleware changes**

Replace `app/middleware/critical_state.py` entirely:

```python
"""Critical state middleware — blocks user-facing operations when system is unhealthy.

When state.system_critical is True:
- Browser requests (Accept: text/html) → static critical.html page
- API requests (Accept: application/json) → 503 JSON
- Health/monitoring/static assets → passthrough (always accessible)
"""

import logging
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from app import state

logger = logging.getLogger("subtitle-generator")

# Load critical page template once at import time
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "critical.html"
_CRITICAL_HTML = _TEMPLATE_PATH.read_text(encoding="utf-8") if _TEMPLATE_PATH.exists() else "<h1>Service Unavailable</h1><p>{{REASONS}}</p>"

# Paths that always pass through during critical state
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
    "/assets",
    "/favicon",
    "/manifest",
    "/system-info",
    "/languages",
    "/events",
)


def _wants_html(request: Request) -> bool:
    """Check if the client prefers HTML (browser) over JSON (API client)."""
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def _build_critical_html(reasons: list[str]) -> str:
    """Inject reasons into the critical state HTML template."""
    items = "".join(f"<li>{r}</li>" for r in reasons) if reasons else "<li>Unknown error</li>"
    return _CRITICAL_HTML.replace("{{REASONS}}", items)


class CriticalStateMiddleware(BaseHTTPMiddleware):
    """Block user-facing requests when system is in critical state."""

    async def dispatch(self, request: Request, call_next):
        if not state.system_critical:
            return await call_next(request)

        path = request.url.path.rstrip("/") or "/"

        # Allow health/monitoring/static asset endpoints through
        if any(path.startswith(prefix) for prefix in _PASSTHROUGH_PREFIXES):
            return await call_next(request)

        reasons = state.system_critical_reasons or ["Unknown"]

        # Browser → serve static HTML critical page
        if _wants_html(request):
            html = _build_critical_html(reasons)
            return HTMLResponse(content=html, status_code=503)

        # API client → JSON error
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Service in critical state — all operations suspended. Reason: {'; '.join(reasons)}",
                "critical": True,
                "reasons": reasons,
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_critical_state.py -v --tb=short`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add app/middleware/critical_state.py tests/test_critical_state.py
git commit -m "feat(middleware): serve HTML critical page to browsers, expand passthrough"
```

---

### Task 4: Create SPA CriticalOverlay component

**Files:**
- Create: `frontend/src/components/system/CriticalOverlay.tsx`

- [ ] **Step 1: Create the component**

```tsx
/**
 * CriticalOverlay — full-screen overlay when system is in critical state.
 *
 * Listens to health SSE data via uiStore. When system_critical is true,
 * renders an opaque overlay blocking all interaction. Auto-dismisses
 * when system recovers.
 *
 * — Pixel (Senior Frontend Engineer)
 */

import { useUIStore } from '../../store/uiStore'

export function CriticalOverlay() {
  const health = useUIStore((s) => s.health)

  const isCritical = health?.system_critical === true
  const reasons: string[] = health?.system_critical_reasons ?? []

  if (!isCritical) return null

  return (
    <div
      data-testid="critical-overlay"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(4px)',
        padding: '24px',
      }}
    >
      <div
        style={{
          maxWidth: '440px',
          width: '100%',
          background: 'var(--color-surface, #FFFFFF)',
          borderRadius: '12px',
          padding: '32px',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '12px', opacity: 0.8 }}>&#9888;</div>
        <h2
          style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: 'var(--color-text, #18181B)',
            marginBottom: '16px',
            letterSpacing: '-0.025em',
          }}
        >
          System Critical
        </h2>
        <ul
          style={{
            listStyle: 'none',
            padding: '12px 16px',
            marginBottom: '16px',
            background: 'var(--color-danger-light, #FEF2F2)',
            border: '1px solid var(--color-danger, #DC2626)',
            borderRadius: '8px',
            textAlign: 'left',
          }}
        >
          {reasons.map((r, i) => (
            <li
              key={i}
              style={{
                fontSize: '0.875rem',
                color: 'var(--color-danger, #DC2626)',
                padding: '3px 0',
              }}
            >
              • {r}
            </li>
          ))}
        </ul>
        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary, #52525B)',
            marginBottom: '6px',
          }}
        >
          All operations are paused to protect your data.
        </p>
        <p
          style={{
            fontSize: '0.75rem',
            color: 'var(--color-text-muted, #A1A1AA)',
          }}
        >
          Checking automatically...
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit src/components/system/CriticalOverlay.tsx 2>&1 || echo "Check manually"`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/system/CriticalOverlay.tsx
git commit -m "feat(ui): add CriticalOverlay component for system critical state"
```

---

### Task 5: Mount CriticalOverlay in both branches

**Files:**
- Modify: Router.tsx (prod-editorial-nav) — add `<CriticalOverlay />` after `<Header />`
- Modify: AppShell.tsx (feat/editorial-redesign) — add `<CriticalOverlay />` after `<Header />`

- [ ] **Step 1: Mount in prod-editorial-nav Router.tsx**

On branch `prod-editorial-nav`, in `frontend/src/Router.tsx`:

Add import:
```tsx
import { CriticalOverlay } from './components/system/CriticalOverlay'
```

Add component after `<Header />` in the return JSX:
```tsx
    <Header />
    <CriticalOverlay />
```

- [ ] **Step 2: Commit on prod-editorial-nav**

```bash
git add frontend/src/Router.tsx
git commit -m "feat(ui): mount CriticalOverlay in prod layout"
```

- [ ] **Step 3: Mount in feat/editorial-redesign AppShell.tsx**

On branch `feat/editorial-redesign`, in `frontend/src/components/layout/AppShell.tsx`:

Add import:
```tsx
import { CriticalOverlay } from '../system/CriticalOverlay'
```

Add component after `<Header />`:
```tsx
    <Header />
    <CriticalOverlay />
```

- [ ] **Step 4: Commit on feat/editorial-redesign**

```bash
git add frontend/src/components/layout/AppShell.tsx
git commit -m "feat(ui): mount CriticalOverlay in editorial layout"
```

---

### Task 6: Integration test — full critical state flow

- [ ] **Step 1: Test end-to-end flow**

Manually verify:
1. Stop PostgreSQL: `sudo docker stop subtitle-generator-postgres-1`
2. Wait 10s for health monitor to detect
3. Visit `http://127.0.0.1:8000` in browser → should see static HTML critical page
4. `curl http://127.0.0.1:8000/upload -X POST` → should get 503 JSON
5. `curl http://127.0.0.1:8000/health` → should get 200 (passthrough)
6. `curl http://127.0.0.1:8000/system-info` → should get 200 (passthrough)
7. Restart PostgreSQL: `sudo docker compose up -d postgres`
8. Wait 10s → refresh browser → should load normal SPA

- [ ] **Step 2: Build and deploy both containers**

```bash
sudo bash scripts/deploy-profile.sh          # prod
sudo bash scripts/deploy-profile.sh newui    # subdomain
```

- [ ] **Step 3: Commit any final fixes**

```bash
git commit -m "test(critical): verify full critical state flow"
```

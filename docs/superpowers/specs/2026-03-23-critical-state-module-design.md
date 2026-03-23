# Critical State Module Design

**Date**: 2026-03-23
**Author**: Atlas (Tech Lead)
**Status**: Approved

## Goal

When any critical subsystem fails, the entire service locks down — no uploads, no processing, no user-facing operations. Users see a clear, designed error page explaining what's wrong, with auto-recovery when the issue resolves. Two independent layers: static HTML for cold visits, SPA overlay for active sessions.

## Scope

| # | Component | Branch | Description |
|---|-----------|--------|-------------|
| 1 | Expanded health checks (8 criteria) | Both | Add FFmpeg, Redis, model, memory, output dir checks |
| 2 | Static critical HTML page | Both | Self-contained error page served by middleware |
| 3 | Middleware passthrough fixes | Both | Allow SPA assets through, serve HTML to browsers |
| 4 | SPA CriticalOverlay component | Both | Full-screen overlay when system_critical detected via SSE |

## Component 1: Expanded Health Checks

Modify `app/services/health_monitor.py` to check 8 conditions every 5 seconds. Any single failure triggers `state.set_critical(reasons)`.

| # | Check | Method | Threshold | Reason string | Conditional? |
|---|-------|--------|-----------|---------------|-------------|
| 1 | Database | `check_db_health()` async | Connection fails or `ok: false` | "Database unreachable" | No |
| 2 | Disk space | `shutil.disk_usage(OUTPUT_DIR)` | < 500 MB free | "Disk space critically low (X MB free)" | No |
| 3 | Shutdown | `state.shutting_down` | Flag is True | "System shutting down" | No |
| 4 | FFmpeg | `shutil.which('ffmpeg')` | Not on PATH | "FFmpeg not available" | No |
| 5 | Redis | `redis.ping()` | Connection fails | "Redis unreachable" | Only if `REDIS_URL` set |
| 6 | Whisper model | `state.loaded_models` empty | No models loaded AND not currently loading | "No transcription model available" | Grace period during startup |
| 7 | Memory | `psutil.virtual_memory().available` | < 500 MB available | "Memory critically low (X MB free)" | No |
| 8 | Output dir | `os.access(OUTPUT_DIR, os.W_OK)` | Not writable | "Output directory not writable" | No |

### Check details

**Check 5 (Redis)**: Import `REDIS_URL` from config. If empty/None, skip check entirely. If set, attempt `redis.asyncio.from_url(REDIS_URL).ping()` with 2-second timeout.

**Check 6 (Model)**: Read `state.loaded_models`. If dict is empty, also check if `model_preload_status` is `'loading'` — if so, skip (startup grace). Only flag critical if no models loaded AND nothing is loading.

**Check 7 (Memory)**: Uses `psutil.virtual_memory().available` (includes reclaimable buffers/cache). Threshold: 500 MB. This is the same `psutil` already mocked in test conftest.

**New checks are independent functions** following the existing pattern (`_check_X() -> str | None`).

## Component 2: Static Critical HTML Page

Create `templates/critical.html` — a self-contained HTML page with:
- **Zero external dependencies** — all CSS inline, no fonts, no JS frameworks
- **Reasons list** — injected via `{{REASONS}}` placeholder, simple string replace
- **Auto-refresh** — `<meta http-equiv="refresh" content="10">` reloads every 10s
- **Retry button** — `onclick="location.reload()"`
- **Links** — `/health` and `/status` remain accessible for debugging
- **Responsive** — works on mobile
- **Matches brand** — uses SubForge colors (indigo accent, warm neutrals)

### Template content

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="10">
  <title>SubForge — Service Unavailable</title>
  <style>/* inline CSS — brand colors, centered layout, reason list */</style>
</head>
<body>
  <div class="container">
    <div class="icon">⚠</div>
    <h1>SubForge is temporarily unavailable</h1>
    <ul class="reasons">{{REASONS}}</ul>
    <p>All operations are paused to protect your data.</p>
    <p class="muted">This page checks automatically every 10 seconds.</p>
    <button onclick="location.reload()">Retry Now</button>
    <div class="links"><a href="/health">Health</a> · <a href="/status">Status</a></div>
  </div>
</body>
</html>
```

## Component 3: Middleware Passthrough Fixes

Modify `app/middleware/critical_state.py`:

### Current behavior (broken)
- `/` → 503 JSON (user sees raw JSON, can't load app)
- `/assets/*` → 503 (SPA JS/CSS blocked)

### New behavior
```
Request arrives during critical state
    │
    ├── Is it a passthrough path? (/health, /ready, /metrics, etc.)
    │   └── YES → proceed normally
    │
    ├── Is it a static asset? (/assets/*, /favicon.*, /manifest.*)
    │   └── YES → proceed normally (SPA overlay needs these)
    │
    ├── Is it a browser request? (Accept: text/html)
    │   └── YES → serve critical.html with reasons injected
    │
    └── Is it an API request? (Accept: application/json)
        └── YES → return 503 JSON (unchanged)
```

### Passthrough additions
```python
_PASSTHROUGH_PREFIXES = (
    # Existing
    "/health", "/ready", "/status", "/api/status", "/api/capabilities",
    "/metrics", "/docs", "/redoc", "/openapi.json", "/static",
    # New — SPA assets + frontend data endpoints
    "/assets",        # Vite-built JS/CSS
    "/favicon",       # Favicon
    "/manifest",      # PWA manifest
    "/system-info",   # Frontend model info
    "/languages",     # Frontend language list
    "/health/stream", # SSE health stream (already under /health)
    "/events",        # SSE task events
)
```

### Browser detection
```python
def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept
```

### HTML serving
Read `templates/critical.html` once at import time (cached). On each request, replace `{{REASONS}}` with `<li>` elements built from `state.system_critical_reasons`.

## Component 4: SPA CriticalOverlay

React component that renders a full-screen overlay when `system_critical: true` is detected from the health SSE stream.

### File
`frontend/src/components/system/CriticalOverlay.tsx`

### Data source
`useUIStore` — the health SSE stream already writes `systemHealth` and `healthMetrics` (which includes `system_critical` and `system_critical_reasons`).

On `prod-editorial-nav`: uses `health` from uiStore which comes from the health SSE stream.

### Behavior
- Renders `null` when system is healthy (zero overhead)
- When `system_critical: true`: renders fixed overlay at `z-50`
- Semi-transparent dark backdrop
- Centered card with warning icon, reasons list, auto-retry countdown
- All content behind overlay gets `pointer-events: none`
- Fade transition (200ms) in/out
- Auto-checks health every 10s (the SSE stream already does this at 3s interval)
- When `system_critical` goes back to `false`: overlay fades out, app resumes

### Placement
Mounted in:
- `prod-editorial-nav`: Router.tsx (alongside Header/Footer)
- `feat/editorial-redesign`: AppShell.tsx (inside the layout wrapper)

### Visual
```
┌──────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│▓▓▓  ┌────────────────────────────┐  ▓▓▓│
│▓▓▓  │          ⚠                 │  ▓▓▓│
│▓▓▓  │   System Critical          │  ▓▓▓│
│▓▓▓  │                            │  ▓▓▓│
│▓▓▓  │   • Database unreachable   │  ▓▓▓│
│▓▓▓  │   • Disk space low         │  ▓▓▓│
│▓▓▓  │                            │  ▓▓▓│
│▓▓▓  │   All operations paused.   │  ▓▓▓│
│▓▓▓  │   Checking every 10s...    │  ▓▓▓│
│▓▓▓  │                            │  ▓▓▓│
│▓▓▓  └────────────────────────────┘  ▓▓▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
└──────────────────────────────────────────┘
```

## Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| Create | `templates/critical.html` | Static critical state page |
| Create | `frontend/src/components/system/CriticalOverlay.tsx` | SPA overlay component |
| Modify | `app/services/health_monitor.py` | Add 5 new checks (FFmpeg, Redis, model, memory, output dir) |
| Modify | `app/middleware/critical_state.py` | Serve HTML to browsers, expand passthrough list |
| Modify | `frontend/src/Router.tsx` (prod-editorial-nav) | Mount CriticalOverlay |
| Modify | `frontend/src/components/layout/AppShell.tsx` (feat/editorial-redesign) | Mount CriticalOverlay |

## Not in Scope

- No changes to `state.py` (set_critical/clear_critical logic unchanged)
- No changes to force-abort behavior (already works)
- No changes to health SSE stream (already sends system_critical)
- No new API endpoints

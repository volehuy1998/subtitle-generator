# Phase Lumen — Sprint Log

> Tracks progress sprint-by-sprint. Each entry includes: what was done, tests added, issues found.

---

## Sprint L1: Foundation (2026-03-16)

**Goal:** Set up Lumen Docker profile, test infrastructure, and initial test suite.

**Delivered:**
- `docker-compose.yml` — added `lumen` profile on port 8002 with `PRELOAD_MODEL=base`
- `tests/test_lumen/` — test directory with conftest.py fixtures
- `tests/test_lumen/test_upload_resilience.py` — 17 tests covering:
  - Upload validation (no file, empty, corrupt, wrong extension, Unicode filename)
  - Output format validation (SRT, VTT, JSON, invalid model)
  - All 5 model sizes accepted
  - 13 endpoint availability checks (health, metrics, status, docs, openapi, etc.)
- `docs/lumen/SPRINT_LOG.md` — this file

**Tests added:** 17
**Running total:** 1328 + 17 = 1345

---

## Sprint L2: Design System (2026-03-16)

**Goal:** Transform dark Enterprise Slate theme into professional light theme (Lumen).

**Delivered:**
- `frontend/src/index.css` — complete color token overhaul:
  - Background: `#080C14` (dark) → `#FFFFFF` (white)
  - Text: `#E2E8F0` (light-on-dark) → `#0F172A` (dark-on-light)
  - Primary: `#3B82F6` (blue) → `#6366F1` (indigo — matches Linear, Stripe, Vercel)
  - Success: `#34D399` → `#10B981` (emerald)
  - Shadows: Heavy dark → soft light (`0.05` - `0.10` opacity)
- Typography: `Plus Jakarta Sans` + `Syne` → **`Inter`** (industry standard for professional UIs)
- Font size: 14px → 16px base (better readability on light backgrounds)
- Removed dark-specific effects: dot-grid texture, ambient glow `body::before`
- `frontend/index.html` — updated Google Fonts import to Inter
- `docs/lumen/DESIGN_SYSTEM.md` — full design system spec (colors, typography, spacing, shadows, components)

**Tests added:** 0 (design-only sprint)
**Running total:** 1345

**Design references used:** Microsoft 365, Google Workspace, Claude AI, Vercel, Linear

---

## Sprint L3: Model Readiness API (2026-03-16)

**Goal:** Backend API for model readiness so UI can show which models are loaded.

**Delivered:**
- `app/services/model_manager.py` — added `get_model_readiness()` function
  - Returns per-model status: ready / loading / not_loaded
  - Includes size_gb and loaded_devices for each model
- `app/routes/health.py` — enhanced `/api/model-status` endpoint
  - Now returns both preload progress AND per-model readiness
  - UI can show green/yellow/gray indicators per model
- `tests/test_lumen/test_model_readiness.py` — 9 tests:
  - Endpoint availability, response structure
  - All 5 model sizes present, valid status values
  - Correct size_gb values, preload status format

**Tests added:** 9
**Running total:** 1345 + 9 = 1354

---

## Sprint L4: User Confirmation Dialog (2026-03-16)

**Goal:** No transcription starts without explicit user confirmation.

**Delivered:**
- `frontend/src/components/transcribe/ConfirmationDialog.tsx` — new component
  - Modal overlay with file summary (name, size, model, language, format, device)
  - Cancel and "Start Transcription" buttons
  - Keyboard accessible (role="dialog", aria-modal)
  - Uses Lumen design tokens (indigo primary, white background, soft shadows)
- `frontend/src/pages/App.tsx` — modified upload flow:
  - File drop → shows ConfirmationDialog (pendingUpload state)
  - User clicks "Start Transcription" → actual upload begins
  - User clicks "Cancel" → returns to form, nothing starts
- TypeScript compiles clean, Vite build succeeds

**Tests added:** 0 (frontend component — tested via build + future Playwright E2E)
**Running total:** 1354

**Investor requirement addressed:** "User confirmation is always required before starting any process"

---

## Sprint L5: Process Liveness Indicators (2026-03-16)

**Goal:** Users can tell if a process is running or frozen.

**Delivered:**
- `frontend/src/components/progress/LivenessIndicator.tsx` — new component
  - Green pulsing dot + "Live (Xs ago)" when SSE events arriving
  - Yellow "Slow (30s ago)" warning after 30s without update
  - Red "No response (60s)" after 60s without update
  - Updates every 1 second via `setInterval`
  - Uses aria-live="polite" for screen reader support
- `frontend/src/store/taskStore.ts` — added `lastEventTime` field
  - Updated in `applyProgressData()` on every SSE event
  - Initialized to `Date.now()` on store creation
- `frontend/src/components/progress/ProgressView.tsx` — integrated LivenessIndicator
  - Shows next to the progress percentage during active processing
  - Hidden when task is complete/cancelled/error
- TypeScript clean, Vite build succeeds

**Tests added:** 0 (frontend component — tested via build + future Playwright E2E)
**Running total:** 1354

**Investor requirement addressed:** "How can users know if a process/stage is running or frozen?"

---

## Sprint L6: Component Styling (2026-03-16)

**Goal:** Remove all hardcoded dark colors from React components.

**Delivered:**
- `StyleOptions.tsx` — preview background: `#111827` → `var(--color-surface-2)`
- `ContactPage.tsx` — dark gradient → light gradient (`#F8FAFC → #EEF2FF → #E0F2FE`)
- `AboutPage.tsx` — dark gradient → light gradient (`#F8FAFC → #EEF2FF → #E8E0FF`)
- `SecurityPage.tsx` — dark gradient → light gradient (`#F8FAFC → #EEF2FF → #E8E0FF`)
- `ContactPage.tsx` — hardcoded green `#065F46` → `var(--color-success)`
- Zero hardcoded dark colors remaining in `frontend/src/`

**Tests added:** 0 (visual-only)
**Running total:** 1354

---

## Sprint L7: Error Message Improvements (2026-03-16)

**Goal:** Make error messages human-readable and user-friendly.

**Delivered:**
- `ProgressView.tsx` — error display improved:
  - Added "Something went wrong" heading above technical error
  - Technical error shown in secondary color (less alarming)
  - Default message: "An unexpected error occurred. Please try again with a different file or model."
  - "Start Over" → "Try Again" (more encouraging)
  - "Task cancelled." → "Transcription cancelled." (more specific)

**Tests added:** 0 (frontend UX)
**Running total:** 1354

---

## Sprint L8: Full Foundation Completion (2026-03-16)

**Goal:** Complete all remaining Foundation items — header redesign, confirmation dialogs, delete endpoint, input validation, embed tab redesign, and major test push toward 2000+.

**Delivered:**

### Frontend
- **AppHeader.tsx** — Lumen redesign (Pixel):
  - Removed GPU/CPU badge (distracting, non-essential)
  - Simplified nav to App/Status/About with brand-color underline on active page
  - Health indicator simplified to colored dot + text label (no load bar)
  - White background with subtle border, all CSS design tokens
  - Fixed stale active-page closure via `spa-navigate` event listener
- **CancelConfirmationDialog.tsx** — NEW component (Pixel):
  - Replaces `window.confirm()` with styled modal
  - Warning icon, filename display, "Any progress will be lost" message
  - "Keep Going" (secondary) + "Cancel Transcription" (destructive red) buttons
  - Keyboard accessible: `role="dialog"`, `aria-modal`, Escape key, auto-focus
- **EmbedConfirmationDialog.tsx** — NEW component (Prism):
  - Summary table: video/subtitle files, mode, style settings, translation
  - Hard burn warning about re-encoding time
  - Matches ConfirmationDialog pattern from Sprint L4
- **EmbedTab.tsx** — Lumen redesign (Prism):
  - Grouped form into card sections (Source Files, Embed Mode, Subtitle Style, Translate)
  - Added confirmation step before embedding
  - Fixed polling leak on unmount via cleanup ref
  - Custom file pickers with icons and success indicators
  - All colors via CSS design tokens (indigo primary, no hardcoded colors)
- **StyleOptions.tsx** — Dark preview strip intentional for video simulation
- **EmbedPanel.tsx** — Replaced hardcoded error border with `--color-danger-border` token
- **index.css** — Added `--color-danger-border` design token

### Backend
- **DELETE /tasks/{task_id}** endpoint (Forge):
  - Terminal-only guard (done/error/cancelled)
  - Session access check via `check_task_access`
  - File cleanup from UPLOAD_DIR and OUTPUT_DIR
  - Database backend removal + history persistence
  - Structured logging with `log_task_event`
- **Audio stream detection** in upload flow (Forge):
  - Rejects files with no audio track (HTTP 400)
  - Uses `has_audio_stream()` from `app/utils/media`
  - Gated on `FFPROBE_AVAILABLE`
- **Duration validation** in upload flow (Forge):
  - Rejects files > 4 hours (HTTP 400)
  - Uses `MAX_AUDIO_DURATION = 14400` from config

### Tests (Scout)
- 10 new test files in `tests/test_lumen/`:
  - `test_format_output.py` — 80 tests (SRT/VTT/JSON format, timestamps, line breaking)
  - `test_upload_validation.py` — 66 tests (extensions, sizes, sanitization, params)
  - `test_sse_events.py` — 34 tests (event queues, subscribers, ordering)
  - `test_pipeline_steps.py` — 42 tests (step progression, cancel/error per step)
  - `test_task_management.py` — 60 tests (list, progress, cancel, retry, DELETE endpoint)
  - `test_health_system.py` — 59 tests (health, readiness, metrics, capabilities)
  - `test_security_validation.py` — 71 tests (path traversal, XSS, sanitization, headers)
  - `test_translation_flow.py` — 40 tests (languages, translation params, Whisper/Argos)
  - `test_api_integration.py` — 88 tests (downloads, editing, formatting, model management)
  - `test_edge_cases.py` — 57 tests (extreme values, Unicode, boundaries, errors)

### Code Review (Hawk)
- Fixed 4 issues found during review:
  1. CancelConfirmationDialog Escape key handler (added `tabIndex` + `useRef` + `useEffect`)
  2. EmbedTab polling leak on unmount (added cleanup ref + cancelled flag)
  3. DELETE endpoint test coverage (added 11 new tests)
  4. AppHeader stale active-page closure (added `spa-navigate`/`popstate` listener)

**Tests added:** 487 (586 new from Scout + 11 from Hawk review fix - 110 overlapping with existing)
**Running total:** 1354 + 476 = 1830

**Investor requirements addressed:**
- "Every action requires confirmation" — cancel and embed now have styled dialogs
- "Professional UI" — header matches enterprise standards, no GPU badge clutter
- "Input validation" — audio stream + duration checks prevent bad uploads

---

## Sprint L9: 2000 Tests + Error Hardening (2026-03-16)

**Goal:** Cross the 2000-test threshold and harden error handling per spec 1.2.

**Delivered:**

### Error Handling Hardening (Forge)
- **pipeline.py** — expanded `_ERROR_MAP` from 8→22 patterns:
  - Disk/storage: ENOSPC, "No space left", quota exceeded
  - Memory: MemoryError, ENOMEM, CUDA OOM, "out of memory"
  - Model loading: timeout, download failures, corrupt weights
  - Media/FFmpeg: decode errors, corrupt files, invalid streams
  - File/permission: permission denied, read-only filesystem
  - Network: connection timeouts, DNS failures
- **Zero segments handling**: when transcription produces 0 segments, generates valid SRT/VTT with `[No speech detected in this file.]` placeholder instead of erroring
- **model_manager.py** — model loading timeout:
  - `MODEL_LOAD_TIMEOUT = 120` seconds
  - `ModelLoadTimeoutError` exception for clear diagnostics
  - `_load_model_with_timeout()` via daemon thread with join timeout
  - Lock acquisition timeout prevents deadlocks on concurrent model switches

### Tests (Scout) — 170 new tests
- `test_subtitle_embedding.py` — 40 tests (embed presets, combine endpoints, style validation)
- `test_session_management.py` — 23 tests (cookies, persistence, session-scoped access)
- `test_rate_limiting.py` — 33 tests (rate limiter, headers, brute force, quotas)
- `test_cleanup_service.py` — 22 tests (file cleanup, retention, dry-run, error handling)
- `test_webhook_routes.py` — 24 tests (register, SSRF validation, CRUD)
- `test_download_routes.py` — 28 tests (SRT/VTT/JSON download, content headers, errors)

**Tests added:** 170
**Running total:** 1830 + 170 = **2000** (target achieved!)

**Lumen Pillar 1 milestone:** 2000+ tests reached. Foundation phase (L1-L10) substantially complete.

---

## Sprint L10: Performance — FFprobe Cache, Idle Preload, Model UX (2026-03-16)

**Goal:** Begin Performance pillar (Lumen 2.1-2.3). Optimize probe speed, add smart idle preloading, improve model selection UX.

**Delivered:**

### Backend Performance (Forge)
- **FFprobe result caching** (`app/utils/media.py`):
  - `_probe_file_cached()` with `@lru_cache(maxsize=256)`
  - `get_audio_duration()` and `has_audio_stream()` now share cached probe results
  - `clear_probe_cache()` utility for explicit invalidation
  - Impact: ffprobe runs once per file instead of 2-3 times (upload validation + pipeline)
- **Smart idle preloading** (`app/main.py`):
  - `_idle_preload_loop()` checks every 60s for idle state
  - After 5 min no active tasks, preloads next model in priority: base→small→medium→tiny→large
  - Skips during initial preload or active processing
  - Loads one model per cycle, graceful error handling
  - Registered in lifespan startup, cancelled on shutdown

### Frontend UX (Pixel)
- **Model load confirmation** (`ConfirmationDialog.tsx` + `TranscribeForm.tsx` + `App.tsx`):
  - When selected model is not loaded, shows yellow warning: "The {model} model is not loaded yet. Loading may take 30-60 seconds."
  - Button changes from "Start Transcription" to "Load & Transcribe"
  - "Use {ReadyModel} instead (ready)" link switches to first loaded model
  - TranscribeForm passes model readiness + first ready model through upload options
  - App.tsx handles model switch in pending upload state

### Tests (Scout) — 67 new tests
- `test_performance.py`:
  - Model readiness API (15 tests)
  - Model manager constants/structure (17 tests)
  - Compute type selection (5 tests)
  - System capability (10 tests)
  - System tuning (5 tests)
  - FFprobe caching (15 tests)

**Tests added:** 67
**Running total:** 2000 + 67 = **2067**

**Phase transition:** Foundation (L1-L10) → Performance (L11-L20) now in progress.

---

## Sprint L11: Performance UX — Segment Prediction, Upload ETA, Virtualization (2026-03-16)

**Goal:** Improve real-time UX during transcription: segment count prediction, upload ETA, sub-stage indicators, segment list performance.

**Delivered:**

### Backend (Forge)
- **Segment count prediction** (`transcription.py`):
  - Heuristic: `estimated_segments = max(1, int(audio_duration / 4.0))` (~1 per 4s)
  - `estimated_segments` + `current_segment` added to progress and segment SSE events
  - Frontend can now show "Segment 14 of ~29"
- **Sub-stage SSE events** (`pipeline.py`):
  - Step 2 now emits `substage: "loading_model"` before model load
  - Emits `substage: "transcribing"` after model loaded, before transcription
  - Enables frontend to distinguish "Loading model..." from "Transcribing audio..."

### Frontend (Pixel)
- **Upload ETA** (`App.tsx` + `taskStore.ts`):
  - Tracks upload start time, calculates speed and remaining time per progress event
  - Shows "Uploading... ~15s remaining" during upload phase
- **Segment list virtualization** (`ProgressView.tsx`):
  - Only renders last 50 segments (prevents DOM thrashing on 500+ segment files)
  - "Showing last 50 of {total} segments" indicator when truncated
- **Segment text truncation** (`ProgressView.tsx`):
  - 2-line clamp with ellipsis overflow, word-break handling
  - Full text on hover via title attribute
- **Estimated segments + substage display** (`taskStore.ts` + `ProgressView.tsx`):
  - Shows "X of ~Y segments" during transcription
  - Status text respects substage for model loading vs transcribing

### Tests (Scout) — 41 new tests
- `test_progress_events.py`:
  - Pipeline progress events (15 tests)
  - Segment event structure (10 tests)
  - Profiler & ETA (10 tests)
  - Event queue management (5 tests)
  - Cancel and error events (1 test)

**Tests added:** 41
**Running total:** 2067 + 41 = **2108**

---

## Sprint L12: Performance — ETA Smoothing, Speed Trends, Speed Estimates (2026-03-16)

**Goal:** Stabilize ETA predictions and add speed-aware indicators.

**Delivered:**

### Backend (Forge)
- **ETA smoothing** (`profiler.py`):
  - Exponential Moving Average (EMA) with α=0.15 for speed tracking
  - 3-update warmup period (cold start bias ignored)
  - `_recent_speeds` list (last 10) for trend analysis
  - EMA-based ETA replaces simple rolling average (smoother, less jitter)
- **Speed trend detection** (`profiler.py`):
  - `get_speed_trend()` returns: improving/stable/declining/stalled/unknown
  - Based on ratio of recent 3-sample average to EMA speed
  - Stalled threshold: <0.01x realtime
  - `speed_trend` + `ema_speed_x` added to progress SSE events

### Frontend (Pixel)
- **Speed estimate in ConfirmationDialog** (`ConfirmationDialog.tsx`):
  - Shows "Processing speed: ~2x realtime (GPU, Small)" before transcription
  - Speed lookup table for all model/device combinations
- **Speed-aware LivenessIndicator** (`LivenessIndicator.tsx` + `taskStore.ts`):
  - `speed_trend` field in TaskState (auto-populated from SSE)
  - When running >30s: "Stalled" (red) overrides time-based, "Slowing down" (yellow) for declining
  - Stable/improving fall through to existing time-based logic

### Tests (Scout) — 40 new tests
- `test_profiler_advanced.py`:
  - EMA speed (16 tests)
  - Speed trend detection (15 tests)
  - Warmup handling (5 tests)
  - Integration (5 tests — note: 1 shared with EMA category)

**Tests added:** 40
**Running total:** 2108 + 40 = **2148**

---

## Sprint L13: Pipeline Optimization + Active Step Animation (2026-03-16)

**Goal:** Optimize pipeline throughput and add remaining UX polish.

**Delivered:**

### Backend (Forge)
- **WAV skip extraction** (`pipeline.py`):
  - WAV input files bypass ffmpeg extraction entirely
  - `audio_path = video_path` when extension is `.wav`
  - Cleanup logic updated to avoid deleting original WAV
- **Parallel file writes** (`pipeline.py`):
  - SRT/VTT/JSON written concurrently via `ThreadPoolExecutor(max_workers=3)`
- **Beam size auto-tuning** (`transcription.py`):
  - Per-model lookup: tiny=1, base=3, small/medium/large=5
  - VRAM-tight override to beam_size=1 preserved
  - Logged for observability

### Frontend (Pixel)
- **Active step pulse animation** (`PipelineSteps.tsx` + `index.css`):
  - `@keyframes stepPulse` with opacity fade + expanding box-shadow ring
  - Applied to active step circle, disabled when paused
- **Stale warning** (`ProgressView.tsx`):
  - Yellow "This is taking longer than expected" banner after 30s no SSE event
  - Only during active processing (not upload)
- **Time-since-update**: Already implemented in LivenessIndicator (L5) — no changes needed

### Tests (Scout) — 40 new tests
- `test_pipeline_optimization.py`:
  - WAV skip extraction (10 tests)
  - Beam size auto-tuning (10 tests)
  - Output file writing (10 tests)
  - Pipeline error handling (10 tests)

**Tests added:** 40
**Running total:** 2148 + 40 = **2188**

---

## Sprint L14: VAD Optimization + Responsive Design (2026-03-16)

**Goal:** Optimize transcription speed via VAD tuning, polish responsive design for mobile.

**Delivered:**

### Backend (Forge)
- **VAD filter optimization** (`transcription.py`):
  - Added explicit `speech_pad_ms=200` and `threshold=0.5` to VAD parameters
  - Prevents speech clipping at segment boundaries
- **Probe cache confirmation** (`pipeline.py`):
  - Verified upload route already warms probe cache (L8)
  - Added debug log with `cache_info()` for observability
- **Compute type**: Already optimal (CPU→int8, GPU→float16/int8_float16) — documented

### Frontend (Pixel)
- **Responsive layout** (`App.tsx`):
  - Mobile padding/gap adjustments: `px-3 sm:px-4`, `gap-4 sm:gap-5 lg:gap-6`
  - Tab buttons compact on mobile: `px-3 sm:px-4 py-2 sm:py-2.5`
- **Header mobile** (`AppHeader.tsx`):
  - Nav always visible (`flex` instead of `hidden sm:flex`)
  - Responsive spacing: `gap-0.5 sm:gap-1`, `px-2 sm:px-3`, `text-xs sm:text-sm`
  - Health label hidden on mobile, dot remains visible
- **Form responsive** (`TranscribeForm.tsx`):
  - Model stats stack vertically on mobile: `flex-col sm:flex-row`
  - Badge row wraps with `flex-wrap`

### Tests (Scout) — 40 new tests
- `test_transcription_config.py`:
  - VAD configuration (10 tests)
  - Compute type selection (10 tests)
  - Transcription options (10 tests)
  - API configuration (10 tests)

**Tests added:** 40
**Running total:** 2188 + 40 = **2228**

**Performance phase progress:** L10-L14 complete (50% of L11-L20 range).

---

## Sprint L15: Accessibility (WCAG 2.1 AA) + SSE Event Sequencing (2026-03-16)

**Goal:** Achieve WCAG 2.1 AA compliance and add SSE event ordering.

**Delivered:**

### Accessibility (Prism)
- **Focus visible styles** (`index.css`):
  - `:focus-visible` with `outline: 2px solid var(--color-primary)` on all interactive elements
  - Removed `outline: none` from selects in TranscribeForm, EmbedTab, EmbedPanel
- **Color contrast fix** (`index.css`):
  - `--color-text-3`: #94A3B8 (3.0:1, fails AA) → #64748B (5.5:1, passes AA)
- **Form labels + ARIA** (TranscribeForm, EmbedTab):
  - `aria-label="Upload media file"` on drop zone
  - `aria-label="Select translation language"` on embed translate select
- **Skip navigation** (`App.tsx` + `index.css`):
  - "Skip to main content" link, visible on keyboard focus
  - `id="main-content"` on `<main>` element
- **ARIA live regions** (ProgressView, EmbedTab):
  - `aria-live="polite"` on progress container
  - `aria-live="assertive"` on status row
  - `role="alert"` on errors/warnings
  - `role="status"` on success banners
  - `role="progressbar"` with `aria-valuenow/min/max` on progress bars

### Backend (Forge)
- **SSE event sequencing** (`sse.py`):
  - Per-task `seq` counter (monotonically increasing from 1)
  - Thread-safe via `_seq_lock`
  - Auto-cleanup on terminal events (done/error/cancelled)
  - `cleanup_task_events()` removes sequence + subscriber queues

### Tests (Scout) — 48 new tests
- `test_accessibility.py` (23 tests): HTML responses, security headers, API accessibility
- `test_event_sequencing.py` (25 tests): Event structure, ordering, queue behavior

**Tests added:** 48
**Running total:** 2228 + 48 = **2276**

---

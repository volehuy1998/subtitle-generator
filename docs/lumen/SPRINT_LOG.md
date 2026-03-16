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

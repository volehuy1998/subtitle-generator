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

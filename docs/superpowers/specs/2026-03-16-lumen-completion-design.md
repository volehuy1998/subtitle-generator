# Phase Lumen Completion — Design Spec

> **Date:** 2026-03-16
> **Author:** Atlas (Tech Lead)
> **Approach:** Compressed Finish (L61-L80)
> **Target:** `newui.openlabs.club`

## Goal

Complete Phase Lumen by closing all remaining gaps in 20 sprints (L61-L80), achieving all 8 success criteria, and deploying to `newui.openlabs.club` for investor review.

## Current State

- **60 sprints complete** (L1-L60), 3,317 tests passing
- **6 of 8 success criteria met** — missing cross-browser/mobile testing and investor approval
- **Frontend tests severely lacking** — 26 tests for 67 files
- **E2E tests shallow** — 85 Playwright tests, no real workflow coverage
- **Backend test gaps** — audit trail, brute force, quarantine, S3 untested
- **pipeline.py** — 572-line monolith needs refactoring into step functions

## Parallel Execution Model

Sprints execute in parallel waves, not sequentially.

```
Wave 1 (L61-L66): Backend Hardening + Frontend Unit Tests — ALL PARALLEL
├── Forge: L61 pipeline refactor + L65 error hardening
├── Bolt: L66 API completeness audit
├── Scout: L62 security test gaps + L63 infra test gaps
├── Shield: L62 security test review + L64 middleware tests
├── Pixel: L67 store/hook tests + L68 UI primitive tests
├── Prism: L69 feature component tests + L70 layout/system tests
└── Quill: Doc accuracy tracking throughout

Wave 2 (L71-L78): E2E + Cross-Browser + Responsive — ALL PARALLEL
├── Scout: L71 core upload E2E + L72 embed E2E + L73 navigation E2E
├── Bolt: L74 settings E2E + L75 error/edge E2E
├── Pixel: L76 responsive validation + L78 accessibility audit
├── Prism: L76 responsive fixes (pair with Pixel)
├── Shield: L78 security review of all changes
└── Scout: L77 cross-browser testing

Wave 3 (L79-L80): Final Integration + Deploy
├── Scout + Stress: L79 full integration + performance benchmarks
├── Harbor + Anchor: L80 Docker build + deploy to newui.openlabs.club
├── Quill: L80 final doc update (module counts, test counts, version)
└── Hawk: Final review gate
```

## Sprint Details

### Wave 1: Backend Hardening + Frontend Tests (PARALLEL)

**L61: pipeline.py Refactoring (Forge)**
- Split `process_video()` (572 lines) into step functions:
  - `_step_probe()`, `_step_extract()`, `_step_transcribe()`
  - `_step_diarize()`, `_step_translate()`, `_step_finalize()`
- Preserve all SSE events and error handling
- Zero behavior change — pure refactor

**L62: Backend Test Gaps — Security (Scout + Shield)**
- Audit trail HMAC verification tests
- Brute force middleware tests (IP blocking, persistence)
- Quarantine/ClamAV integration tests (mocked clamd)
- FFmpeg injection edge cases

**L63: Backend Test Gaps — Infrastructure (Scout)**
- S3/MinIO storage backend tests (mocked boto3)
- Redis pub/sub relay tests (mocked redis)
- Database backend transaction tests
- Model manager cache eviction + concurrent load tests

**L64: Backend Test Gaps — Middleware (Shield)**
- Slow query logging middleware tests
- Complete middleware stack ordering validation
- Session management edge cases (expiry, concurrent, cookie)
- Rate limiter Redis fallback path tests

**L65: Error Handling Hardening (Forge)**
- Verify all 17 error codes return correct HTTP status + structured response
- Test error sanitization (no paths, DB URLs, tracebacks leak)
- WebSocket cleanup on ungraceful disconnect
- S3 upload retry with exponential backoff

**L66: API Completeness Audit (Bolt)**
- Focus on untested endpoints only (cross-reference existing test coverage)
- Verify OpenAPI spec matches actual behavior for gap endpoints
- Response schema consistency for auth, webhook, export, tracking routes
- Rate limit headers present on rate-limited routes

**L67: Frontend Unit Tests — Stores + Hooks (Pixel)**
- Framework: Vitest + React Testing Library + jsdom (already configured in `frontend/vitest.config.ts`)
- Complete taskStore tests (all 14 actions)
- preferencesStore + toastStore tests
- useTheme, useFocusTrap, useTaskQueue hook tests

**L68: Frontend Unit Tests — UI Primitives (Pixel)**
- Button, Badge, Card, Dialog, Input, Select, Tooltip, StatusIndicator, Skeleton
- All variants, sizes, states (disabled, loading, error)
- Accessibility: role, aria-label, keyboard interaction

**L69: Frontend Unit Tests — Feature Components (Prism)**
- TranscribeForm: model selection, file validation, format switching
- ConfirmationDialog: summary display, cancel/confirm actions
- ProgressView: step transitions, segment display, stale detection
- OutputPanel: download button states, copy-to-clipboard

**L70: Frontend Unit Tests — Layout + System (Prism)**
- AppHeader: navigation, theme toggle, health indicator
- Footer: session info, SSE status
- ConnectionBanner: reconnect states
- HealthPanel: metric display, alert states
- ErrorBoundary: error catching, fallback UI

### Wave 2: E2E + Cross-Browser + Responsive (PARALLEL)

**E2E Mock Strategy:** All E2E tests use MSW (Mock Service Worker) to intercept API calls with realistic fixtures. No real Whisper model needed. MSW handlers already exist in `frontend/src/mocks/handlers.ts`. Backend E2E tests use the existing conftest.py mocking (torch, faster_whisper, psutil, argos mocked).

**L71: E2E — Core Upload Flow (Scout)**
- Upload file → confirmation → transcription → progress → download
- Cancel mid-transcription → verify cleanup
- Upload invalid file → verify error message

**L72: E2E — Embedding Flow (Scout)**
- Complete embed workflow (soft + hard)
- Style preset selection → preview → embed → download
- Combine external video + subtitle

**L73: E2E — Navigation + Pages (Scout)**
- SPA navigation between all 5 pages
- Status page: component health, incident display
- Browser back/forward, deep linking

**L74: E2E — Settings + Preferences (Bolt)**
- Theme toggle persistence across page reloads
- Preferences panel saves/restores all settings
- Keyboard shortcuts (1, 2, ?, Esc)
- Task history search + filter

**L75: E2E — Error + Edge Cases (Bolt)**
- Connection loss → reconnect banner → recovery
- System critical state → upload blocked
- Session restore on page reload

**L76: Responsive Validation + Fixes (Pixel + Prism)**
- Test breakpoints: 375px, 768px, 1024px, 1440px
- Fix layout breaks at each breakpoint
- Verify touch targets ≥ 44px on mobile
- Model grid column hiding works correctly

**L77: Cross-Browser Testing (Scout)**
- Playwright multi-browser: Chromium, Firefox, WebKit
- SSE works across all browsers
- File upload/drag-drop across browsers
- Theme switching across browsers

**L78: Accessibility Audit (Pixel + Shield)**
- WCAG 2.1 AA compliance check
- Screen reader: all interactive elements labeled
- Keyboard-only navigation end-to-end
- Focus indicators on all interactive elements
- Color contrast ≥ 4.5:1

### Wave 3: Integration + Deploy

**L79: Full Integration + Benchmarks (Scout + Stress)**
- Run complete test suite: all backend + frontend + E2E
- API response times < 200ms (p95)
- Memory stability over 100 requests
- Concurrent task handling (3 simultaneous)

**L80: Deploy to newui.openlabs.club (Harbor + Anchor)**
- Build React SPA (`npm run build`)
- Docker image build + push
- Deploy to newui.openlabs.club
- Smoke test: upload → transcribe → download on live site
- All health checks pass
- Quill updates CLAUDE.md (module counts, test counts, sprint count)
- Notify investor for review

## Engineer Assignments (Balanced)

| Engineer | Sprints | Load |
|----------|---------|------|
| Forge (Sr. Backend) | L61, L65 | 2 sprints |
| Bolt (Jr. Backend) | L66, L74, L75 | 3 sprints |
| Scout (QA Lead) | L62, L63, L71-L73, L77, L79 | 7 sprints |
| Shield (Security) | L62, L64, L78 | 3 sprints |
| Pixel (Sr. Frontend) | L67, L68, L76, L78 | 4 sprints |
| Prism (UI/UX) | L69, L70, L76 | 3 sprints |
| Stress (Perf) | L79 | 1 sprint |
| Harbor (DevOps) | L80 | 1 sprint |
| Anchor (Infra) | L80 | 1 sprint |
| Quill (Docs) | L80 + throughout | Standing order |
| Hawk (Review) | All sprints | Standing order |

## Success Criteria (All 8 Required)

1. Zero known bugs — all test gaps closed
2. 2000+ tests passing — target ~4,000+
3. Model loads in <5s — already achieved
4. UI matches enterprise standards — already achieved
5. Every action requires confirmation — already achieved
6. Every process shows liveness — already achieved
7. Cross-browser and mobile tested — L76-L78
8. Investor approves — after L80 deploy

## Non-Goals (Deferred Post-Lumen)

- API key hash migration (separate production blocker)
- mypy/pyright in CI
- GPU real-hardware testing
- Multi-server distributed deployment
- Visual regression testing (Playwright screenshots)

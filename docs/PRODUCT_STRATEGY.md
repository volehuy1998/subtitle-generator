# Product Strategy — Subtitle Generator

**Document Owner:** Atlas, Tech Lead — Team Sentinel
**Created:** 2026-03-14
**Last Updated:** 2026-03-14
**Status:** Living document — reviewed quarterly

---

## Table of Contents

1. [Product Vision & Mission](#1-product-vision--mission)
2. [Product Architecture](#2-product-architecture)
3. [Feature Definition](#3-feature-definition)
4. [Development Roadmap](#4-development-roadmap)
5. [Quality Strategy](#5-quality-strategy)
6. [Frontend Strategy](#6-frontend-strategy)
7. [Backend Strategy](#7-backend-strategy)
8. [Security Strategy](#8-security-strategy)
9. [Infrastructure Strategy](#9-infrastructure-strategy)
10. [Team Scaling Plan](#10-team-scaling-plan)
11. [Maintenance & Operations](#11-maintenance--operations)
12. [Success Metrics](#12-success-metrics)

---

## 1. Product Vision & Mission

### Vision

**Make every piece of audio and video content accessible to every person on Earth, regardless of language or ability.**

### Mission

Build a production-grade, self-hostable subtitle generation platform that combines state-of-the-art speech recognition with neural machine translation and professional subtitle tooling, serving content creators, educators, journalists, enterprises, and accessibility advocates at global scale.

### Target Users

| Segment | Needs | Scale |
|---------|-------|-------|
| **Content Creators** | Fast turnaround, multiple languages for YouTube/TikTok, style control | Individual, high volume |
| **Journalists** | Accurate transcription of interviews, speaker identification, timestamped quotes | Small teams, precision-critical |
| **Educators** | Lecture transcription, translation for international students, accessibility compliance | Institutions, batch processing |
| **Enterprises** | API integration, team workspaces, audit trails, SLAs, on-premise deployment | Large orgs, compliance-heavy |
| **Accessibility Advocates** | WCAG compliance, accurate captions for deaf/HoH communities, SDH support | NGOs, government, regulated industries |
| **Localization Studios** | Batch translation, style consistency, QA workflows, format flexibility | Professional teams, high throughput |

### Global Scale Considerations

| Dimension | Current State | Target State |
|-----------|---------------|--------------|
| **Languages** | ~99 via faster-whisper | 99 transcription + 50+ translation pairs via Argos |
| **RTL Support** | Not yet implemented | Full RTL rendering for Arabic, Hebrew, Persian, Urdu in subtitles and UI |
| **Unicode** | UTF-8 throughout | Full Unicode 15.0 support including CJK, Devanagari, Thai, emoji |
| **CDN** | None | CloudFront/Cloudflare for static assets and subtitle file delivery |
| **Regions** | Single server (US) | Multi-region: US-East, EU-West, AP-Southeast (see Infrastructure Strategy) |
| **Compliance** | Basic | GDPR (EU), CCPA (US), PIPEDA (CA), accessibility mandates (Section 508, EN 301 549) |

---

## 2. Product Architecture

### Current Feature Map

```
+------------------------------------------------------------------+
|                        SUBTITLE GENERATOR                         |
+------------------------------------------------------------------+
|                                                                    |
|  INGEST            PROCESS              OUTPUT          DELIVER    |
|  +----------+      +--------------+     +----------+   +--------+ |
|  | Upload   |----->| Transcribe   |---->| SRT      |-->|Download| |
|  | (file)   |      | (whisper)    |     | VTT      |   |        | |
|  +----------+      +--------------+     | JSON     |   +--------+ |
|       |                  |              +----------+       |       |
|       |                  v                   |             |       |
|       |            +-----------+             v             |       |
|       |            | Translate |       +-----------+       |       |
|       |            | (Whisper/ |       | Embed     |       |       |
|       |            |  Argos)   |       | (soft/    |       |       |
|       |            +-----------+       |  hard)    |       |       |
|       |                  |             +-----------+       |       |
|       |                  v                   |             |       |
|       |            +-----------+             v             |       |
|       |            | Diarize   |       +-----------+       |       |
|       |            | (pyannote)|       | Combine   |       |       |
|       |            +-----------+       | (video+   |       |       |
|       |                                |  subs)    |       |       |
|       |                                +-----------+       |       |
|       |                                                    |       |
+------------------------------------------------------------------+
|  REAL-TIME TRANSPORT: SSE | WebSocket | Polling            |       |
+------------------------------------------------------------------+
|  MONITORING: Health | Metrics | Analytics | Audit          |       |
+------------------------------------------------------------------+
```

### Core Flow: Upload -> Transcribe -> Download

```
User                    Frontend                 Backend                  Worker
 |                         |                        |                       |
 |-- Upload file --------->|                        |                       |
 |                         |-- POST /upload ------->|                       |
 |                         |<-- task_id ------------|                       |
 |                         |                        |-- spawn thread ------>|
 |                         |-- GET /events/{id} --->|                       |
 |                         |<-- SSE: probing -------|<-- probe (ffprobe) ---|
 |                         |<-- SSE: extracting ----|<-- extract audio -----|
 |                         |<-- SSE: loading -------|<-- load model --------|
 |                         |<-- SSE: transcribing --|<-- transcribe --------|
 |                         |<-- SSE: formatting ----|<-- format & write ----|
 |                         |<-- SSE: completed -----|<-- done --------------|
 |<-- Show results --------|                        |                       |
 |-- Click download ------>|-- GET /download/{id} ->|                       |
 |<-- SRT/VTT/JSON file --|<-- file response ------|                       |
```

### Extended Flow: Translate

```
  [ Core Flow ] --> SSE: translating --> Whisper translate (en only)
                                     --> Argos translate (any pair)
                --> SSE: completed   --> Translated subtitle files available
```

### Extended Flow: Embed (Soft / Hard)

```
  [ Core Flow or Upload Existing ] --> POST /embed
      |
      +--> Soft embed: ffmpeg mux SRT into MKV/MP4 container (no re-encode, fast)
      |
      +--> Hard burn: ffmpeg ASS filter overlay, re-encode video (slow, permanent)
      |
      +--> SSE: embed_progress --> SSE: embed_complete --> Download embedded video
```

### Extended Flow: Combine

```
  User uploads: video file + subtitle file (SRT/VTT)
      |
      +--> POST /combine --> validation --> embed --> Download combined video
```

### Planned Flows

| Flow | Description | Target |
|------|-------------|--------|
| **Batch Processing** | Upload multiple files, queue processing, bulk download as ZIP | Q2 2026 |
| **API-First** | RESTful API with versioning, webhooks for completion, API key management | Q2 2026 |
| **Collaboration** | Team workspaces, shared projects, subtitle editing, review/approve | Q3 2026 |
| **Real-Time** | Live audio stream transcription via WebSocket | 2027 |
| **Plugin System** | Third-party extensions for custom formats, translation engines, post-processing | Q4 2026 |

---

## 3. Feature Definition

### Tier 1 — Core (Must Work Perfectly)

These features are the foundation. Zero tolerance for bugs or regressions.

| Feature | Description | Status | Quality Bar |
|---------|-------------|--------|-------------|
| **File Upload** | Accept audio/video up to 2 GB, validate format/size/duration | DONE | <500ms validation, clear error messages |
| **Transcription** | faster-whisper (CTranslate2) with model selection (tiny/base/small/medium/large) | DONE | WER within 5% of OpenAI Whisper baseline |
| **SRT Download** | Standard SubRip format with proper timestamps, UTF-8, line breaking | DONE | 100% compliant with SRT spec |
| **VTT Download** | WebVTT format with proper headers and cue formatting | DONE | 100% compliant with WebVTT spec |
| **JSON Download** | Structured JSON with segments, timestamps, confidence scores | DONE | Stable schema, backward compatible |
| **Progress Tracking** | Real-time progress via SSE with step-by-step updates | DONE | <1s latency, no dropped events |
| **Error Handling** | Graceful failures with user-friendly messages, no silent drops | DONE | Every error path returns actionable message |

### Tier 2 — Essential (High Value)

Features that make the product genuinely useful beyond basic transcription.

| Feature | Description | Status | Priority |
|---------|-------------|--------|----------|
| **Translation (Whisper)** | Any language to English via Whisper's built-in translate task | DONE | — |
| **Translation (Argos)** | Any-to-any language pairs via offline neural MT | DONE | — |
| **Soft Embed** | Mux subtitle track into MKV/MP4 without re-encoding | DONE | — |
| **Hard Burn** | Render subtitles permanently into video via ASS overlay | DONE | — |
| **Model Selection** | User chooses model size (speed vs accuracy trade-off) | DONE | — |
| **Combine** | Upload video + external subtitle file for embedding | DONE | — |
| **Auto-Embed** | Automatically embed after transcription completes | DONE | — |
| **Task Cancellation** | Cancel in-flight transcription jobs | DONE | — |

### Tier 3 — Professional (Differentiation)

Features that separate this product from commodity transcription tools.

| Feature | Description | Status | Target |
|---------|-------------|--------|--------|
| **Speaker Diarization** | Identify and label different speakers via pyannote | DONE | — |
| **Word-Level Timestamps** | Per-word timing for karaoke-style subtitles | PLANNED | Q2 2026 |
| **Batch Upload** | Upload and process multiple files in one session | PLANNED | Q2 2026 |
| **Style Presets** | Configurable font, size, color, position, background for hard burn | DONE | — |
| **Subtitle Editor** | In-browser editing of transcription results before download | PLANNED | Q2 2026 |
| **Custom Vocabulary** | User-defined word lists for domain-specific accuracy | PLANNED | Q3 2026 |
| **Format Conversion** | Convert between SRT, VTT, ASS, SSA, TTML, DFXP | PLANNED | Q2 2026 |
| **Audio Extraction** | Download extracted audio track from video | PLANNED | Q2 2026 |

### Tier 4 — Enterprise (Future)

Features for organizational adoption and paid tiers.

| Feature | Description | Target |
|---------|-------------|--------|
| **API Access** | Versioned REST API with documentation, rate limits, usage tracking | Q2 2026 |
| **API Key Management** | Create, rotate, revoke keys; per-key rate limits and permissions | Q2 2026 |
| **Team Workspaces** | Multi-user projects, shared transcription history, role-based access | Q3 2026 |
| **Webhook Integrations** | HTTP callbacks on task completion, failure, progress milestones | Q2 2026 |
| **Custom Models** | Upload fine-tuned Whisper models for domain-specific use | Q4 2026 |
| **Usage Analytics** | Per-user/team dashboards: minutes transcribed, languages, costs | Q3 2026 |
| **SSO Integration** | SAML/OIDC for enterprise identity providers | Q3 2026 |
| **Audit Logging** | Immutable audit trail for compliance (SOC 2, HIPAA) | DONE (basic), Q3 2026 (full) |
| **SLA Tiers** | Guaranteed processing times, priority queuing, dedicated resources | Q4 2026 |

### Tier 5 — Platform (Long-Term)

Features that transform the product from a tool into a platform.

| Feature | Description | Target |
|---------|-------------|--------|
| **Plugin System** | Extension API for custom translation engines, post-processors, formats | Q4 2026 |
| **Marketplace** | Community plugins, shared style presets, custom models | 2027 |
| **Self-Hosted Enterprise** | Air-gapped deployment package with installer and management console | 2027 |
| **Real-Time Transcription** | Live audio/video stream transcription via WebSocket | 2027 |
| **Live Streaming** | Real-time subtitle overlay for live broadcasts (OBS integration) | 2027+ |
| **Mobile App** | iOS/Android companion for recording + transcription on device | 2027+ |
| **Federated Processing** | Distribute work across customer's own GPU fleet | 2027+ |

---

## 4. Development Roadmap

### Q1 2026 — Foundation & Stability (COMPLETED)

**Theme:** Build a solid, well-tested, production-ready single-server product.

| Sprint | Deliverables | Status |
|--------|-------------|--------|
| Sprint 1-5 | Core pipeline: upload, transcribe, download SRT/VTT/JSON | DONE |
| Sprint 6-10 | Translation (Whisper + Argos), subtitle embedding, combine | DONE |
| Sprint 11-15 | Analytics, health monitoring, cleanup, rate limiting, audit | DONE |
| Sprint 16-20 | PostgreSQL persistence, Alembic migrations, task backend | DONE |
| Sprint 21-25 | Multi-server architecture (web/worker roles), Redis pub/sub, S3 storage | DONE |
| Sprint 26-30 | React SPA frontend, SSE/WebSocket, CI pipeline, 1326 tests | DONE |

**Key Metrics Achieved:**
- 1326 automated tests passing
- CI pipeline: lint + test + build (fully green)
- Sub-second file validation
- 3 concurrent task processing
- Full real-time progress via SSE

### Q2 2026 — Scale & API (April - June)

**Theme:** Distributed deployment, batch processing, API-first, performance optimization.

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| 31-32 | **Distributed Deploy** | Ansible playbooks for 5-server cluster (sub-ctrl, sub-api-1, sub-api-2, sub-data, sub-worker-1). Load balancer config. Health check orchestration. |
| 33-34 | **Batch Processing** | Multi-file upload UI, queue management, bulk download as ZIP, batch progress tracking. |
| 35-36 | **API v1** | Versioned API (`/api/v1/`), OpenAPI 3.1 spec, API key management UI, rate limit dashboard, webhook delivery with retries. |
| 37-38 | **Performance** | Model preloading optimization, connection pooling (PgBouncer), Redis caching for repeated transcriptions, CDN for static assets. |
| 39-40 | **Subtitle Editor** | In-browser timeline editor for adjusting timestamps, editing text, splitting/merging segments. Format conversion (SRT/VTT/ASS/TTML). |
| 41-42 | **Word-Level Timestamps** | Per-word timing output, karaoke-style VTT, highlight-as-spoken mode in preview. |

**Q2 Exit Criteria:**
- 5-server cluster running in production
- API v1 documented and stable
- 10+ concurrent tasks across worker pool
- Batch upload of 20 files in single session
- p99 transcription latency under 2x real-time for `base` model on CPU

### Q3 2026 — Enterprise & Collaboration (July - September)

**Theme:** Multi-user, team features, compliance, mobile responsive.

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| 43-44 | **Authentication Overhaul** | OAuth2 with PKCE, social login (Google, GitHub), session management, password reset. |
| 45-46 | **Team Workspaces** | Organizations, team membership, shared project folders, role-based access (admin/editor/viewer). |
| 47-48 | **Webhook Integrations** | Configurable webhook endpoints per workspace, event filtering, delivery logs, retry with exponential backoff. |
| 49-50 | **Mobile Responsive** | Fully responsive UI, touch-optimized controls, mobile upload from camera roll. |
| 51-52 | **i18n — UI Localization** | UI in 20 languages, RTL layout support, locale-aware date/number formatting. |
| 53-54 | **Compliance** | GDPR data export/deletion, CCPA opt-out, SOC 2 Type I preparation, enhanced audit logging. |

**Q3 Exit Criteria:**
- OAuth2 login with 3+ identity providers
- Team workspaces with RBAC
- WCAG 2.1 AA compliance
- UI available in 10+ languages
- GDPR Article 17 (right to erasure) fully implemented

### Q4 2026 — Platform & Enterprise Self-Hosted (October - December)

**Theme:** Extensibility, marketplace foundations, enterprise packaging.

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| 55-56 | **Plugin System** | Plugin API v1: hooks for post-transcription, custom translation, output format. Plugin manifest format, sandbox execution. |
| 57-58 | **Custom Models** | Upload fine-tuned CTranslate2 models, model validation, A/B testing between models. |
| 59-60 | **Marketplace MVP** | Community plugin directory, rating/reviews, one-click install. Shared style presets. |
| 61-62 | **Self-Hosted Package** | Docker Compose bundle, Helm chart for Kubernetes, installation wizard, license management. |
| 63-64 | **SLA & Billing** | Usage metering, tiered plans (free/pro/enterprise), Stripe integration, priority queuing. |
| 65-66 | **Observability** | Distributed tracing (OpenTelemetry), centralized logging (Loki/ELK), Grafana dashboards, PagerDuty integration. |

**Q4 Exit Criteria:**
- Plugin API stable with 3+ example plugins
- Self-hosted enterprise package installable in <30 minutes
- Marketplace with 5+ community contributions
- Full observability stack deployed
- SOC 2 Type I audit completed

### 2027+ — AI Improvements & Platform Maturity

| Initiative | Description | Timeline |
|------------|-------------|----------|
| **Real-Time Transcription** | WebSocket-based live audio stream processing with <3s latency | H1 2027 |
| **Fine-Tuned Models** | Domain-specific models (medical, legal, technical) trained on customer data | H1 2027 |
| **Live Streaming** | OBS plugin for real-time subtitle overlay on live broadcasts | H2 2027 |
| **Mobile Apps** | Native iOS/Android with on-device transcription (whisper.cpp) | H2 2027 |
| **Federated Processing** | Customer-managed GPU nodes joining processing pool | 2028 |
| **Multi-Modal** | Video scene description, speaker face recognition, emotion detection | 2028 |

---

## 5. Quality Strategy

### Test Pyramid

```
              /\
             /  \         5% E2E Tests (Playwright)
            /    \        - Critical user journeys
           /------\       - Cross-browser validation
          /        \
         /          \     15% Integration Tests
        /            \    - API endpoint contracts
       /              \   - Database operations
      /                \  - Service interactions
     /------------------\
    /                    \
   /                      \  80% Unit Tests
  /                        \ - Business logic
 /                          \- Utility functions
/____________________________\- Data transformations
```

### Coverage Targets by Quarter

| Quarter | Unit | Integration | E2E | Total Tests | Line Coverage |
|---------|------|-------------|-----|-------------|---------------|
| Q1 2026 (actual) | 85% | 12% | 3% | 1,326 | ~70% |
| Q2 2026 | 85% | 15% | 5% | 2,000+ | 80% |
| Q3 2026 | 85% | 15% | 5% | 2,800+ | 85% |
| Q4 2026 | 80% | 15% | 5% | 3,500+ | 85% |

### Performance SLOs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Transcription Latency** | < 2x real-time (base model, CPU) | p99 of task duration / audio duration |
| **Upload Acceptance** | < 500ms for validation + task creation | p99 of POST /upload response |
| **API Response (non-transc.)** | < 200ms | p99 of all non-transcription endpoints |
| **SSE Event Delivery** | < 1s from state change to client | p99 of event propagation delay |
| **Throughput** | 10 tasks/min sustained (5-server cluster) | Rolling 5-minute average |
| **Availability** | 99.5% monthly uptime | Excludes planned maintenance windows |
| **Error Rate** | < 1% of transcription tasks fail | Rolling 24-hour window |
| **File Download** | < 2s for subtitle files, < 30s for embedded video | p95 of download initiation |

### Security Posture

| Area | Approach | Frequency |
|------|----------|-----------|
| **OWASP Top 10** | Automated scanning (ZAP), manual review of new routes | Every release |
| **CodeQL** | Static analysis in CI pipeline | Every PR |
| **Dependency Audit** | `pip-audit` + `npm audit` in CI | Every PR |
| **Penetration Testing** | Third-party engagement | Annually (Q4) |
| **Vulnerability Disclosure** | security.txt, responsible disclosure policy | Ongoing |
| **Secret Scanning** | Pre-commit hooks + CI check | Every commit |

### Monitoring — Four Golden Signals

| Signal | What We Measure | Alerting Threshold |
|--------|-----------------|-------------------|
| **Latency** | Request duration histograms per endpoint, transcription time per audio minute | p99 > 5x baseline |
| **Traffic** | Requests/sec, uploads/hour, active WebSocket connections | Spike > 3x rolling average |
| **Errors** | HTTP 5xx rate, task failure rate, unhandled exceptions | > 2% of requests in 5-min window |
| **Saturation** | CPU usage, memory usage, disk I/O, GPU VRAM, task queue depth | > 85% sustained for 10 min |

### Incident Management

| Process | Detail |
|---------|--------|
| **Severity Levels** | SEV1 (service down) -> SEV4 (cosmetic issue) |
| **Response Times** | SEV1: 15 min, SEV2: 1 hour, SEV3: 4 hours, SEV4: next sprint |
| **Postmortem** | Required for SEV1/SEV2. Blameless format. Published within 48 hours. |
| **On-Call Rotation** | Weekly rotation among senior engineers (when human team joins) |
| **Runbooks** | Written for every alerting rule, reviewed quarterly |

---

## 6. Frontend Strategy

### Current State

- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS
- **State:** Zustand (taskStore, uiStore)
- **Real-Time:** Custom `useSSE` and `useHealthStream` hooks
- **Routing:** Client-side SPA routing
- **Pages:** App (main), StatusPage, AboutPage, ContactPage, SecurityPage

### Component Library Standardization

| Phase | Action | Target |
|-------|--------|--------|
| Phase 1 | Audit existing components, extract shared patterns | Q2 2026 |
| Phase 2 | Build component library (buttons, inputs, modals, cards, alerts) | Q2 2026 |
| Phase 3 | Storybook documentation for all components | Q3 2026 |
| Phase 4 | Publish as internal package for plugin developers | Q4 2026 |

### Design System Tokens

```
COLORS
  Primary:    --color-primary-500: #3B82F6    (blue)
  Secondary:  --color-secondary-500: #8B5CF6  (purple)
  Success:    --color-success-500: #10B981     (green)
  Warning:    --color-warning-500: #F59E0B     (amber)
  Error:      --color-error-500: #EF4444       (red)
  Neutral:    --color-neutral-50 to --color-neutral-950

TYPOGRAPHY
  Font Family:  Inter (sans-serif), JetBrains Mono (mono)
  Scale:        text-xs (12px) -> text-4xl (36px)
  Line Height:  1.4 (body), 1.2 (headings)
  Font Weight:  400 (normal), 500 (medium), 600 (semibold), 700 (bold)

SPACING
  Base unit:    4px
  Scale:        0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64

MOTION
  Duration:     fast (150ms), normal (300ms), slow (500ms)
  Easing:       ease-out (entries), ease-in (exits), ease-in-out (transitions)
  Reduce motion: respect prefers-reduced-motion
```

### Accessibility Roadmap

| Level | Target | Key Requirements |
|-------|--------|-----------------|
| **WCAG 2.1 AA** | Q3 2026 | Color contrast 4.5:1, keyboard navigation, screen reader labels, focus indicators, alt text |
| **WCAG 2.1 AAA** | Q1 2027 | Enhanced contrast 7:1, sign language for video help, extended audio descriptions |
| **Section 508** | Q3 2026 | US federal accessibility standard (overlaps with AA) |
| **EN 301 549** | Q4 2026 | EU accessibility standard for ICT |

Specific actions:
- Audit with axe-core and Lighthouse (automated, every PR)
- Manual screen reader testing (NVDA, VoiceOver) quarterly
- Keyboard-only navigation testing for all features
- Focus management for modals, dropdowns, dynamic content
- ARIA labels for all interactive elements
- Skip-to-content links

### Internationalization (i18n) Plan

| Phase | Languages | Approach |
|-------|-----------|----------|
| Phase 1 (Q3 2026) | English, Spanish, French, German, Portuguese, Chinese (Simplified), Japanese, Korean, Arabic, Hindi | react-i18next with namespace-based JSON bundles |
| Phase 2 (Q4 2026) | Russian, Italian, Dutch, Polish, Turkish, Vietnamese, Thai, Indonesian, Malay, Swahili | Community translation via Crowdin |
| Phase 3 (2027) | 30+ languages, RTL support for Arabic/Hebrew/Persian/Urdu | Bidi text handling, mirrored layouts |

Implementation details:
- All user-facing strings extracted to translation keys
- ICU MessageFormat for plurals, dates, numbers
- Lazy-load language bundles (code splitting per locale)
- Language detection: browser preference -> user setting -> default (English)
- RTL layout via CSS logical properties (inline-start/end instead of left/right)

### Performance Budget

| Metric | Budget | Measurement Tool |
|--------|--------|-----------------|
| **Bundle Size (gzipped)** | < 200 KB initial, < 500 KB total | webpack-bundle-analyzer |
| **Largest Contentful Paint (LCP)** | < 2.5s | Lighthouse, Web Vitals |
| **First Input Delay (FID)** | < 100ms | Lighthouse, Web Vitals |
| **Cumulative Layout Shift (CLS)** | < 0.1 | Lighthouse, Web Vitals |
| **Time to Interactive (TTI)** | < 3.5s | Lighthouse |
| **JavaScript Execution** | < 300ms on mid-tier mobile | Chrome DevTools |

Enforcement: Lighthouse CI in PR checks, fail build if LCP > 3s or CLS > 0.15.

### Dark Mode Roadmap

| Phase | Scope | Target |
|-------|-------|--------|
| Phase 1 | System preference detection, CSS custom properties for all colors | Q2 2026 |
| Phase 2 | Manual toggle in settings, persist preference | Q2 2026 |
| Phase 3 | High contrast mode for accessibility | Q3 2026 |

---

## 7. Backend Strategy

### API Versioning Plan

```
Current:    /upload, /download/{id}, /events/{id}, ...
                    (unversioned, implicit v0)

Q2 2026:    /api/v1/upload, /api/v1/tasks/{id}, ...
                    (versioned, documented)
            /upload, /download/{id} ...
                    (legacy aliases, deprecated, sunset Q4 2026)

Q4 2026:    /api/v1/ (stable, maintained)
            /api/v2/ (if breaking changes needed)
            Legacy routes removed
```

Versioning rules:
- Minor additions (new fields, new endpoints) are non-breaking and stay in v1
- Breaking changes (renamed fields, removed endpoints, changed semantics) require v2
- Each version supported for minimum 12 months after successor ships
- Deprecation headers (`Sunset`, `Deprecation`) on legacy endpoints

### Database Scaling

```
Phase 1 (Current):
  App --> SQLite (dev) / PostgreSQL (prod)

Phase 2 (Q2 2026):
  App --> PgBouncer --> PostgreSQL Primary
                           |
                        Streaming Replication
                           |
                        PostgreSQL Read Replica
  Read traffic (analytics, history) --> Read Replica

Phase 3 (Q4 2026):
  App --> PgBouncer --> PostgreSQL Primary (writes)
                    --> PostgreSQL Read Replica 1 (reads, region US)
                    --> PostgreSQL Read Replica 2 (reads, region EU)
  Table partitioning on tasks table by created_at (monthly)
  Archive partitions older than 12 months to cold storage

Phase 4 (2027+):
  Evaluate Citus for horizontal sharding if single-primary becomes bottleneck
```

Connection pooling targets:
- PgBouncer in transaction mode
- 20 connections per API server, 10 per worker
- Connection lifetime: 30 minutes
- Idle timeout: 5 minutes

### File Storage Scaling

```
Phase 1 (Current):
  Local filesystem: uploads/ and outputs/ directories
  Cleanup: periodic task deletes files after FILE_RETENTION_HOURS

Phase 2 (Q2 2026):
  S3-compatible storage (AWS S3 or MinIO for self-hosted)
  Pre-signed URLs for direct upload/download (bypass API server)
  Lifecycle policies: move to Glacier after 30 days, delete after 90

Phase 3 (Q3 2026):
  CDN (CloudFront) in front of S3 for subtitle file delivery
  Edge caching for frequently accessed subtitle files
  Multi-region replication for low-latency global access

Phase 4 (Q4 2026):
  Resumable uploads via tus protocol for large files
  Client-side chunked upload with progress
```

### Queue System Evolution

```
Phase 1 (Current):
  asyncio.to_thread() + threading.Semaphore
  In-memory task state, Redis pub/sub for multi-server

Phase 2 (Q2 2026):
  Celery + Redis broker
  Priority queues: high (paid/API), normal (web), low (batch)
  Dead letter queue for failed tasks
  Task routing by capability (CPU-only, GPU-required)

Phase 3 (Q4 2026):
  Evaluate dedicated message broker (RabbitMQ) if Redis limitations arise
  Delayed/scheduled tasks (process at off-peak hours)
  Task chaining (transcribe -> translate -> embed as atomic pipeline)

Phase 4 (2027):
  Event-driven architecture with event store
  Saga pattern for multi-step workflows
```

### Model Serving

```
Phase 1 (Current):
  In-process model loading in worker thread
  Model cache: state.loaded_models[(model_size, device)]
  Thread-safe access via state.model_lock

Phase 2 (Q3 2026):
  Dedicated model server process
  gRPC interface for transcription requests
  Model warm-up pool: keep N models loaded based on usage patterns
  Graceful model eviction (LRU with min-retention)

Phase 3 (2027):
  Triton Inference Server for GPU model serving
  Dynamic batching of short audio segments
  Model versioning and A/B testing
  Auto-scaling model replicas based on queue depth
```

### Caching Strategy

| Layer | Technology | What | TTL | Invalidation |
|-------|-----------|------|-----|-------------|
| **Browser** | HTTP Cache-Control | Static assets (JS, CSS, images) | 1 year (hashed filenames) | Deploy (new hash) |
| **CDN** | CloudFront | Subtitle files, embedded videos | 24 hours | Explicit invalidation on re-process |
| **Application** | Redis | Rate limit counters, session data, API key validation | Varies | TTL expiry |
| **Model** | In-memory | Loaded Whisper models, translation models | Until eviction | LRU when memory pressure |
| **Database** | Redis | Frequent queries (task status, analytics aggregates) | 5 minutes | Write-through invalidation |
| **Translation** | Redis | Translated segment cache (hash of source text + lang pair) | 7 days | Manual flush |

---

## 8. Security Strategy

### Authentication Roadmap

```
Phase 1 (Current):
  API key authentication (optional, header-based)
  Session middleware for web UI
  Brute-force protection middleware

Phase 2 (Q2 2026):
  API key management UI (create, rotate, revoke, expiry)
  Per-key permissions (read-only, write, admin)
  Key usage tracking and rate limits

Phase 3 (Q3 2026):
  OAuth2 with PKCE for web UI
  Social login (Google, GitHub, Microsoft)
  JWT tokens with refresh rotation
  MFA support (TOTP, WebAuthn)

Phase 4 (Q4 2026):
  SAML 2.0 for enterprise SSO
  OIDC provider federation
  Service accounts for machine-to-machine auth
```

### Authorization — RBAC Model

| Role | Permissions |
|------|------------|
| **Viewer** | View transcription results, download files within their workspace |
| **Member** | All Viewer + upload files, create transcriptions, manage own tasks |
| **Team Lead** | All Member + manage team members, view team analytics, configure webhooks |
| **Admin** | All Team Lead + manage organization, billing, API keys, audit logs |
| **Super Admin** | All Admin + system configuration, model management, user impersonation |

Permission enforcement:
- Middleware-level role check on every request
- Resource-level ownership validation (users can only access their own tasks unless shared)
- API key permissions are a subset of the associated user's role

### Data Privacy

| Regulation | Requirements | Implementation | Target |
|------------|-------------|----------------|--------|
| **GDPR** | Right to access, rectify, erase, port data; DPO appointment; breach notification | Data export API, deletion pipeline, privacy policy, DPA template | Q3 2026 |
| **CCPA** | Right to know, delete, opt-out of sale; privacy notice | Opt-out mechanism, data inventory, privacy notice | Q3 2026 |
| **PIPEDA** | Consent, limiting collection, retention limits | Consent management, retention policies | Q4 2026 |

Data handling principles:
- Files deleted after `FILE_RETENTION_HOURS` (default 24h, configurable down to 1h)
- No transcription content stored permanently unless user opts in
- All data encrypted at rest (database, file storage)
- All data encrypted in transit (TLS 1.2+)
- No third-party data sharing without explicit consent
- Data residency options (EU, US) for enterprise customers

### File Handling Security

| Control | Current | Target |
|---------|---------|--------|
| **Virus Scanning** | ClamAV integration (quarantine service) | Mandatory scan before processing |
| **File Validation** | Extension + MIME + size + duration checks | Add magic byte verification |
| **Sandboxing** | ffmpeg runs as subprocess | Container isolation (seccomp profile) for ffmpeg/whisper |
| **Auto-Deletion** | Periodic cleanup task | Cryptographic deletion (overwrite) for sensitive content |
| **Upload Limits** | 2 GB max, 4h max duration | Per-user quotas, per-org quotas |

### Infrastructure Security

| Area | Implementation |
|------|---------------|
| **Network** | VPC with private subnets for workers/DB, public subnet for API only. Security groups: API -> worker (gRPC), API -> DB (5432), API -> Redis (6379). No direct worker/DB internet access. |
| **Secrets** | HashiCorp Vault or AWS Secrets Manager. No secrets in env vars or config files in production. Rotation: API keys 90 days, DB passwords 30 days, TLS certs auto-renew. |
| **TLS** | TLS 1.2+ everywhere. Let's Encrypt with auto-renewal. HSTS with preload. Certificate pinning for internal services. |
| **Container** | Non-root containers. Read-only filesystem (except temp dirs). No privileged mode. Resource limits (CPU, memory). |
| **Supply Chain** | Pin all dependency versions. Verify checksums. SBOM generation. Sigstore for container image signing. |

### Security Audit Schedule

| Type | Frequency | Scope |
|------|-----------|-------|
| Automated SAST (CodeQL, Semgrep) | Every PR | All application code |
| Dependency vulnerability scan | Every PR | Python + Node.js dependencies |
| Container image scan (Trivy) | Every build | Docker images |
| DAST (OWASP ZAP) | Weekly | All API endpoints |
| Manual code review (security focus) | Monthly | New features, auth changes |
| Penetration test (third-party) | Annually (Q4) | Full application + infrastructure |
| Red team exercise | Annually (Q2) | Social engineering + infrastructure |

---

## 9. Infrastructure Strategy

### Scaling Path

```
Phase 1 — Single Server (Current, Q1 2026)
+-------------------------------------------+
|              sub-main (8 CPU, 32 GB)       |
|  [FastAPI + Whisper + PostgreSQL + Redis]  |
|  3 concurrent tasks, ~1 task/min           |
+-------------------------------------------+

Phase 2 — Multi-Server (Q2 2026)
+------------------+     +------------------+
| sub-ctrl         |     | sub-data         |
| [Nginx LB]       |     | [PostgreSQL]     |
| [Monitoring]     |     | [Redis]          |
| [Ansible]        |     | [MinIO/S3]       |
+------------------+     +------------------+
        |                         |
   +----+----+              +-----+
   |         |              |
+--+---+ +---+--+     +----+-----+
|sub-  | |sub-  |     |sub-      |
|api-1 | |api-2 |     |worker-1  |
|[API] | |[API] |     |[Celery]  |
+------+ +------+     |[Whisper] |
                       +----------+

Phase 3 — Kubernetes (Q4 2026)
+--------------------------------------------------+
| Kubernetes Cluster                                |
|  +------------+  +------------+  +-------------+ |
|  | API Pods   |  | Worker Pods|  | Model Server| |
|  | (HPA: 2-8) |  | (HPA: 1-4)|  | (gRPC)      | |
|  +------------+  +------------+  +-------------+ |
|  +------------+  +------------+  +-------------+ |
|  | PostgreSQL |  | Redis      |  | MinIO/S3    | |
|  | (Operator) |  | (Sentinel) |  | (Operator)  | |
|  +------------+  +------------+  +-------------+ |
|  +------------+  +-------------+                  |
|  | Ingress    |  | Cert-Manager|                  |
|  | (Nginx)    |  | (Let's Enc.)|                  |
|  +------------+  +-------------+                  |
+--------------------------------------------------+

Phase 4 — Multi-Region (2027+)
  US-East Cluster <--replication--> EU-West Cluster
                        |
                  AP-Southeast Cluster
  Global load balancing via Cloudflare/Route53
  Data residency enforcement per region
```

### GPU Strategy

| Trigger | Action | Cost Consideration |
|---------|--------|-------------------|
| Queue depth > 5 for > 10 min | Add GPU worker | GPU instance ~4x CPU cost, but ~10x faster for large models |
| `large` model requests > 30% of traffic | Dedicated GPU worker for large model | Keep CPU workers for tiny/base/small |
| Real-time transcription feature launch | GPU required (latency constraint) | Reserved instances for predictable cost |
| Self-hosted enterprise customer | Document GPU requirements per throughput tier | Customer bears hardware cost |

GPU instance recommendations:
- Development/testing: NVIDIA T4 (16 GB VRAM) — runs all models
- Production (moderate): NVIDIA A10G (24 GB VRAM) — 2-3 concurrent large model tasks
- Production (high): NVIDIA A100 (40/80 GB) — batch processing, real-time features

### CDN Strategy

| Asset Type | CDN Behavior | Cache TTL |
|------------|-------------|-----------|
| Frontend JS/CSS/images | Immutable, hashed filenames | 1 year |
| API responses | No cache (dynamic) | 0 |
| Subtitle file downloads | Cache by task ID, invalidate on re-process | 24 hours |
| Embedded video downloads | No CDN (large files, S3 pre-signed URLs) | 0 |
| OpenAPI spec / docs | Cache with revalidation | 1 hour |

### Backup & Disaster Recovery

| Component | Backup Strategy | RPO | RTO |
|-----------|----------------|-----|-----|
| **PostgreSQL** | Continuous WAL archiving to S3, daily base backups | 5 minutes | 1 hour |
| **Redis** | AOF persistence, hourly RDB snapshots to S3 | 1 hour | 15 minutes |
| **File Storage (S3)** | Cross-region replication, versioning enabled | 0 (replicated) | 0 (auto-failover) |
| **Configuration** | Git-managed (Ansible, Helm charts) | 0 (in repo) | 30 minutes |
| **Whisper Models** | Cached from HuggingFace, re-downloadable | N/A | 10 minutes |

Disaster recovery procedure:
1. DNS failover to standby region (automated, < 5 min)
2. Promote read replica to primary (automated, < 15 min)
3. Restore Redis from latest snapshot (automated, < 15 min)
4. Scale API and worker pods in standby region (automated, < 5 min)
5. Verify health checks pass, resume traffic

### Geographic Distribution

| Region | Role | Target Latency (API) | Target |
|--------|------|---------------------|--------|
| US-East (Virginia) | Primary | < 50ms | Q2 2026 |
| EU-West (Frankfurt) | Secondary | < 50ms for EU users | Q4 2026 |
| AP-Southeast (Singapore) | Tertiary | < 100ms for APAC users | 2027 |

---

## 10. Team Scaling Plan

### Current: Team Sentinel (Q1 2026)

```
Atlas (Tech Lead)
  |
  +-- Aegis (Backend / Security)
  +-- Helix (Backend / Pipeline)
  +-- Prism (Frontend / UI)
  +-- Nexus (Infrastructure / DevOps)
  +-- Forge (Testing / Quality)
  +-- Cipher (Security / Compliance)
  +-- Beacon (Monitoring / Observability)
  +-- Relay (API / Integration)
  +-- Flux (Performance / Optimization)
  +-- Orbit (Frontend / Accessibility)
```

All positions currently filled by AI engineers. Full-stack capability across the team.

### Phase 2: Add Human Engineers (Q3 2026)

| Role | Responsibility | Hire By |
|------|---------------|---------|
| **Product Manager** | Feature prioritization, user research, competitive analysis, stakeholder communication | Q2 2026 |
| **UX Designer** | User research, wireframes, design system, usability testing | Q2 2026 |
| **Customer Support Lead** | Support channels, knowledge base, bug triage, user feedback loop | Q3 2026 |
| **DevOps Engineer** | Infrastructure automation, monitoring, on-call, cost optimization | Q2 2026 |
| **Security Engineer** | Threat modeling, pen testing, compliance, incident response | Q3 2026 |

### Phase 3: Multiple Squads (Q1 2027)

```
Engineering Organization
  |
  +-- Core Squad (Transcription, Translation, Pipeline)
  |     Lead: Helix
  |     4-6 engineers
  |
  +-- Platform Squad (API, Plugins, Marketplace)
  |     Lead: Relay
  |     4-6 engineers
  |
  +-- Enterprise Squad (Auth, Teams, Compliance, Self-Hosted)
  |     Lead: Cipher
  |     3-5 engineers
  |
  +-- Growth Squad (Onboarding, Analytics, Billing, i18n)
  |     Lead: Prism
  |     3-5 engineers
  |
  +-- Infrastructure Squad (DevOps, SRE, Performance)
        Lead: Nexus
        3-4 engineers
```

### Knowledge Management

| Artifact | Purpose | Owner | Location |
|----------|---------|-------|----------|
| **ADRs** (Architecture Decision Records) | Document significant technical decisions with context and trade-offs | Tech Lead | `docs/adr/` |
| **Runbooks** | Step-by-step procedures for operational tasks and incident response | SRE/DevOps | `docs/runbooks/` |
| **Onboarding Guide** | New engineer setup, codebase walkthrough, first PR guide | Tech Lead | `docs/onboarding/` |
| **API Documentation** | OpenAPI spec, usage examples, authentication guide | Platform Squad | Auto-generated + `docs/api/` |
| **CLAUDE.md** | AI assistant context for codebase conventions | Tech Lead | Repository root |
| **Sprint Retros** | Lessons learned, process improvements | Scrum Master | Internal wiki |

---

## 11. Maintenance & Operations

### Release Cadence

| Release Type | Frequency | Branch Strategy | Audience |
|-------------|-----------|----------------|----------|
| **Dev Build** | Every merged PR | `main` branch, CI/CD auto-deploy to staging | Internal/staging |
| **Weekly Release** | Every Tuesday | Tag `v{year}.{week}.{patch}` from `main` | Early adopters, self-hosted dev |
| **Monthly Stable** | First Tuesday of month | Tag `v{major}.{minor}.0`, release notes | Production, self-hosted stable |
| **Hotfix** | As needed | Branch from latest stable tag, cherry-pick fix | All production users |

Version numbering: CalVer for weekly (`2026.12.0`), SemVer for stable (`1.2.0`).

### Dependency Update Strategy

| Category | Tool | Frequency | Process |
|----------|------|-----------|---------|
| **Python patch updates** | Dependabot | Weekly PRs | Auto-merge if tests pass |
| **Node.js patch updates** | Dependabot | Weekly PRs | Auto-merge if tests pass |
| **Python minor updates** | Dependabot | Monthly PRs | Manual review, test in staging |
| **Major version upgrades** | Manual | Quarterly | Dedicated sprint capacity, migration plan, staged rollout |
| **Security patches** | Dependabot + pip-audit | Immediate | Fast-track PR, deploy within 24h |
| **Whisper model updates** | Manual | As released | Benchmark against current models before adoption |

### Technical Debt Management

**Allocation:** 20% of sprint capacity reserved for technical debt and refactoring.

| Category | Examples | Tracking |
|----------|---------|----------|
| **Code Quality** | Extract duplicated logic, improve naming, add type hints | GitHub issues labeled `tech-debt` |
| **Test Gaps** | Increase coverage for under-tested modules, add missing edge cases | Coverage reports, labeled issues |
| **Documentation** | Update outdated docstrings, add architecture diagrams | Quarterly doc review |
| **Performance** | Profile and optimize hot paths, reduce memory allocations | Performance regression tests |
| **Dependency Hygiene** | Remove unused deps, consolidate overlapping libraries | `pip-audit`, `npm ls` |

Quarterly tech debt review:
1. Measure debt indicators (test coverage, lint warnings, TODO count, dependency age)
2. Prioritize top 5 items by impact
3. Allocate to upcoming sprints
4. Track reduction over time

### Deprecation Policy

| Stage | Timeline | Action |
|-------|----------|--------|
| **Announcement** | T-6 months | Add `Deprecated` header to responses, update docs, blog post |
| **Warning** | T-3 months | Log warnings server-side when deprecated features are used |
| **Migration Guide** | T-3 months | Publish detailed migration guide with code examples |
| **Soft Removal** | T-0 | Return 410 Gone with migration link, keep endpoint alive for 30 days |
| **Hard Removal** | T+1 month | Remove code and endpoint entirely |

### Backward Compatibility Guarantees

**API Stability Contract:**
- Stable API versions (`/api/v1/`) will not have breaking changes for 12 months after successor release
- Fields will not be removed from responses (may be deprecated with null values)
- New required request parameters will not be added to existing endpoints
- HTTP status codes for existing scenarios will not change
- Error response format (`{"error": "...", "detail": "..."}`) is permanent

**File Format Contract:**
- SRT output will always conform to SubRip specification
- VTT output will always conform to WebVTT specification
- JSON output schema changes will be additive only (new fields, never removed fields)

---

## 12. Success Metrics

### Product Metrics

| Metric | Current | Q2 Target | Q4 Target | 2027 Target |
|--------|---------|-----------|-----------|-------------|
| **Monthly Active Users (MAU)** | <10 (beta) | 100 | 1,000 | 10,000 |
| **Transcription Completion Rate** | ~95% | 98% | 99% | 99.5% |
| **Average Processing Time** (1-min audio, base model) | ~15s | ~12s | ~8s | ~5s |
| **Translation Usage** (% of tasks) | ~5% | 15% | 25% | 35% |
| **Embedding Usage** (% of tasks) | ~3% | 10% | 20% | 25% |
| **API vs Web Usage** | 0% API | 20% API | 40% API | 50% API |
| **Returning Users** (30-day retention) | N/A | 30% | 45% | 60% |

### Quality Metrics

| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| **Test Pass Rate** | 100% (1,326 tests) | 100% (2,000+ tests) | 100% (3,500+ tests) |
| **Line Coverage** | ~70% | 80% | 85% |
| **Mean Time to Recovery (MTTR)** | N/A | < 1 hour | < 30 min |
| **Error Budget Consumption** | N/A | < 50% monthly | < 30% monthly |
| **Lint Warnings** | 0 | 0 | 0 |
| **Dependency Vulnerabilities (critical)** | 0 | 0 | 0 |

### Performance Metrics

| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| **p99 API Latency** (non-transcription) | ~100ms | < 200ms | < 150ms |
| **Throughput** (tasks/min, cluster) | ~1 | 10 | 25 |
| **Availability** | ~99% (single server) | 99.5% | 99.9% |
| **SSE Event Latency** | < 1s | < 500ms | < 200ms |
| **Frontend LCP** | ~3s | < 2.5s | < 2s |
| **Frontend Bundle Size** | ~300 KB | < 250 KB | < 200 KB |

### Security Metrics

| Metric | Target |
|--------|--------|
| **Days Since Last Critical Vulnerability** | > 90 (rolling) |
| **Mean Time to Patch** (critical) | < 24 hours |
| **Mean Time to Patch** (high) | < 7 days |
| **Mean Time to Patch** (medium/low) | < 30 days |
| **Security Test Coverage** | 100% of auth/authz paths |
| **Failed Login Rate** | < 5% (detect credential stuffing) |
| **Secrets in Codebase** | 0 (enforced by pre-commit) |

### Dashboard Summary

```
+------------------------------------------------------------------+
|                    PRODUCT HEALTH DASHBOARD                       |
+------------------------------------------------------------------+
|                                                                    |
|  USERS        QUALITY       PERFORMANCE      SECURITY             |
|  +---------+  +---------+   +-----------+    +---------+          |
|  | MAU     |  | Tests   |   | p99 API   |    | Vulns   |          |
|  | ___/10K |  | ____/OK |   | ___ms     |    | __/0    |          |
|  +---------+  +---------+   +-----------+    +---------+          |
|  | Compl.  |  | Cover.  |   | Avail.    |    | MTTP    |          |
|  | __.__%  |  | __.__%  |   | __.__% /  |    | __h     |          |
|  |         |  |         |   |  99.5% SLO|    |         |          |
|  +---------+  +---------+   +-----------+    +---------+          |
|  | Retain. |  | MTTR    |   | Tasks/min |    | Last    |          |
|  | __.__%  |  | __h/30m |   | ___/25    |    | Audit   |          |
|  +---------+  +---------+   +-----------+    +---------+          |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Appendix A: Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-01 | Use faster-whisper (CTranslate2) over OpenAI Whisper | 4x faster inference, lower memory, int8 quantization | Active |
| 2026-01 | Zustand over Redux for frontend state | Simpler API, less boilerplate, sufficient for current scope | Active |
| 2026-02 | PostgreSQL over MySQL for primary database | Better JSON support, async driver (asyncpg), richer extension ecosystem | Active |
| 2026-02 | Argos Translate over LibreTranslate API | Offline capability, no API dependency, self-hostable | Active |
| 2026-02 | SSE as primary real-time transport | Simpler than WebSocket for unidirectional events, auto-reconnect, HTTP/2 compatible | Active |
| 2026-03 | Single uvicorn worker per process | Whisper model not safe for multi-worker sharing; scale via multiple server instances | Active |
| 2026-03 | Sprint-based test organization | Matches development cadence, easy to trace features to tests | Active |

## Appendix B: Competitive Landscape

| Competitor | Strengths | Weaknesses | Our Differentiation |
|------------|-----------|------------|-------------------|
| **Whisper.cpp** | Fast, C++ native, mobile-ready | CLI only, no translation, no embedding | Full platform with UI, translation, embedding |
| **Subtitle Edit** | Feature-rich desktop app, many formats | Desktop only, no auto-transcription | Cloud-native, automatic transcription |
| **Kapwing** | Polished UI, collaboration | SaaS only, expensive, no self-hosting | Self-hostable, open architecture, offline capable |
| **Descript** | Excellent editor, multi-modal | Very expensive, SaaS only | Free/open, self-hosted option, API-first |
| **AssemblyAI** | High accuracy, great API | SaaS only, per-minute pricing | Self-hosted, no per-minute cost, offline |
| **Rev.com** | Human + AI hybrid | Expensive, slow turnaround | Instant results, self-hosted, free |

## Appendix C: Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Whisper model quality stagnates | Low | Medium | Monitor alternatives (Canary, Universal-1), modular model serving allows swapping |
| GPU costs make scaling uneconomical | Medium | High | CPU-first architecture, quantized models (int8), batch optimization |
| Security breach (file upload vector) | Medium | Critical | ClamAV scanning, sandboxed processing, input validation, penetration testing |
| Key dependency abandoned | Low | High | Pin versions, maintain forks of critical deps, SBOM tracking |
| Team scaling challenges | Medium | Medium | Strong documentation, ADRs, onboarding guides, knowledge transfer sessions |
| Regulatory changes (AI/copyright) | Medium | Medium | Offline-first architecture, self-hosted option, no data retention by default |

---

*This document is the north star for Team Sentinel. It will be reviewed and updated quarterly by the Tech Lead with input from all team members. Major strategic changes require team consensus.*

*Last reviewed: 2026-03-14 by Atlas, Tech Lead — Team Sentinel*

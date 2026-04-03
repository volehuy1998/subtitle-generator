# Roadmap

**Updated**: 2026-04-03 | **Sprints complete**: 110 (S1-S30 + L1-L80) | **Tests**: 3,667

## Current Priorities

1. **Distributed deployment** -- 5-server architecture (API nodes, worker nodes, data tier)
2. **API key hash migration** -- HMAC-SHA256 migration for existing SHA-256 records (production blocker)
3. **Static analysis** -- mypy/pyright integration in CI

## Completed Milestones

### Phase 1: Legacy Sprints (S1-S30)

30 sprints from foundation to production-grade platform. 1,130 tests.

| Milestone | Sprints | Key Deliverables |
|-----------|---------|-----------------|
| Foundation | S1-S2 | 99 languages, SRT/VTT output, task persistence, subtitle editor, batch upload |
| Architecture | S3-S5 | System capability detection, structured logging, Docker, CI/CD, API auth |
| Scale | S6-S7 | WebSocket, translation, monitoring dashboard, v1.0 release |
| Analytics | S8-S12 | Analytics service, Chart.js dashboard, user tracking, session resilience |
| API | S13-S15 | Queue management, OpenAPI tags, bulk export, share links |
| Security | S16, S24-S26 | Audit logging, brute force protection, rate limiting, CSP nonces, HSTS, SRI |
| Database | S18-S19 | PostgreSQL, SQLAlchemy async, Alembic, analytics migration |
| UX | S20-S21 | Full UI audit, auto-embed, embed SSE, user activity tracking |
| Observability | S22, S29 | Structured JSON logging, Prometheus metrics, alerting, health dashboard |
| Auth | S23 | User registration, JWT, API key management, RBAC |
| Scalability | S27-S28 | Memory cache, worker management, connection pooling, cursor pagination |
| Polish | S30 | Quick embed, stage timing, health SSE stream |

### Phase 2: Lumen (L1-L80)

80 sprints focused on stability, performance, and professional design. 2,537 additional tests.

| Milestone | Sprints | Key Deliverables |
|-----------|---------|-----------------|
| Foundation | L1-L8 | Lumen Docker profile, light theme design system, model readiness API, confirmation dialogs, liveness indicators, header redesign, embed tab redesign |
| Performance | L7-L60 | Model preloading optimization, pipeline performance, feature polish, design refinements |
| Hardening | L61-L80 | Pipeline refactored into 8 step functions with `_PipelineContext`, backend test gaps closed (audit HMAC, brute force, quarantine, S3, pub/sub, Redis, model manager), 372 frontend tests, 129 E2E Playwright tests |

**Current UI**: Lumen light theme (Inter font, preferences, theme toggle). Promoted to production 2026-03-17.

## Long-Term Plan

| Priority | Item | Status |
|----------|------|--------|
| 1 | UX: user confirmation before every process, lighter UI | Done |
| 2 | Performance: model preloading (60-120s down to <5s cached) | Done |
| 3 | Distributed workers: 5-server deployment plan | Not started |
| 4 | API key hash migration | Blocked (needs migration script) |
| 5 | Batch processing: upload multiple files, queue, bulk download | Planned |
| 6 | Collaboration: team workspaces, shared projects | Planned |
| 7 | Live streaming: real-time audio transcription via WebSocket | Planned |
| 8 | Plugin system: custom formats, translation engines | Planned |

## Infrastructure Plan

5-server CPU deployment (all 8C/24G/300GB):

| Server | Role |
|--------|------|
| sub-ctrl | Load balancer, deploy controller (Nginx, Ansible, Certbot, Flower) |
| sub-api-1, sub-api-2 | API nodes (FastAPI, `ROLE=web`) |
| sub-data | Data tier (PostgreSQL 16, Redis 7, MinIO) |
| sub-worker-1 | Transcription worker (Celery, `ROLE=worker`, `PRELOAD_MODEL=all`) |

---

<details>
<summary>Sprint History (S1-S30)</summary>

| Sprint | Goal | Tests Added | Total |
|--------|------|-------------|-------|
| S1 | Foundation Polish | 153 | 153 |
| S2 | User Experience | 22 | 175 |
| S3 | Architecture and Embedding | 29 | 204 |
| S4 | Advanced Transcription | 45 | 249 |
| S5 | Production Deployment | 35 | 284 |
| S6 | Scale and Monitor | 23 | 307 |
| S7 | Polish and Ship v1.0 | 36 | 343 |
| S8 | Analytics and Session Resilience | 43 | 386 |
| S9 | Analytics Dashboard | 31 | 417 |
| S10 | Frontend Modernization | 33 | 450 |
| S11 | Performance Optimization | 26 | 476 |
| S12 | Advanced Analytics | 28 | 504 |
| S13 | Queue and Batch Optimization | 21 | 525 |
| S14 | API v2 and Swagger UI | 26 | 551 |
| S15 | Notification and Export | 16 | 567 |
| S16 | Advanced Security and Audit | 35 | 602 |
| S17 | Scale and High Availability | 41 | 643 |
| S18 | Database Foundation | 51 | 694 |
| S19 | Analytics and Audit Migration | 38 | 732 |
| S20 | UI/UX Overhaul | 56 | 788 |
| S21 | User Activity Tracking | 41 | 829 |
| S22 | Structured Logging | 43 | 872 |
| S23 | Authentication and Access Control | 32 | 901 |
| S24 | Rate Limiting and DDoS Protection | 29 | 930 |
| S25 | Input Validation | 37 | 967 |
| S26 | Infrastructure Security | 31 | 998 |
| S27 | Scalability and Multi-Instance | 31 | 1,029 |
| S28 | Query Layer and Data Management | 27 | 1,056 |
| S29 | Monitoring and Observability | 30 | 1,086 |
| S30 | UX Flow and Live Status | 44 | 1,130 |

</details>

<details>
<summary>Lumen Sprint Summary (L1-L80)</summary>

- **L1**: Lumen Docker profile, 17 upload resilience tests
- **L2**: Light theme design system (Inter font, indigo primary, soft shadows)
- **L3**: Model readiness API (per-model status endpoint)
- **L4**: User confirmation dialog before transcription
- **L5**: Process liveness indicators (live/slow/no-response)
- **L6**: Component styling (removed all hardcoded dark colors)
- **L7**: Error message improvements (user-friendly text)
- **L8**: Full foundation completion (header redesign, cancel/embed dialogs, 388 tests added)
- **L9-L60**: Performance optimization, feature polish, design refinements
- **L61-L80**: Integration and hardening sprint block:
  - Pipeline refactored: `process_video()` split into 8 step functions with `_PipelineContext` dataclass
  - Backend test gaps closed: audit HMAC, brute force, quarantine, S3, pub/sub, Redis, model manager, slow query, session, rate limiting
  - Frontend: 372 tests across 27 files (stores, hooks, UI primitives, components, responsive, cross-browser, WCAG 2.1 AA)
  - E2E: 129 Playwright tests (upload flow, embed flow, SPA navigation)

Final total: 3,667 tests (3,295 backend + 372 frontend). CI green.

</details>

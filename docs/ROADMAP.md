# Subtitle Generator - Product Roadmap

## Team Roles

| Role | Responsibility | Focus Area |
|------|---------------|------------|
| **Product Owner** | Priorities, user stories, acceptance criteria | What to build and why |
| **Scrum Master** | Sprint planning, blockers, velocity tracking | Process and delivery |
| **Software Developer** | Implementation, code review, architecture | How to build it |
| **Tester** | Test strategy, automation, regression, edge cases | Quality assurance |

## Priority Order (PO directive)
1. **Architecture & Performance** - Optimal data processing, minimal user wait time
2. **Security** - Production-grade input validation and error handling
3. **Features** - User-facing functionality and UX improvements

---

## Sprint Plan (2-week cycles)

### Sprint 1: Foundation Polish [DONE]
**Goal**: Multi-language, output formats, error handling, task persistence
- 99 languages + auto-detect, VTT format, task persistence, error handling
- 153 tests, 0 regressions

### Sprint 2: User Experience [DONE]
**Goal**: In-browser editing, video preview, batch processing
- Subtitle editor, video preview, batch upload, responsive layout, task queue
- 175 tests, 0 regressions

### Sprint 3: Architecture & Performance + Subtitle Embedding [DONE]
**Goal**: System capability detection, structured logging, reliability, subtitle embedding

| ID | Story | Status |
|----|-------|--------|
| S3-1 | System capability detection at startup (CPU, GPU, RAM, OS, codecs) | DONE |
| S3-2 | Auto-tuning: OMP threads, max tasks, model selection based on hardware | DONE |
| S3-3 | Cross-platform support (Linux/Windows detection, Docker detection) | DONE |
| S3-4 | Structured JSON logging (app.jsonl for ELK/Grafana integration) | DONE |
| S3-5 | Request ID tracing across middleware, logs, and task events | DONE |
| S3-6 | Global exception handler (no unhandled crashes in production) | DONE |
| S3-7 | Health check (/health) and readiness probe (/ready) endpoints | DONE |
| S3-8 | Subtitle embedding: soft mux (fast, lossless) into MKV/MP4 | DONE |
| S3-9 | Subtitle hard burn with YouTube-style customizable styling | DONE |
| S3-10 | Style presets: default, youtube_white, youtube_yellow, cinema, large_bold, top | DONE |
| S3-11 | Lifespan-based startup/shutdown (replaced deprecated on_event) | DONE |
| S3-12 | Tests for all Sprint 3 features (29 tests) | DONE |

---

### Sprint 4: Advanced Transcription [DONE]
**Goal**: Speaker diarization, word-level timestamps, custom vocabulary

| ID | Story | Status |
|----|-------|--------|
| S4-1 | Speaker diarization (who is speaking) via pyannote (optional, graceful degradation) | DONE |
| S4-2 | Word-level timestamps for karaoke-style subtitles | DONE |
| S4-3 | Custom vocabulary/prompt for domain-specific terms | DONE |
| S4-4 | Subtitle line-breaking rules (max chars per line, CPS validation) | DONE |
| S4-5 | Auto-cleanup of old output/upload files (configurable 24h retention) | DONE |
| S4-6 | Tests for all Sprint 4 features (45 tests) | DONE |

---

### Sprint 5: Production Deployment [DONE]
**Goal**: Containerization, CI/CD, authentication, rate limiting

| ID | Story | Status |
|----|-------|--------|
| S5-1 | Dockerfile + docker-compose with GPU passthrough (NVIDIA Container Toolkit) | DONE |
| S5-2 | GitHub Actions CI/CD pipeline (lint, test, build, health check) | DONE |
| S5-3 | API key authentication for programmatic access (X-API-Key header) | DONE |
| S5-4 | Rate limiting via slowapi (in-memory, Redis upgrade deferred to S6) | DONE |
| S5-5 | Prometheus /metrics endpoint (zero-dependency text exposition) | DONE |
| S5-6 | Graceful shutdown with in-flight task draining (60s timeout) | DONE |
| S5-7 | Load testing and capacity planning script | DONE |

---

### Sprint 6: Scale & Monitor [DONE]
**Goal**: Task queue, metrics dashboard, subtitle translation

| ID | Story | Status |
|----|-------|--------|
| S6-1 | Celery + Redis task queue (deferred; in-memory queue sufficient for current scale) | DEFERRED |
| S6-2 | Built-in performance monitoring dashboard (/dashboard) | DONE |
| S6-3 | Subtitle translation (Whisper translate -> English; external API placeholder) | DONE |
| S6-4 | WebSocket real-time updates (ws/{task_id}, alongside existing SSE) | DONE |
| S6-5 | User session management (cookie-based) and task ownership | DONE |

---

### Sprint 7: Polish & Ship v1.0 [DONE]
**Goal**: Documentation, feedback, release

| ID | Story | Status |
|----|-------|--------|
| S7-1 | User feedback collection (1-5 star rating + comments, /feedback endpoint) | DONE |
| S7-2 | API documentation (OpenAPI v1.0.0, /docs, /redoc with full descriptions) | DONE |
| S7-3 | Architecture docs, CHANGELOG, ROADMAP maintained throughout | DONE |
| S7-4 | Release v1.0 with CHANGELOG.md | DONE |
| S7-5 | Performance benchmarks (loadtest.py, benchmark.py, endpoint latency tests) | DONE |

---

### Sprint 8: Analytics Foundation & Session Resilience [DONE]
**Goal**: Analytics data collection, time-series storage, session reconnection on page reload
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S8-1 | Analytics service: per-task timing, success/error counters, language distribution | DONE |
| S8-2 | Time-series data store (in-memory ring buffer, 24h retention, minute-resolution) | DONE |
| S8-3 | Analytics data collection hooks in pipeline (processing_time, file_size, model, language) | DONE |
| S8-4 | GET /analytics/summary endpoint (totals, rates, averages, top languages) | DONE |
| S8-5 | GET /analytics/timeseries endpoint (per-minute data points for charts) | DONE |
| S8-6 | Session reconnection: persist currentTaskId in sessionStorage, auto-reconnect SSE on reload | DONE |
| S8-7 | Wire metrics.inc() counters into upload and pipeline (uploads_total, completed, failed) | DONE |
| S8-8 | Frontend: add advanced options (word timestamps, diarize, translate) to upload form | DONE |
| S8-9 | Tests for Sprint 8 features (43 tests) | DONE |

---

### Sprint 9: Real-Time Analytics Dashboard with Charts [DONE]
**Goal**: Interactive charts page with processing trends, language distribution, error rates
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S9-1 | /analytics page: full-page dashboard with Chart.js (CDN) | DONE |
| S9-2 | Processing volume chart (tasks/hour over 24h) | DONE |
| S9-3 | Success/error rate chart (doughnut chart) | DONE |
| S9-4 | Language distribution chart (top 10 horizontal bar chart) | DONE |
| S9-5 | Average processing time chart (by model size) | DONE |
| S9-6 | Device distribution chart (doughnut) | DONE |
| S9-7 | Real-time KPI counters: uploads, completed, failed, success rate, avg time | DONE |
| S9-8 | Auto-refresh with configurable interval (5s/10s/30s/60s) + time range (1h/6h/12h/24h) | DONE |
| S9-9 | Tests for Sprint 9 features (31 tests) | DONE |

---

### Sprint 10: Frontend Modernization [DONE]
**Goal**: Wire all Sprint 4-7 backend features into the UI, subtitle embedding UI
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S10-1 | Upload form: word timestamps toggle, diarize toggle, translate checkbox | DONE |
| S10-2 | Upload form: custom vocabulary (initial_prompt) text field | DONE |
| S10-3 | Upload form: max line chars slider (20-80) | DONE |
| S10-4 | Download section: JSON format button (when word-level data available) | DONE |
| S10-5 | Subtitle embedding UI: soft mux / hard burn with style preset picker | DONE |
| S10-6 | Speaker labels in segment preview (colored per speaker) | DONE |
| S10-7 | Upload param wiring (all advanced options sent in FormData) | DONE |
| S10-8 | Tests for Sprint 10 features (33 tests) | DONE |

---

### Sprint 11: Performance Optimization [DONE]
**Goal**: Faster processing, smarter caching, resource efficiency
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S11-1 | Model preloading at startup (configurable via PRELOAD_MODEL env) | DONE |
| S11-2 | CSP updated for Chart.js CDN access | DONE |
| S11-3 | Response compression (GZip middleware, min 500 bytes) | DONE |
| S11-4 | Static asset caching headers (Cache-Control for /languages, /embed/presets, /system-info) | DONE |
| S11-5 | Compression config (ENABLE_COMPRESSION env var) | DONE |
| S11-6 | Performance config constants (STATIC_CACHE_MAX_AGE) | DONE |
| S11-7 | Benchmark regression tests (8 endpoint latency thresholds) | DONE |
| S11-8 | Tests for Sprint 11 features (26 tests) | DONE |

---

### Sprint 12: Advanced Analytics & User Tracking [DONE]
**Goal**: User behavior tracking, error analysis, data export
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S12-1 | Request tracking (IP, user-agent categorization: browser/mobile/api/bot) | DONE |
| S12-2 | User traffic stats (unique users, total requests, top users, agent distribution) | DONE |
| S12-3 | GET /analytics/users endpoint (unique users, agent breakdown, top IPs) | DONE |
| S12-4 | Error categorization by type (ValueError, RuntimeError, etc.) | DONE |
| S12-5 | Pipeline error category wiring (record_error_category on failure) | DONE |
| S12-6 | Export analytics as CSV/JSON (GET /analytics/export?format=csv|json) | DONE |
| S12-7 | Tests for Sprint 12 features (28 tests) | DONE |

---

### Sprint 13: Queue & Batch Pipeline Optimization [DONE]
**Goal**: Smarter queue management, retry, deduplication
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S13-1 | Queue position estimation (position + ETA for queued tasks) | DONE |
| S13-2 | GET /tasks/{id}/position endpoint | DONE |
| S13-3 | Tasks list includes queue position for queued tasks | DONE |
| S13-4 | POST /tasks/{id}/retry endpoint (retry failed/cancelled tasks) | DONE |
| S13-5 | Retry preserves original filename, language, session | DONE |
| S13-6 | GET /tasks/duplicates endpoint (filename + file_size matching) | DONE |
| S13-7 | Tests for Sprint 13 features (21 tests) | DONE |

---

### Sprint 14: API v2 & Swagger UI Enhancement [DONE]
**Goal**: Enhanced Swagger UI, OpenAPI tags, webhook support
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S14-1 | OpenAPI tags on all 15+ route modules (9 tag groups) | DONE |
| S14-2 | Enhanced Swagger UI (tryItOut, filter, docExpansion) | DONE |
| S14-3 | Rich markdown API description (features, formats, auth) | DONE |
| S14-4 | Webhook callbacks (POST/GET/DELETE /webhooks) | DONE |
| S14-5 | API version bump to v2.0.0 | DONE |
| S14-6 | Tag descriptions for organized documentation | DONE |
| S14-7 | Tests for Sprint 14 features (26 tests) | DONE |

---

### Sprint 15: Notification & Export System [DONE]
**Goal**: Bulk export, share links, download management
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S15-1 | Bulk export: download all completed subtitles as ZIP (GET /export/bulk) | DONE |
| S15-2 | ZIP format selection (SRT, VTT, JSON) | DONE |
| S15-3 | Share link creation (POST /share/{task_id}) | DONE |
| S15-4 | Share link download (GET /share/{id}/download, no auth required) | DONE |
| S15-5 | Share link info (GET /share/{id}/info) | DONE |
| S15-6 | Tests for Sprint 15 features (16 tests) | DONE |

---

### Sprint 16: Advanced Security & Audit [DONE]
**Goal**: Security hardening, audit logging, compliance
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S16-1 | Audit log: all admin actions, API key usage, auth events | DONE |
| S16-2 | CORS configuration (configurable allowed origins) | DONE |
| S16-3 | Request body size limiting middleware | DONE |
| S16-4 | Brute force protection (login/API key attempt throttling) | DONE |
| S16-5 | File quarantine: suspicious uploads moved to quarantine dir | DONE |
| S16-6 | Security audit endpoint: GET /security/audit (admin only) | DONE |
| S16-7 | Tests for Sprint 16 features (35 tests) | DONE |

---

### Sprint 17: Scale & High Availability [DONE]
**Goal**: Multi-worker support, external storage, HA preparation
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S17-1 | Task backend abstraction (InMemoryTaskBackend, pluggable for Redis) | DONE |
| S17-2 | Storage adapter abstraction (LocalStorageAdapter, pluggable for S3/MinIO) | DONE |
| S17-3 | Worker health monitoring (register, heartbeat, cleanup dead workers) | DONE |
| S17-4 | Load balancer health check compatibility (/health/live, /ready returns 503) | DONE |
| S17-5 | Scale info endpoint (GET /scale/info: workers, backends, storage, DB) | DONE |
| S17-6 | SQLite analytics persistence (analytics_db with daily aggregation) | DONE |
| S17-7 | Tests for Sprint 17 features (41 tests) | DONE |

---

### Sprint 18: Database Foundation [DONE]
**Goal**: PostgreSQL connection, SQLAlchemy models, Alembic migrations, core tables
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S18-1 | Add SQLAlchemy (async) + asyncpg + Alembic to dependencies | DONE |
| S18-2 | Database config: DATABASE_URL env var, connection pool settings | DONE |
| S18-3 | SQLAlchemy Base, async engine, async session factory (app/db/) | DONE |
| S18-4 | Alembic init with async driver, initial migration | DONE |
| S18-5 | tasks table: id, status, filename, language, model, device, progress, segments (JSONB), timestamps, session_id | DONE |
| S18-6 | sessions table: id, created_at, last_seen, ip, user_agent | DONE |
| S18-7 | Migrate InMemoryTaskBackend → DatabaseTaskBackend (implement same interface) | DONE |
| S18-8 | Lifespan: init DB pool on startup, dispose on shutdown | DONE |
| S18-9 | Pipeline and upload persist tasks to DB, fallback to JSON | DONE |
| S18-10 | Tests for Sprint 18 (51 tests, SQLite async) | DONE |

---

### Sprint 19: Analytics & Audit Migration [DONE]
**Goal**: Move analytics, audit logs, and feedback from memory/JSONL to PostgreSQL
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S19-1 | analytics_events table: id, timestamp, event_type, data (JSON) | DONE |
| S19-2 | analytics_daily table: date PK, uploads, completed, failed, cancelled, processing_sec, avg_file_size | DONE |
| S19-3 | analytics_timeseries table: minute-resolution, replaces in-memory ring buffer | DONE |
| S19-4 | audit_log table: id, timestamp, event_type, ip, path, details (JSON) — replaces audit.jsonl | DONE |
| S19-5 | feedback table: id, task_id, rating, comment, created_at — replaces feedback.jsonl | DONE |
| S19-6 | analytics_pg.py: async PG service with write-through from analytics.py (in-memory cache kept) | DONE |
| S19-7 | audit_pg.py: async PG audit persistence, fire-and-forget from audit.py | DONE |
| S19-8 | Analytics routes: /analytics/timeseries reads from DB, /analytics/daily new endpoint, export includes daily | DONE |
| S19-9 | Feedback route: DB-primary writes with JSONL fallback, summary from SQL aggregation | DONE |
| S19-10 | Alembic migration 002, load_analytics_from_db() at startup, tests (38 tests) | DONE |

---

### Sprint 20: UI/UX Overhaul & Functional Stability [DONE]
**Goal**: Fix all broken/non-functional UI features, clean embed interface, polished user flow
**Theme**: Every button works. No dead features on the interface.
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S20-1 | Full UI audit: verified all buttons, fixed dead code, fixed resetUI() completeness | DONE |
| S20-2 | Auto-embed: upload param -> pipeline keeps video -> embeds after transcription (no re-upload) | DONE |
| S20-3 | Embed SSE events: embed_progress, embed_done, embed_error for real-time embed status | DONE |
| S20-4 | Video preview fix: CSP media-src blob:, subtitle track recreation, loadVideoFile() | DONE |
| S20-5 | Embed presets: EMBED_PRESETS JS object, applyPreset() applies to form controls + live preview | DONE |
| S20-6 | Embed fallback: startEmbed() uses preview video file if embed video not selected | DONE |
| S20-7 | Mobile responsive: embed grid, tabs, style grid, preview text all stack on small screens | DONE |
| S20-8 | Close buttons: video preview and embed panel both have close/dismiss buttons | DONE |
| S20-9 | Reset completeness: resetUI() clears embed panel, video player, subtitle track, embed mode | DONE |
| S20-10 | Code cleanup: removed dead origAddSegment, fixed misleading editor save message | DONE |
| S20-11 | Hex-to-ASS color conversion in embed route (#RRGGBB -> &HBBGGRR) | DONE |
| S20-12 | Tests for Sprint 20 (56 tests: UI elements, embed panel, video preview, auto-embed, SSE, responsive) | DONE |

---

### Sprint 21: User Activity Tracking & Analytics [DONE]
**Goal**: Track every user interaction for UI/UX improvement and bug detection
**Theme**: Know exactly what users do, where they get stuck, what breaks
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S21-1 | Frontend event tracker: click tracking, page views, feature usage (JS -> /track endpoint) | DONE |
| S21-2 | ui_events table: id, session_id, timestamp, event_type, target, extra (JSON) | DONE |
| S21-3 | Track key flows: upload start/complete/fail, embed start/complete/fail, download clicks | DONE |
| S21-4 | Track UI interactions: button clicks, panel opens, option changes, errors shown | DONE |
| S21-5 | Error tracking: capture JS errors (window.onerror), unhandled promise rejections, send to backend | DONE |
| S21-6 | Funnel analysis endpoint: GET /analytics/funnel (upload → transcribe → download → embed conversion) | DONE |
| S21-7 | Feature usage endpoint: GET /analytics/features — most-used features by click count | DONE |
| S21-8 | Session activity endpoint: GET /analytics/session/{id} — timeline per session | DONE |
| S21-9 | Batch tracking: POST /track/batch — buffered client-side, bulk insert server-side | DONE |
| S21-10 | Alembic migration 003: ui_events table | DONE |
| S21-11 | Tests for Sprint 21 (41 tests: model, service, endpoints, frontend tracker, migration) | DONE |

---

### Sprint 22: Structured Logging & Log Pipeline [DONE]
**Goal**: Standardized log format, correlation IDs, log levels, ready for ELK/Loki/Datadog
**Theme**: Every log line is parseable, traceable, and exportable
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S22-1 | Structured JSON log format: {timestamp, level, logger, message, request_id, task_id, extra} | DONE |
| S22-2 | Correlation IDs: X-Request-ID flows through all layers (middleware -> route -> service -> pipeline) | DONE |
| S22-3 | Log levels standardization: DEBUG (internal detail), INFO (operations), WARN (recoverable), ERROR (failures) | DONE |
| S22-4 | Task lifecycle logging: consistent events at each pipeline stage with timing and context | DONE |
| S22-5 | HTTP access log: structured format (method, path, status, duration_ms, ip, user_agent, request_id) | DONE |
| S22-6 | Security event logging: auth, rate-limit, quarantine, brute-force — all in structured format | DONE |
| S22-7 | Log output targets: stdout (Docker), file rotation (standalone), syslog (enterprise) — configurable | DONE |
| S22-8 | Log export endpoint: GET /admin/logs?level=ERROR&since=1h&task_id=xxx (admin only, paginated) | DONE |
| S22-9 | Log push integration: configurable webhook/syslog forwarder for third-party analysis | DONE |
| S22-10 | Log sanitization: redact sensitive data (API keys, IPs in certain contexts, file paths) in logs | DONE |
| S22-11 | Tests for Sprint 22 (log format, correlation ID propagation, output targets, export) | DONE |

---

### Sprint 23: Authentication & Access Control [DONE]
**Goal**: User identity, API key management, session security, role-based access
**Theme**: No unauthorized access to data or admin functions
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S23-1 | users table: id, username, password_hash, role (admin/user), created_at, is_active | DONE |
| S23-2 | api_keys table: id, key_hash (SHA-256), label, owner_id FK, created_at, last_used, expires_at, is_active | DONE |
| S23-3 | Auth endpoints: POST /auth/register, POST /auth/login, POST /auth/logout (JWT access + refresh tokens) | DONE |
| S23-4 | JWT token management: access tokens, refresh tokens, decode/verify | DONE |
| S23-5 | API key management: create, list, revoke — authenticated users, header-only transport | DONE |
| S23-6 | Role-based guards: _require_auth, _require_admin helpers for endpoint protection | DONE |
| S23-7 | GET /auth/me: current user info from JWT | DONE |
| S23-8 | POST /auth/refresh: refresh access token using refresh token | DONE |
| S23-9 | Alembic migration 004: users and api_keys tables | DONE |
| S23-10 | Tests for Sprint 23 (32 tests: auth flows, JWT, API keys, RBAC, migration) | DONE |

---

### Sprint 24: Rate Limiting & DDoS Protection [DONE]
**Goal**: Enforce rate limits, per-user quotas, brute force persistence
**Theme**: System stays responsive under attack and high load
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S24-1 | Sliding window rate limiter: per-IP buckets with configurable limits | DONE |
| S24-2 | Per-user/API-key rate limits: separate upload vs API rate limits | DONE |
| S24-3 | Brute force persistence: brute_force_events table, survives restart | DONE |
| S24-4 | Retry-After headers on 429 responses, X-RateLimit-* headers on all responses | DONE |
| S24-5 | IP allowlist/blocklist: admin-managed, bypass or instant reject | DONE |
| S24-6 | Concurrent task quota per user: max N tasks per user (configurable via PER_USER_MAX_TASKS) | DONE |
| S24-7 | Rate limit middleware: RateLimitMiddleware with exempt paths | DONE |
| S24-8 | Alembic migration 005: brute_force_events and ip_lists tables | DONE |
| S24-9 | Tests for Sprint 24 (29 tests: rate limiting, IP lists, quotas, middleware, models) | DONE |

---

### Sprint 25: Input Validation & Secure Processing [DONE]
**Goal**: Strict validation at every boundary, injection prevention
**Theme**: No user input reaches internal systems without validation
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S25-1 | Centralized safe_path(): .resolve() + prefix check on ALL file ops | DONE |
| S25-2 | File integrity: SHA-256 checksums on uploads, compute/verify functions | DONE |
| S25-3 | FFmpeg filter injection hardening: allowlisted values only, validate_ffmpeg_filter_value() | DONE |
| S25-4 | Subtitle content sanitization: strip control chars, remove script tags, validate timing | DONE |
| S25-5 | Error message sanitization: redact paths, DB URLs, tracebacks from client responses | DONE |
| S25-6 | Path traversal prevention: safe_path() with allowed_dir parameter | DONE |
| S25-7 | Pydantic validation on all routes: tested upload, track, feedback, auth endpoints | DONE |
| S25-8 | Tests for Sprint 25 (37 tests: traversal, checksums, XSS, injection, timing, sanitization) | DONE |

---

### Sprint 26: Infrastructure Security & Hardening [DONE]
**Goal**: HTTPS, CSP nonces, CORS lockdown, secrets management
**Theme**: Production-grade security posture
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S26-1 | HSTS configuration: configurable max-age, includeSubDomains, preload via env vars | DONE |
| S26-2 | CSP nonce generation: cryptographically random per-request nonces | DONE |
| S26-3 | CORS lockdown: get_safe_cors_origins() with default-deny mode, origin validation | DONE |
| S26-4 | SRI hashes: compute_sri_hash() for CDN resource integrity verification | DONE |
| S26-5 | Audit log integrity: HMAC-signed entries, create_signed_audit_entry(), verify_audit_entry() | DONE |
| S26-6 | Security headers validated: X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy | DONE |
| S26-7 | Config variables: HSTS_ENABLED, HTTPS_REDIRECT, CSP_NONCE_ENABLED, CORS_DEFAULT_DENY | DONE |
| S26-8 | Tests for Sprint 26 (31 tests: nonces, SRI, HSTS, CORS, audit HMAC, headers, Docker) | DONE |

---

### Sprint 27: Scalability & Multi-Instance [DONE]
**Goal**: Redis backend, connection pooling, horizontal scaling readiness
**Theme**: System handles 100+ concurrent users across multiple instances
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S27-1 | MemoryCache: Redis-compatible in-memory backend with TTL, incr, pattern keys | DONE |
| S27-2 | Worker management: register, heartbeat, dead worker cleanup, get_workers() | DONE |
| S27-3 | Connection pool config: get_pool_config() from env vars (pool_size, max_overflow, recycle) | DONE |
| S27-4 | InMemoryTaskQueue: FIFO queue with max_size, enqueue/dequeue/peek/clear | DONE |
| S27-5 | Redis config: REDIS_URL env var, REDIS_ENABLED flag, graceful fallback to memory | DONE |
| S27-6 | Scale info: get_scale_info() combining worker, cache, queue, pool status | DONE |
| S27-7 | Tests for Sprint 27 (31 tests: cache, workers, pool, queue, scale info, Redis config) | DONE |

---

### Sprint 28: Query Layer & Data Management [DONE]
**Goal**: Search, pagination, retention, data export
**Theme**: Efficient data access at scale
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S28-1 | Task search & filtering: by status, language, filename, date range, session_id | DONE |
| S28-2 | Cursor-based paginated task list: GET /tasks/search?cursor=xxx&limit=20 | DONE |
| S28-3 | Analytics rollup: daily/weekly/monthly SQL aggregations via GET /analytics/rollup | DONE |
| S28-4 | Data retention: POST /admin/retention — auto-purge old tasks, events, audit logs | DONE |
| S28-5 | Bulk export: GET /admin/export/tasks — CSV and JSON formats with filters | DONE |
| S28-6 | DB health: GET /health/db — pool check, query latency measurement | DONE |
| S28-7 | Tests for Sprint 28 (27 tests: search, pagination, rollup, retention, export, DB health) | DONE |

---

### Sprint 29: Monitoring & Observability [DONE]
**Goal**: Prometheus metrics, alerting, health dashboards, performance visibility
**Theme**: Full operational visibility — know before users complain
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S29-1 | Prometheus metrics endpoint: /metrics with task counts, file counts, uptime, system stats | DONE |
| S29-2 | Business metrics: uploads/hour, success rate, avg/p95 processing time, embed usage | DONE |
| S29-3 | Alerting rules: configurable thresholds (error rate, queue depth, disk free, latency, memory) | DONE |
| S29-4 | Health dashboard: GET /monitoring/dashboard — Grafana-compatible JSON aggregation | DONE |
| S29-5 | Performance profiling: start_timer/record_timing per-stage breakdown (upload, probe, transcribe, embed) | DONE |
| S29-6 | Monitoring endpoints: /monitoring/metrics, /alerts, /thresholds, /performance, /dashboard | DONE |
| S29-7 | Tests for Sprint 29 (30 tests: metrics, alerts, profiling, dashboard, Prometheus format) | DONE |

---

### Sprint 30: UX Flow, Stage Timing & Live Status [DONE]
**Goal**: Seamless post-transcription embed, per-stage duration display, continuous health signal
**Theme**: Users see exactly what's happening and never need to re-upload
**Completed**: 2026-03-11

| ID | Story | Status |
|----|-------|--------|
| S30-1 | Quick embed: POST /embed/{task_id}/quick using preserved video (no re-upload) | DONE |
| S30-2 | Pipeline preserves video file for deferred embed after transcription | DONE |
| S30-3 | Inline embed card in results area: mode + preset + "Embed Now" button | DONE |
| S30-4 | Live step timing: real-time elapsed counter per pipeline stage | DONE |
| S30-5 | Step timing summary: breakdown table shown after completion | DONE |
| S30-6 | Health SSE stream: GET /health/stream pushes status every 5s | DONE |
| S30-7 | Health indicator: load bar, offline state, CPU/memory gauges in panel | DONE |
| S30-8 | Enriched /api/status: cpu_percent, memory_percent, max_tasks fields | DONE |
| S30-9 | Health panel: DB latency badges, mini-bar gauges, task load visualization | DONE |
| S30-10 | Tests for Sprint 30 (44 tests: timing UI, health SSE, quick embed, video preservation) | DONE |

---

## Sprint History

| Sprint | Goal | Completed | Tests Added | Total Tests |
|--------|------|-----------|-------------|-------------|
| Sprint 1 | Foundation Polish | 2026-02-15 | 153 | 153 |
| Sprint 2 | User Experience | 2026-02-22 | 22 | 175 |
| Sprint 3 | Architecture & Embedding | 2026-03-01 | 29 | 204 |
| Sprint 4 | Advanced Transcription | 2026-03-05 | 45 | 249 |
| Sprint 5 | Production Deployment | 2026-03-07 | 35 | 284 |
| Sprint 6 | Scale & Monitor | 2026-03-09 | 23 | 307 |
| Sprint 7 | Polish & Ship v1.0 | 2026-03-11 | 36 | 343 |
| Sprint 8 | Analytics & Session Resilience | 2026-03-11 | 43 | 386 |
| Sprint 9 | Analytics Dashboard with Charts | 2026-03-11 | 31 | 417 |
| Sprint 10 | Frontend Modernization | 2026-03-11 | 33 | 450 |
| Sprint 11 | Performance Optimization | 2026-03-11 | 26 | 476 |
| Sprint 12 | Advanced Analytics & User Tracking | 2026-03-11 | 28 | 504 |
| Sprint 13 | Queue & Batch Optimization | 2026-03-11 | 21 | 525 |
| Sprint 14 | API v2 & Swagger UI | 2026-03-11 | 26 | 551 |
| Sprint 15 | Notification & Export | 2026-03-11 | 16 | 567 |
| Sprint 16 | Advanced Security & Audit | 2026-03-11 | 35 | 602 |
| Sprint 17 | Scale & High Availability | 2026-03-11 | 41 | 643 |
| Sprint 18 | Database Foundation | 2026-03-11 | 51 | 694 |
| Sprint 19 | Analytics & Audit Migration | 2026-03-11 | 38 | 732 |
| Sprint 20 | UI/UX Overhaul & Stability | 2026-03-11 | 56 | 788 |
| Sprint 21 | User Activity Tracking | 2026-03-11 | 41 | 829 |
| Sprint 22 | Structured Logging & Log Pipeline | 2026-03-11 | 43 | 872 |
| Sprint 23 | Authentication & Access Control | 2026-03-11 | 32 | 901 |
| Sprint 24 | Rate Limiting & DDoS Protection | 2026-03-11 | 29 | 930 |
| Sprint 25 | Input Validation & Secure Processing | 2026-03-11 | 37 | 967 |
| Sprint 26 | Infrastructure Security & Hardening | 2026-03-11 | 31 | 998 |
| Sprint 27 | Scalability & Multi-Instance | 2026-03-11 | 31 | 1029 |
| Sprint 28 | Query Layer & Data Management | 2026-03-11 | 27 | 1056 |
| Sprint 29 | Monitoring & Observability | 2026-03-11 | 30 | 1086 |
| Sprint 30 | UX Flow, Stage Timing & Live Status | 2026-03-11 | 44 | 1130 |

## Current Sprint Progress

**All 11 sprints (S20-S30) COMPLETE** — 2026-03-11

### Sprint Plan (S20-S30) — ALL DONE
| Sprint | Theme | Status |
|--------|-------|--------|
| **S20** | UI/UX Overhaul & Stability | ✅ DONE |
| **S21** | User Activity Tracking | ✅ DONE |
| **S22** | Structured Logging & Log Pipeline | ✅ DONE |
| **S23** | Authentication & Access Control | ✅ DONE |
| **S24** | Rate Limiting & DDoS Protection | ✅ DONE |
| **S25** | Input Validation & Secure Processing | ✅ DONE |
| **S26** | Infrastructure Security & Hardening | ✅ DONE |
| **S27** | Scalability & Multi-Instance | ✅ DONE |
| **S28** | Query Layer & Data Management | ✅ DONE |
| **S29** | Monitoring & Observability | ✅ DONE |
| **S30** | UX Flow, Stage Timing & Live Status | ✅ DONE |

### Cumulative Progress
- [x] Sprint 1: Foundation (multi-language, VTT, persistence, error handling)
- [x] Sprint 2: UX (editor, video preview, batch, responsive, task queue)
- [x] Sprint 3: Architecture (system caps, auto-tune, JSON logging, health, embed)
- [x] Sprint 4: Advanced Transcription (diarization, word timestamps, vocabulary, line-breaking, cleanup)
- [x] Sprint 5: Production Deployment (Docker, CI/CD, auth, metrics, graceful shutdown)
- [x] Sprint 6: Scale & Monitor (dashboard, translation, WebSocket, sessions)
- [x] Sprint 7: Polish & Ship v1.0 (feedback, docs, changelog, benchmarks)
- [x] Sprint 8: Analytics Foundation & Session Resilience (43 tests)
- [x] Sprint 9: Real-Time Analytics Dashboard with Charts (31 tests)
- [x] Sprint 10: Frontend Modernization (33 tests)
- [x] Sprint 11: Performance Optimization (26 tests)
- [x] Sprint 12: Advanced Analytics & User Tracking (28 tests)
- [x] Sprint 13: Queue & Batch Pipeline Optimization (21 tests)
- [x] Sprint 14: API v2 & Swagger UI Enhancement (26 tests)
- [x] Sprint 15: Notification & Export System (16 tests)
- [x] Sprint 16: Advanced Security & Audit (35 tests)
- [x] Sprint 17: Scale & High Availability (41 tests)
- [x] Sprint 18: Database Foundation (PostgreSQL + SQLAlchemy + Alembic, 51 tests)
- [x] Sprint 19: Analytics & Audit Migration (PG analytics/audit/feedback, 38 tests)
- [x] Sprint 20: UI/UX Overhaul & Functional Stability (56 tests)
- [x] Sprint 21: User Activity Tracking & Analytics (41 tests)
- [x] Sprint 22: Structured Logging & Log Pipeline (43 tests)
- [x] Sprint 23: Authentication & Access Control (32 tests)
- [x] Sprint 24: Rate Limiting & DDoS Protection (29 tests)
- [x] Sprint 25: Input Validation & Secure Processing (37 tests)
- [x] Sprint 26: Infrastructure Security & Hardening (31 tests)
- [x] Sprint 27: Scalability & Multi-Instance (31 tests)
- [x] Sprint 28: Query Layer & Data Management (27 tests)
- [x] Sprint 29: Monitoring & Observability (30 tests)
- [x] Sprint 30: UX Flow, Stage Timing & Live Status (44 tests)
- **1130 total tests passing, 0 regressions**

---

## Phase Lumen (L1-L80) — Active Development Phase

> **Full spec**: `docs/lumen/PHASE_LUMEN.md` · **Status**: 80 sprints complete · **Tests**: 3,667 total

Phase Lumen follows the legacy 30 sprints with a focus on stability, performance, and professional design:
- **L1-L6**: Foundation, design system (light theme), model readiness API, confirmation dialogs, liveness indicators, component styling
- **L7-L60**: Performance optimization, feature polish, design refinements
- **L61-L80**: Integration + hardening — pipeline refactored (8 step functions), backend test gaps closed, 372 frontend tests, 129 E2E Playwright tests

**Current UI**: Lumen light theme (Inter font, preferences, theme toggle) — promoted to production on 2026-03-17.

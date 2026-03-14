# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0](https://github.com/volehuy1998/subtitle-generator/compare/v2.1.0...v2.2.0) (2026-03-14)


### Features

* **ui:** Enterprise Slate dark theme — corporate redesign ([#45](https://github.com/volehuy1998/subtitle-generator/issues/45)) ([070bcff](https://github.com/volehuy1998/subtitle-generator/commit/070bcffb1e89a933ae3ed7ad9a4e8929d0541518)), closes [#44](https://github.com/volehuy1998/subtitle-generator/issues/44)


### Bug Fixes

* **deploy:** add complete .env.example and document Docker preview subdomain ([#49](https://github.com/volehuy1998/subtitle-generator/issues/49)) ([ca5abe3](https://github.com/volehuy1998/subtitle-generator/commit/ca5abe31950d1f5264fc802c5b062fef2f8a2ab4)), closes [#47](https://github.com/volehuy1998/subtitle-generator/issues/47)
* **deploy:** fix deploy.sh Unicode bug, add newui profile, pin PROD_IMAGE_TAG, update docs ([#73](https://github.com/volehuy1998/subtitle-generator/issues/73)) ([627429e](https://github.com/volehuy1998/subtitle-generator/commit/627429e087ecfa9b1359eca5dc30eedda2f1a20c))
* **middleware:** add Secure flag to session cookie and explicit CORS allow_headers ([#74](https://github.com/volehuy1998/subtitle-generator/issues/74)) ([92ca304](https://github.com/volehuy1998/subtitle-generator/commit/92ca3044b465b586d9e36aa20b0da0c5157872cf))
* **security:** allow Google Fonts in CSP so brand fonts load correctly ([#57](https://github.com/volehuy1998/subtitle-generator/issues/57)) ([bbd0a92](https://github.com/volehuy1998/subtitle-generator/commit/bbd0a92e6c1c6525ec15b312a662f15adb019af7))
* **security:** stop post-commit hook updating last_security_commit on every commit ([#61](https://github.com/volehuy1998/subtitle-generator/issues/61)) ([65a4b51](https://github.com/volehuy1998/subtitle-generator/commit/65a4b51bc6cdb976c99191c7a5e4639eee3d6377))
* **status:** remove test incidents from public status page ([#58](https://github.com/volehuy1998/subtitle-generator/issues/58)) ([2472d9a](https://github.com/volehuy1998/subtitle-generator/commit/2472d9a9507becdbac4c65a0f3cfa2376e73a164))
* **ui:** fix 5 ESLint errors and remove || true mask from CI ([#65](https://github.com/volehuy1998/subtitle-generator/issues/65)) ([54dbb77](https://github.com/volehuy1998/subtitle-generator/commit/54dbb7790c26d9be9bf4cfe4361949df6c364078))
* **ui:** hide GPU/CPU hardware badge on non-app pages ([#59](https://github.com/volehuy1998/subtitle-generator/issues/59)) ([f06d051](https://github.com/volehuy1998/subtitle-generator/commit/f06d0513854b797e4d40e94e70e924bb04351afa)), closes [#54](https://github.com/volehuy1998/subtitle-generator/issues/54)
* **ui:** update About page tech stack — React 18 → React 19, Vite → Vite 6 ([#60](https://github.com/volehuy1998/subtitle-generator/issues/60)) ([e74eecb](https://github.com/volehuy1998/subtitle-generator/commit/e74eecbea961d76ed2ca010a22318b0604487d53))


### Documentation

* **config:** fix .sentinel restore path and explain naming pattern ([#43](https://github.com/volehuy1998/subtitle-generator/issues/43)) ([c280af3](https://github.com/volehuy1998/subtitle-generator/commit/c280af30b97db4ede77900b6603a67b74f51bf60))
* **ui:** establish subdomain-first design review policy ([#50](https://github.com/volehuy1998/subtitle-generator/issues/50)) ([923dcec](https://github.com/volehuy1998/subtitle-generator/commit/923dcec782dbdb99d68c8beabc1f592af9c04a6a)), closes [#48](https://github.com/volehuy1998/subtitle-generator/issues/48)

## [Unreleased] - v2.1.0

### Added
- Multi-model preload support: `PRELOAD_MODEL` now accepts comma-separated values (e.g., `tiny,base,large`) or `all` to load every model
- Background model preloading: models load after server starts accepting connections so the UI is available immediately
- Model preload status API (`/api/model-status`) for frontend display of loading progress
- Model preload status included in `/system-info` and `/api/system-status` endpoints
- `MAX_CONCURRENT_TASKS` environment variable for explicit override of auto-tuned concurrency
- Upload progress percentage display in the transcription form
- Transcription detail panel with richer progress information
- Model selector redesign with card-based layout and research-accurate specs
- Conventional Commits hook and pre-commit hook for git standards
- PR template and CONTRIBUTING.md with contribution guidelines
- CI frontend testing: GitHub Actions now runs Vitest + TypeScript checks

### Changed
- Pipeline transcription step shows "Starting transcription with X model..." when model is already cached instead of misleading "Loading..." message
- `PRELOAD_MODEL` config updated from single-model to multi-model support
- Concurrency tuning now respects explicit `MAX_CONCURRENT_TASKS` env var, skipping auto-tune override when set
- Docker Compose passes `MAX_CONCURRENT_TASKS` env var to containers
- Frontend SSE hook, progress view, and task store updated for richer transcription state tracking

### Fixed
- ERR_CONNECTION_REFUSED during model preload (server now starts immediately, loads models in background)
- Misleading "Loading model" message when model was already preloaded and cached

## [2.0.0] - 2026-03-13

### Added
- Argos Translate integration for any-to-any language translation (100+ language pairs, post-transcription step)
- Whisper built-in translation (any language to English) exposed in the transcribe form
- Translation batch progress events via SSE for real-time UI updates
- React 18 + TypeScript + Vite frontend replacing Jinja2 server-rendered templates
- Zustand state management (taskStore, uiStore) replacing ad-hoc DOM state
- Client-side SPA navigation with session restore on reload
- Public status page (`/status`) with auto-incident detection, uptime history, and 30s auto-refresh
- Status page admin panel (`/status/manage`) for incident management
- Deployment history section on status page with GitHub CI/CD badges and clickable commit SHA links
- About, Contact, and Security static pages with fixed navigation header
- `/security` page documenting attack prevention measures
- Distributed architecture support: Redis Pub/Sub, Celery workers, nginx load balancer
- `ROLE` environment variable for multi-server deployment (`standalone`, `web`, `worker`)
- PostgreSQL shared task persistence via `DatabaseTaskBackend` with SQLAlchemy async and Alembic migrations
- S3/MinIO optional shared file storage backend
- `ENVIRONMENT` mode (`dev`/`prod`) for deployment flexibility
- TLS support with Let's Encrypt certificates and HTTP-to-HTTPS redirect
- Docker TLS support with bind-mount directory safety checks
- Automated deployment script and DEPLOY.md guide
- Standalone embed subtitles tab for local-file embedding (upload video + subtitle separately)
- Embed style live preview on both transcription and standalone embed panels
- Subtitle embedding improvements: soft mux and hard burn with ASS styling presets
- Disk usage percentage in health panel with root filesystem fallback
- Pipeline step tracking with step timing data emitted via SSE
- Critical state system: health monitor auto-blocks uploads and aborts in-flight tasks on disk/DB/VRAM failure
- Worker health monitoring: background checks for disk, DB, VRAM, workers
- Audit trail: all sensitive operations logged to PostgreSQL `audit_log` table
- ClamAV quarantine integration for optional virus scanning of uploads
- Analytics dashboard with upload counters, timeseries, daily aggregates, and data export
- Graceful FFmpeg feature degradation when FFmpeg is missing
- Paginated subtitle editor to handle 10,000+ segments without lag
- OWASP security test fixtures with real SQL injection, XSS, and path traversal payloads
- E2E tests with Playwright (excluded from default pytest run)
- MSW mocks, Vitest, and JSON schemas for parallel frontend/backend development
- Test suite expanded to 1,326 tests (up from 307 in v1.0.0)

### Changed
- Frontend migrated from Jinja2 server-rendered templates to React SPA (Vite + TypeScript + Tailwind CSS)
- UI redesigned with light theme replacing dark theme
- Task Queue redesigned as fixed flex sidebar (always visible, no scrolling needed)
- Embed panel simplified to soft-mux only with more prominent placement
- Embed style options reduced to color + size only (from 6 presets)
- Model info panel redesigned with structured card layout
- Subtitle editor layout: timestamp stacked above textarea for full-width editing
- Advanced Options panel removed from transcription form (settings moved inline)
- Video preview and subtitle editor panels removed from output card
- GitHub commits cache TTL tuned (30s for freshness, 300s with stale fallback on rate limit)
- Status page polling reduced from 1s to 30s with server-side caching
- Health status uses `asyncio.Lock` to serialize cache fills (prevents freeze on rapid refresh)
- Blocking syscalls in health monitoring offloaded from event loop via `asyncio.to_thread`
- Scrollbar styling unified between React and legacy Jinja2 pages (pill thumb, Firefox support)
- Navigation header unified across all pages with consistent alignment
- Technology credits updated across all UI surfaces
- CLAUDE.md rewritten to reflect current architecture

### Fixed
- Server freeze on rapid F5 refresh (health cache serialization with asyncio.Lock)
- Server freeze from blocking syscalls in event loop (health status offloaded to thread)
- Embed button not showing after transcription without page refresh
- Live subtitle preview not restoring after F5 refresh
- Output panel not showing after transcription (stale refs to deleted Advanced Options elements)
- Offline banner flickering during heavy CPU load
- Disk percentage showing 0% (fallback to root filesystem when mount point unavailable)
- Disk percent computation crashing health check in tests
- HealthPanel props type mismatch in StatusPage
- Commit card collapsing on refresh in deployment history
- Jump-to-segment scrolling the browser window instead of the editor pane
- Embed mode cards shifting layout on selection (description length and card sizing)
- Pause timer bug and paused state reconnection after disconnect
- UI state not persisting across Transcribe/Combine tab navigation
- Download button visibility after transcription completion
- Container crash from unwritable bind-mount directories
- CI test failures: missing uploads dir, cross-platform path sanitization, sessionStorage to localStorage migration
- Multiple ruff lint errors across routes and middleware modules

### Security
- Fixed task enumeration (IDOR) vulnerability allowing access to other users' tasks
- Fixed rate-limit proxy bypass vulnerability
- Added dynamic OWASP assertion tests with real SQL injection, XSS, and path traversal fixtures
- Brute force protection middleware with exponential backoff
- Request body size limiting middleware

## [1.0.0] - 2026-03-12

### Added
- AI-powered subtitle generation using faster-whisper (CTranslate2 engine)
- Support for 99 languages with auto-detection
- Output formats: SRT, VTT, JSON (with word-level timestamps)
- GPU acceleration (CUDA) with automatic model selection based on VRAM
- CPU fallback with hardware-aware optimization (OMP threads, model selection)
- 5 Whisper models: tiny, base, small, medium, large
- Word-level timestamps for karaoke-style subtitles
- Speaker diarization via pyannote.audio (optional, graceful degradation)
- Custom vocabulary via `initial_prompt` for domain-specific terms
- Whisper translate mode (any language to English)
- VAD filtering (Silero) for silence skipping
- Smart line-breaking at sentence, clause, and word boundaries
- Characters per second (CPS) validation (Netflix/YouTube standards)
- Subtitle embedding: soft mux (MKV/MP4) and hard burn with ASS styling
- 6 style presets: default, youtube_white, youtube_yellow, cinema, large_bold, top_position
- In-browser subtitle editor with save/regenerate
- Single-page web application with dark theme (Jinja2 templates)
- Drag-and-drop file upload with batch processing
- Real-time progress via SSE and WebSocket
- Video preview with subtitle track overlay
- Task queue visualization
- Built-in monitoring dashboard (`/dashboard`)
- System capability detection at startup (CPU, GPU, RAM, disk, OS)
- Hardware-aware auto-tuning (threads, concurrency, model selection)
- Structured JSON logging (`app.jsonl`) for ELK/Grafana/Loki integration
- Request ID tracing across middleware, logs, and response headers
- Global exception handler preventing service crashes
- Background file cleanup (configurable 24h retention)
- Task persistence across restarts (JSON file backend)
- Dockerfile (CPU) + Dockerfile.gpu (NVIDIA CUDA) with non-root user
- docker-compose.yml with CPU/GPU profiles
- GitHub Actions CI/CD: lint, test, build, health check
- API key authentication (`X-API-Key` header, optional)
- Prometheus `/metrics` endpoint (zero-dependency)
- Health (`/health`) and readiness (`/ready`) probes
- Graceful shutdown with in-flight task draining
- Session management via cookies with task ownership
- Rate limiting via slowapi
- 307 automated tests across 10 test modules
- Cross-platform support (Linux, Windows, macOS, Docker)

### Security
- File extension allowlist + magic byte verification
- Filename sanitization (path separators, null bytes, special chars)
- File size limits (1KB - 2GB) and audio duration limit (4 hours)
- ffmpeg protocol whitelist + execution timeout
- Security headers: CSP, X-Frame-Options, X-Content-Type-Options
- Path traversal prevention on downloads
- Auth middleware, brute force protection, body size limits
- Audit logging for sensitive operations

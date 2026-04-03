# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.1](https://github.com/volehuy1998/subtitle-generator/compare/v2.5.0...v2.5.1) (2026-04-03)


### Bug Fixes

* **ux:** close all user feedback gaps — 16 fixes across 19 files ([#215](https://github.com/volehuy1998/subtitle-generator/issues/215)) ([77ff962](https://github.com/volehuy1998/subtitle-generator/commit/77ff9622b52581455a7b5888fbe967f6c2ba1736))

## [2.5.0](https://github.com/volehuy1998/subtitle-generator/compare/v2.4.0...v2.5.0) (2026-03-23)


### Features

* critical state module — 8 health checks, static HTML page, SPA overlay ([#201](https://github.com/volehuy1998/subtitle-generator/issues/201)) ([321d2b1](https://github.com/volehuy1998/subtitle-generator/commit/321d2b115ec66bba8c1eec2b28ac59b57f05d878))
* **deploy:** branch-per-environment deployment model ([#186](https://github.com/volehuy1998/subtitle-generator/issues/186)) ([4cb4dc6](https://github.com/volehuy1998/subtitle-generator/commit/4cb4dc601f70b24151d566dd14b8a5e293e2814d))
* **test:** add Drop, See, Refine E2E test suite (tests/e2e_newui/) ([#173](https://github.com/volehuy1998/subtitle-generator/issues/173)) ([bc738d9](https://github.com/volehuy1998/subtitle-generator/commit/bc738d99e358da1e8eeb0be04c9a47d03386697e))
* **ui:** Drop, See, Refine — full frontend redesign ([#171](https://github.com/volehuy1998/subtitle-generator/issues/171)) ([811305a](https://github.com/volehuy1998/subtitle-generator/commit/811305a6a87cf024a38dc997dc339fbb0f97b7e7))
* **ui:** Premium Editorial redesign — dark mode, settings, power-user controls ([#180](https://github.com/volehuy1998/subtitle-generator/issues/180)) ([487a4ff](https://github.com/volehuy1998/subtitle-generator/commit/487a4ffc5c34187258e4ad7ef2ef23bc14867662))


### Bug Fixes

* **ci:** add stub checks for all 9 required status checks in docs workflow ([#190](https://github.com/volehuy1998/subtitle-generator/issues/190)) ([74f3eb7](https://github.com/volehuy1998/subtitle-generator/commit/74f3eb7d3d4f2d7eceebc8f44d6c838e6eca87bc))
* **docker:** cpu profile uses nginx reverse proxy instead of direct TLS ([#163](https://github.com/volehuy1998/subtitle-generator/issues/163)) ([a3100be](https://github.com/volehuy1998/subtitle-generator/commit/a3100be9fa757753bbd9587f889e2049e82ebab6))
* **docker:** preload large model in cpu profile ([#164](https://github.com/volehuy1998/subtitle-generator/issues/164)) ([c66eec3](https://github.com/volehuy1998/subtitle-generator/commit/c66eec39bda158dcf8693efaa854192b95b75ac3))
* **embed:** wait for SSE embed_done before showing download link ([#183](https://github.com/volehuy1998/subtitle-generator/issues/183)) ([78c6027](https://github.com/volehuy1998/subtitle-generator/commit/78c60274560730c68a9c718764708d3357704025))
* **pipeline:** store model, audio_duration, step_timings in task dict ([#177](https://github.com/volehuy1998/subtitle-generator/issues/177)) ([ec87419](https://github.com/volehuy1998/subtitle-generator/commit/ec874191e46d5ebcceebed973cc5b3a73acccc74))
* **test:** fix upload E2E test isolation and SPA navigation detection ([#174](https://github.com/volehuy1998/subtitle-generator/issues/174)) ([09797ab](https://github.com/volehuy1998/subtitle-generator/commit/09797abae49a575f429ee4485791732eca5931d9))
* **ui:** 5 bugs — embed progress, filename truncation, undefined segments, error flash, translate panel ([#184](https://github.com/volehuy1998/subtitle-generator/issues/184)) ([b21f528](https://github.com/volehuy1998/subtitle-generator/commit/b21f528a2bef0cae3d6af5c99c5d202bb8a8e49e))
* **ui:** add working translation endpoint + fix TranslatePanel ([#185](https://github.com/volehuy1998/subtitle-generator/issues/185)) ([e97df07](https://github.com/volehuy1998/subtitle-generator/commit/e97df0765ccd96555dde51764c057198ccc7b58f))
* **ui:** align duplicates API response shape with backend ([#172](https://github.com/volehuy1998/subtitle-generator/issues/172)) ([3603d0c](https://github.com/volehuy1998/subtitle-generator/commit/3603d0cdce83789c3828009e2bd5426b5414ffb2))
* **ui:** browser audit — 8 bugs fixed in editor and static pages ([#176](https://github.com/volehuy1998/subtitle-generator/issues/176)) ([730001e](https://github.com/volehuy1998/subtitle-generator/commit/730001e473de7161bc4412bcb72e6b8abaa1a4e3))
* **ui:** CSS custom property var() fix + contrast improvements ([#178](https://github.com/volehuy1998/subtitle-generator/issues/178)) ([916df79](https://github.com/volehuy1998/subtitle-generator/commit/916df7950ef7a0a168d56f29d49ae66601b844b0))
* **ui:** prevent embed button race condition — disable during burn, handle 409, clear stale download ([#182](https://github.com/volehuy1998/subtitle-generator/issues/182)) ([47485e9](https://github.com/volehuy1998/subtitle-generator/commit/47485e9caef2c14bea797fc25bd240df25239b03))
* **ui:** show visible loading badge during model preload ([#165](https://github.com/volehuy1998/subtitle-generator/issues/165)) ([1431366](https://github.com/volehuy1998/subtitle-generator/commit/143136632035eecc10b20d29fa072d0966432710))
* **ui:** SSE done handler crashes editor with segment count as array ([#175](https://github.com/volehuy1998/subtitle-generator/issues/175)) ([d4510fa](https://github.com/volehuy1998/subtitle-generator/commit/d4510fad1b5732cfaf1a625abe2a7a8be4454816))


### Documentation

* add long-term development plan with investor priorities ([#144](https://github.com/volehuy1998/subtitle-generator/issues/144)) ([40b34b9](https://github.com/volehuy1998/subtitle-generator/commit/40b34b996e61f37a645d97190ef59a63128731d3))
* sync CLAUDE.md deployment flow with actual commands ([#167](https://github.com/volehuy1998/subtitle-generator/issues/167)) ([47caf8c](https://github.com/volehuy1998/subtitle-generator/commit/47caf8c372eeae57bde65411a2dde73474dcd291))
* update stale documentation to reflect current state ([#166](https://github.com/volehuy1998/subtitle-generator/issues/166)) ([be9d873](https://github.com/volehuy1998/subtitle-generator/commit/be9d873f353c0fdd6e074c53f83aae6c6389893c))

## [2.4.0](https://github.com/volehuy1998/subtitle-generator/compare/v2.3.0...v2.4.0) (2026-03-17)


### Features

* **lumen:** Sprint L1 — foundation ([#146](https://github.com/volehuy1998/subtitle-generator/issues/146)) ([d0cb63d](https://github.com/volehuy1998/subtitle-generator/commit/d0cb63dead07cbbb5688f8998ca4d05edc92c0f6))
* **lumen:** Sprint L2 — design system, light theme ([#147](https://github.com/volehuy1998/subtitle-generator/issues/147)) ([54afbc3](https://github.com/volehuy1998/subtitle-generator/commit/54afbc3f6a969c734a07a06970f1baddc1804dc6))
* **lumen:** Sprint L3 — model readiness API ([#148](https://github.com/volehuy1998/subtitle-generator/issues/148)) ([7025d6e](https://github.com/volehuy1998/subtitle-generator/commit/7025d6e09624c4167d859ada3127b6e83ddfab9b))
* **lumen:** Sprint L6 — component styling ([#150](https://github.com/volehuy1998/subtitle-generator/issues/150)) ([5f448ae](https://github.com/volehuy1998/subtitle-generator/commit/5f448aec874e2bac6f842629a037c3ba251eca85))
* **lumen:** Sprints L4+L5 — confirmation + liveness ([#149](https://github.com/volehuy1998/subtitle-generator/issues/149)) ([8d58133](https://github.com/volehuy1998/subtitle-generator/commit/8d58133087bf10e6ecf8ee073090e8e9b751117e))
* **lumen:** Sprints L61-L80 — integration + hardening phase complete ([213e9f3](https://github.com/volehuy1998/subtitle-generator/commit/213e9f31ce67eaf0cbd0b160f79c0c010b9565ca))


### Bug Fixes

* **ci:** invalidate stale reviews after new pushes to PR ([#143](https://github.com/volehuy1998/subtitle-generator/issues/143)) ([9686d86](https://github.com/volehuy1998/subtitle-generator/commit/9686d8680daf5a997c5238a5ba63a64db7d3861f))
* correct team member count in .sentinel/ frontmatter ([#116](https://github.com/volehuy1998/subtitle-generator/issues/116)) ([aac9cf0](https://github.com/volehuy1998/subtitle-generator/commit/aac9cf0eb59f671029599e3ffcc37fd6b70c0cd5))
* **health:** replace asyncio.timeout for Python 3.10 compatibility ([#120](https://github.com/volehuy1998/subtitle-generator/issues/120)) ([51839bd](https://github.com/volehuy1998/subtitle-generator/commit/51839bd9ad79ecac0a01238bb8c91d67e99c4b45))
* **policy:** ban --admin merge override, close enforcement loophole ([#142](https://github.com/volehuy1998/subtitle-generator/issues/142)) ([ea92acc](https://github.com/volehuy1998/subtitle-generator/commit/ea92acca8dfcc01844be4ac4caa8c2744152fffd))
* preferences defaults + CLAUDE.md deployment docs ([10ca293](https://github.com/volehuy1998/subtitle-generator/commit/10ca293d508a335da079940fc060383b0052449c))
* resolve 3 DVS deployment issues — nginx upload, ffmpeg errors, JS error ([#128](https://github.com/volehuy1998/subtitle-generator/issues/128)) ([4803a99](https://github.com/volehuy1998/subtitle-generator/commit/4803a998b1983c80b75367918120476e097abb66)), closes [#127](https://github.com/volehuy1998/subtitle-generator/issues/127)
* resolve 9 DVS follow-up issues — Sprint 31 ([#139](https://github.com/volehuy1998/subtitle-generator/issues/139)) ([43bcbb8](https://github.com/volehuy1998/subtitle-generator/commit/43bcbb814c4b0b706f6699f87ccc1dfaeb8e9eef))


### Documentation

* add deployment UI rules to prevent same-UI-everywhere mistake ([#124](https://github.com/volehuy1998/subtitle-generator/issues/124)) ([f9742b8](https://github.com/volehuy1998/subtitle-generator/commit/f9742b8b5f6e9d0dc4b964cede702ac8cad2a1ce))
* consolidate all operational knowledge into CLAUDE.md ([#118](https://github.com/volehuy1998/subtitle-generator/issues/118)) ([70f1d1a](https://github.com/volehuy1998/subtitle-generator/commit/70f1d1aaf05f7a7a9e04b56bf31a204a7c6747b9))
* document dual-UI system (React SPA vs Jinja templates) ([#123](https://github.com/volehuy1998/subtitle-generator/issues/123)) ([7e1a344](https://github.com/volehuy1998/subtitle-generator/commit/7e1a344517cee1d4cda03e152ae0aab4b47d522f))
* expand CLAUDE.md with team structure and operational rules ([#117](https://github.com/volehuy1998/subtitle-generator/issues/117)) ([eef45fd](https://github.com/volehuy1998/subtitle-generator/commit/eef45fdee3268677bcc585f8202a992b89f79e27))
* fill 15 gaps found in CLAUDE.md audit ([#119](https://github.com/volehuy1998/subtitle-generator/issues/119)) ([36b5532](https://github.com/volehuy1998/subtitle-generator/commit/36b55327d8bff65db5656dfb09545c255aab96f7))
* Phase Lumen — quality & design overhaul spec ([#145](https://github.com/volehuy1998/subtitle-generator/issues/145)) ([1d39d05](https://github.com/volehuy1998/subtitle-generator/commit/1d39d05b38264b27607d71b30653928a2eb23711))
* promote React SPA to production on all main domains ([#138](https://github.com/volehuy1998/subtitle-generator/issues/138)) ([6ba9160](https://github.com/volehuy1998/subtitle-generator/commit/6ba91600e62a3f788e8995625383478e05daa313))
* save session context to CLAUDE.md ([eb53aab](https://github.com/volehuy1998/subtitle-generator/commit/eb53aab6e1ce314431d31c7fd347413f91eedc57))
* simplify deployment rule to technology-agnostic matching principle ([#125](https://github.com/volehuy1998/subtitle-generator/issues/125)) ([c67c9da](https://github.com/volehuy1998/subtitle-generator/commit/c67c9da83de04ec06f515284327b4b31d9b4cd8f))

## [2.3.0](https://github.com/volehuy1998/subtitle-generator/compare/v2.2.0...v2.3.0) (2026-03-14)


### Features

* **ci:** automated deployment collaboration — CODEOWNERS + release notify + deploy validation ([#83](https://github.com/volehuy1998/subtitle-generator/issues/83)) ([7b3020a](https://github.com/volehuy1998/subtitle-generator/commit/7b3020a3ebfc76dad7d3cf0ef51a74a2c3501bad))
* **ci:** automated sensitive data scanning to prevent information leaks ([#87](https://github.com/volehuy1998/subtitle-generator/issues/87)) ([90f5f82](https://github.com/volehuy1998/subtitle-generator/commit/90f5f82f5c04926a3a5dff97c59374fab01c3b72))


### Bug Fixes

* **config:** bump PROD_IMAGE_TAG to v2.2.0 in .env.example ([#76](https://github.com/volehuy1998/subtitle-generator/issues/76)) ([b904090](https://github.com/volehuy1998/subtitle-generator/commit/b904090739a0e6022b3284b433d32f686f9dbc2b))


### Documentation

* **deploy:** add Configuration Best Practices section ([#80](https://github.com/volehuy1998/subtitle-generator/issues/80)) ([aac31b7](https://github.com/volehuy1998/subtitle-generator/commit/aac31b7a83ea895963474eff5bb727f3c4428beb))

## [2.2.0](https://github.com/volehuy1998/subtitle-generator/compare/v2.1.0...v2.2.0) (2026-03-14)

### Features

* **ui:** Enterprise Slate dark theme — corporate redesign ([#45](https://github.com/volehuy1998/subtitle-generator/issues/45)) ([070bcff](https://github.com/volehuy1998/subtitle-generator/commit/070bcffb1e89a933ae3ed7ad9a4e8929d0541518)), closes [#44](https://github.com/volehuy1998/subtitle-generator/issues/44)


### Bug Fixes

* **deploy:** add complete .env.example and document Docker preview subdomain ([#49](https://github.com/volehuy1998/subtitle-generator/issues/49)) ([ca5abe3](https://github.com/volehuy1998/subtitle-generator/commit/ca5abe31950d1f5264fc802c5b062fef2f8a2ab4)), closes [#47](https://github.com/volehuy1998/subtitle-generator/issues/47)
* **deploy:** fix deploy.sh Unicode bug, add newui profile, pin PROD_IMAGE_TAG, update docs ([#73](https://github.com/volehuy1998/subtitle-generator/issues/73)) ([627429e](https://github.com/volehuy1998/subtitle-generator/commit/627429e087ecfa9b1359eca5dc30eedda2f1a20c))
* **status:** remove test incidents from public status page ([#58](https://github.com/volehuy1998/subtitle-generator/issues/58)) ([2472d9a](https://github.com/volehuy1998/subtitle-generator/commit/2472d9a9507becdbac4c65a0f3cfa2376e73a164))
* **ui:** fix 5 ESLint errors and remove || true mask from CI ([#65](https://github.com/volehuy1998/subtitle-generator/issues/65)) ([54dbb77](https://github.com/volehuy1998/subtitle-generator/commit/54dbb7790c26d9be9bf4cfe4361949df6c364078))
* **ui:** hide GPU/CPU hardware badge on non-app pages ([#59](https://github.com/volehuy1998/subtitle-generator/issues/59)) ([f06d051](https://github.com/volehuy1998/subtitle-generator/commit/f06d0513854b797e4d40e94e70e924bb04351afa)), closes [#54](https://github.com/volehuy1998/subtitle-generator/issues/54)
* **ui:** update About page tech stack — React 18 → React 19, Vite → Vite 6 ([#60](https://github.com/volehuy1998/subtitle-generator/issues/60)) ([e74eecb](https://github.com/volehuy1998/subtitle-generator/commit/e74eecbea961d76ed2ca010a22318b0604487d53))


### Security

* **security:** allow Google Fonts in CSP so brand fonts load correctly ([#57](https://github.com/volehuy1998/subtitle-generator/issues/57)) ([bbd0a92](https://github.com/volehuy1998/subtitle-generator/commit/bbd0a92e6c1c6525ec15b312a662f15adb019af7))
* **security:** stop post-commit hook updating last_security_commit on every commit ([#61](https://github.com/volehuy1998/subtitle-generator/issues/61)) ([65a4b51](https://github.com/volehuy1998/subtitle-generator/commit/65a4b51bc6cdb976c99191c7a5e4639eee3d6377))
* **middleware:** add Secure flag to session cookie and explicit CORS allow_headers ([#74](https://github.com/volehuy1998/subtitle-generator/issues/74)) ([92ca304](https://github.com/volehuy1998/subtitle-generator/commit/92ca3044b465b586d9e36aa20b0da0c5157872cf))


### Documentation

* **config:** fix .sentinel restore path and explain naming pattern ([#43](https://github.com/volehuy1998/subtitle-generator/issues/43)) ([c280af3](https://github.com/volehuy1998/subtitle-generator/commit/c280af30b97db4ede77900b6603a67b74f51bf60))
* **ui:** establish subdomain-first design review policy ([#50](https://github.com/volehuy1998/subtitle-generator/issues/50)) ([923dcec](https://github.com/volehuy1998/subtitle-generator/commit/923dcec782dbdb99d68c8beabc1f592af9c04a6a)), closes [#48](https://github.com/volehuy1998/subtitle-generator/issues/48)

## [Unreleased]

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

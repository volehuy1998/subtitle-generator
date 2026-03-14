# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — v2.1.0

### Added
- **Upload progress tracking**: Instant screen switch on file drop with real-time XHR upload percentage
- **Background model preloading**: Server accepts connections immediately, model loads in background (~60s saved)
- **Model preload status indicator**: Spinner on model row while loading, green "Ready" badge when done
- **Transcription detail panel**: Audio position bar, speed (Nx realtime), ETA countdown, elapsed time, segment counter
- **Model selector redesign**: Card-based layout with research-accurate specs (params, WER, speed bars)
- **Tooltips for abbreviations**: WER, ETA, realtime speed all have hover explanations
- **Conventional Commits hook**: `commit-msg` hook validates all commits follow `type(scope): description`
- **Pre-commit hook**: Blocks secrets, cert/key files, .env; runs ruff (Python) and eslint (frontend)
- **Branch protection**: `main` branch requires CI checks (lint + test) to pass
- **PR template**: `.github/PULL_REQUEST_TEMPLATE.md` with type checkboxes and test plan
- **CI: Frontend testing**: GitHub Actions now runs Vitest + TypeScript checks alongside backend tests
- **CONTRIBUTING.md**: Full contribution guidelines with git workflow, code standards, testing guide
- **Git standards in CLAUDE.md**: Conventional Commits, GitHub Flow, semver documented

### Changed
- Pipeline message shows "Starting transcription with large model..." when model is cached (instead of misleading "Loading...")
- Model selector data updated with accurate OpenAI Whisper paper specs (39M-1.55B params, WER benchmarks)
- `MAX_CONCURRENT_TASKS` now configurable via env var (supports 10 concurrent users)

### Fixed
- ERR_CONNECTION_REFUSED during model preload (server now starts immediately)
- Misleading "Loading model" message when model was already preloaded (0.002s cache hit)

---

## [2.0.0] — 2026-03-13

### Added
- **Translation support**: Whisper built-in (any -> English) + Argos Translate (any-to-any, 100+ language pairs)
- **Subtitle embedding improvements**: Soft mux and hard burn with ASS styling presets
- **Public status page** at /status with auto-incident detection and uptime history
- **Multi-server deployment**: ROLE env var (standalone/web/worker), Redis Pub/Sub, Celery, S3 storage
- **Critical state system**: Health monitor auto-blocks uploads and aborts tasks on disk/DB/VRAM failure
- **Database task backend**: PostgreSQL persistence with SQLAlchemy async + Alembic migrations
- **Analytics dashboard**: Upload counters, timeseries, daily aggregates, data export
- **SPA routing**: Client-side navigation for About, Contact, Security, Status pages
- **Speaker diarization**: pyannote.audio integration with configurable speaker count
- **Real-time SSE**: Server-sent events with exponential backoff, watchdog, heartbeat
- **WebSocket support**: Alternative real-time transport alongside SSE and polling
- **Audit trail**: All sensitive operations logged to PostgreSQL audit_log table
- **Brute force protection**: Rate limiting middleware with exponential backoff
- **ClamAV integration**: Optional virus scanning for uploads
- **System capability detection**: Auto-tunes OMP threads, concurrent tasks, model selection at startup
- **Worker health monitoring**: Background health checks for disk, DB, VRAM, workers

### Security
- Magic bytes validation for uploaded files
- Filename sanitization (path traversal, null bytes, special chars)
- Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- API key authentication (optional, via X-API-Key header)
- Request body size limiting middleware
- ffmpeg protocol whitelist + execution timeout

---

## [1.0.0] — 2026-03-11

### Added
- Core subtitle generation with faster-whisper (CTranslate2 engine)
- 99 languages with auto-detection
- 5 Whisper models: tiny, base, small, medium, large
- Output formats: SRT, VTT, JSON
- GPU acceleration (CUDA) with automatic model selection
- CPU fallback with hardware-aware optimization
- Word-level timestamps for karaoke-style subtitles
- Smart line-breaking (sentence/clause/word boundaries)
- React SPA frontend with drag-and-drop upload
- Real-time progress tracking
- Docker support with CPU/GPU profiles
- GitHub Actions CI/CD pipeline
- 307+ automated tests
- Health and readiness probes
- Graceful shutdown with task draining

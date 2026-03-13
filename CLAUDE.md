# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Subtitle generator web app: upload audio/video, transcribe with faster-whisper (CTranslate2), download SRT/VTT/JSON. Supports translation (Whisper built-in + Argos Translate), subtitle embedding (soft mux / hard burn), speaker diarization, and real-time progress via SSE/WebSocket. FastAPI backend with React SPA frontend (Vite + Zustand). Deployable as a single standalone server or multi-server (web + worker) with Redis and S3.

## Commands

```bash
# Run the app (development mode — plain HTTP, no HSTS)
python main.py                    # starts uvicorn on 0.0.0.0:8000

# Run in production mode (HTTPS on 443 + HTTP redirect on 80)
ENVIRONMENT=prod SSL_CERTFILE=/path/to/cert.pem SSL_KEYFILE=/path/to/key.pem python main.py

# Run all tests (1326 tests, ~20s)
pytest tests/ -v --tb=short

# Run e2e tests (requires playwright)
pytest tests/e2e/ -v

# Run a single test file
pytest tests/test_sprint17.py -v

# Run a single test
pytest tests/test_api.py::test_health_endpoint -v

# Lint (matches CI)
ruff check . --select E,F,W --ignore E501

# Docker
docker compose --profile cpu up --build
docker compose --profile gpu up --build    # NVIDIA GPU
```

## Architecture

### Pipeline Flow (`app/services/pipeline.py`)
Upload -> probe (ffprobe) -> extract audio (ffmpeg->WAV) -> load model -> transcribe (faster-whisper) -> optional diarize (pyannote) -> optional translate (Whisper or Argos) -> format (line-breaking) -> write SRT/VTT/JSON -> optional auto-embed. Each step emits SSE events for real-time UI updates.

### Module Layout
- **`app/routes/`** (29 modules) — FastAPI routers, one per feature domain. Aggregated in `routes/__init__.py`. Covers: upload, download, control, events, embed, combine, translation, tasks, subtitles, analytics, dashboard, feedback, auth, monitoring, health, metrics, webhooks, export, security, admin_logs, query, tracking, status_page, system, pages, ws, logs.
- **`app/services/`** (32 modules) — Business logic. Key: `pipeline.py` (orchestration), `transcription.py` (whisper), `model_manager.py` (model caching), `translation.py` (Whisper + Argos translation), `subtitle_embed.py` (soft/hard embed), `diarization.py` (pyannote), `analytics.py` (counters/timeseries), `health_monitor.py` (background checks + critical state), `cleanup.py` (file/DB retention), `rate_limiter.py`, `quarantine.py` (ClamAV), `audit.py`, `pubsub.py` (Redis Pub/Sub).
- **`app/middleware/`** (12 modules) — Auth, security headers, session, request logging, brute force, body limit, compression, CORS, rate limit, slow query logging, critical state blocking.
- **`app/db/`** — SQLAlchemy async models (15 tables), engine setup (PostgreSQL via asyncpg, SQLite fallback via aiosqlite), Alembic migrations (5 versions), database task backend.
- **`app/utils/`** — SRT/VTT/JSON generation, line-breaking, media probing (ffmpeg), file validation, security helpers.
- **`app/config.py`** — All constants, paths, env vars, limits.
- **`app/state.py`** — Global in-memory state: `state.tasks[task_id]` dict, model cache with `state.model_lock`, translation model cache with `state.translation_model_lock`, task semaphore, critical state management.
- **`frontend/src/`** — React SPA (Vite + TypeScript + Zustand). Pages: App (main), StatusPage, AboutPage, ContactPage, SecurityPage. Components organized by feature: transcribe, embed, output, progress, system, layout.

### Frontend (React SPA)
- **Build**: Vite + TypeScript, Tailwind CSS
- **State management**: Zustand stores (`taskStore.ts` for task state, `uiStore.ts` for UI/theme)
- **Real-time**: `useSSE` hook for server-sent events, `useHealthStream` for health monitoring
- **API client**: `frontend/src/api/client.ts` — typed HTTP client for all backend endpoints
- **Client-side routing**: SPA navigation without full page reloads, session restore on reload

### Concurrency Model
Each upload spawns a background thread via `asyncio.to_thread()`. Concurrent tasks limited by semaphore (default 3 in `config.MAX_CONCURRENT_TASKS`). Models cached in `state.loaded_models` with thread-safe lock. Single uvicorn worker required (Whisper is not multi-worker safe).

### State & Persistence
- **Tasks**: in-memory dict (`state.tasks`), persisted to PostgreSQL via `DatabaseTaskBackend` (fallback: `task_history.json`).
- **Models**: cached in `state.loaded_models[(model_size, device)]`, reused across requests.
- **Translation models**: cached in `state.translation_models[(src, tgt)]` with thread-safe lock.
- **Analytics**: in-memory ring buffer (24h, minute resolution) + PostgreSQL tables (daily aggregates, timeseries, events).
- **Audit trail**: all sensitive operations logged to PostgreSQL `audit_log` table.
- **Task backend and storage**: abstracted (`task_backend.py`, `storage.py`) — supports local/PostgreSQL/Redis for tasks, local/S3 for files.

### Real-Time Updates
Three transport options, all delivering the same pipeline events:
- SSE: `GET /events/{task_id}`
- WebSocket: `WS /ws`
- Polling: `GET /progress/{task_id}`

### Translation
Two translation modes available from the Transcribe form:
1. **Whisper translate** (any language -> English): Uses faster-whisper's built-in `task="translate"` during transcription. Higher quality, no extra dependency.
2. **Argos Translate** (any-to-any language pairs): Offline neural MT via `argostranslate`. Models downloaded on demand (~100-200MB per pair), cached in `state.translation_models`. Runs as a post-transcription step with progress events.

### Subtitle Embedding
- **Soft embed**: Mux SRT track into MKV/MP4 container without re-encoding (ffmpeg `-c copy`).
- **Hard burn**: Render subtitles as ASS overlay via ffmpeg filter, re-encodes video.
- **Style presets**: Configurable font, size, color, position, background opacity.
- **Auto-embed**: Pipeline can auto-embed after transcription if `auto_embed` param is set.
- **Combine route**: Users can upload their own video + subtitle files for embedding.

### Multi-Server Deployment
- **Roles** (`ROLE` env var): `standalone` (default, all-in-one), `web` (API only), `worker` (background processing via Celery).
- **Redis**: Pub/Sub for inter-worker SSE relay, Celery broker, rate limit state.
- **PostgreSQL**: Shared task persistence, analytics, audit logs.
- **S3/MinIO**: Optional shared file storage for uploads and outputs.

### Critical State & Health Monitoring
- `health_monitor.py` runs background checks (disk, DB, VRAM, workers).
- On failure: sets `state.system_critical`, blocks new uploads, force-aborts in-flight tasks.
- Injects `CriticalAbortError` into pipeline threads, kills ffmpeg subprocesses.
- Frontend shows critical state banner, disables upload form.

## Testing Patterns

Tests mock `torch`, `faster_whisper`, and `psutil` in `conftest.py` via `sys.modules` patching BEFORE any app imports. This avoids loading GPU/ML dependencies during testing.

Tests use `httpx.AsyncClient` with `ASGITransport` against the FastAPI app directly (no server needed). Test files are organized by sprint (`test_sprint1.py` through `test_sprint30.py`) plus domain files (`test_api.py`, `test_security.py`, `test_srt.py`, `test_formatting.py`, `test_combine.py`, `test_translation.py`, `test_control.py`, etc.).

E2E tests in `tests/e2e/` use Playwright for browser testing. They are excluded from the default `pytest tests/` run (requires `pytest-playwright`).

When adding tests, follow the existing sprint pattern or add to the relevant domain test file.

## Key Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` (HTTP, no HSTS) or `prod` (HTTPS, HSTS) | `dev` |
| `SSL_CERTFILE` | TLS certificate path (prod mode) | empty |
| `SSL_KEYFILE` | TLS private key path (prod mode) | empty |
| `PORT` | HTTP listen port (dev mode) | `8000` |
| `API_KEYS` | Comma-separated API keys (auth disabled if empty) | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup (tiny/base/small/medium/large) | empty |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | `24` |
| `ENABLE_COMPRESSION` | GZip response compression | `true` |
| `ROLE` | Server role: `standalone`, `web`, or `worker` | `standalone` |
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) or SQLite fallback | SQLite |
| `REDIS_URL` | Redis connection for Pub/Sub, Celery, rate limiting | empty |
| `STORAGE_BACKEND` | File storage: `local` or `s3` | `local` |
| `TRANSLATION_BATCH_SIZE` | Segments per progress update during translation | `50` |

## Conventions

- Python 3.12. No line length limit enforced (E501 ignored).
- Route modules use OpenAPI tags for Swagger grouping.
- All routes registered through `app/routes/__init__.py` router aggregator.
- Middleware order matters: defined in `app/main.py` lifespan/setup (last added = first executed).
- Subtitle embedding requires ffmpeg on PATH (soft mux for MKV/MP4, hard burn via ASS filter).
- System requirements detected at startup (`services/system_capability.py`): CPU/GPU/RAM/OS/codecs, auto-tunes OMP threads and max concurrent tasks.
- Database migrations managed via Alembic (`app/db/alembic/`).
- Frontend built with Vite; dev server proxies API calls to FastAPI backend.

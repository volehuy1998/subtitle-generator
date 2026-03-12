# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Subtitle generator web app: upload audio/video, transcribe with faster-whisper (CTranslate2), download SRT/VTT/JSON. FastAPI backend, Jinja2 templates frontend, real-time progress via SSE/WebSocket.

## Commands

```bash
# Run the app (development mode — plain HTTP, no HSTS)
python main.py                    # starts uvicorn on 0.0.0.0:8000

# Run in production mode (HTTPS)
ENVIRONMENT=prod SSL_CERTFILE=/path/to/cert.pem SSL_KEYFILE=/path/to/key.pem python main.py

# Run all tests (643 tests, ~20s)
pytest tests/ -v --tb=short

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
Upload -> probe (ffprobe) -> extract audio (ffmpeg->WAV) -> load model -> transcribe (faster-whisper) -> optional diarize (pyannote) -> format (line-breaking) -> write SRT/VTT/JSON. Each step emits SSE events for real-time UI updates.

### Module Layout
- **`app/routes/`** (14+ modules) — FastAPI routers, one per feature domain. Aggregated in `routes/__init__.py`.
- **`app/services/`** (15+ modules) — Business logic. Key: `pipeline.py` (orchestration), `transcription.py` (whisper), `model_manager.py` (caching), `analytics.py` (counters/timeseries), `analytics_db.py` (SQLite persistence).
- **`app/middleware/`** (8 modules) — Auth, security headers, session, request logging, brute force, body limit, compression, CORS.
- **`app/utils/`** — SRT/VTT generation, line-breaking, media probing (ffmpeg), file validation.
- **`app/config.py`** — All constants, paths, env vars, limits.
- **`app/state.py`** — Global in-memory state: `state.tasks[task_id]` dict, model cache with `state.model_lock`, task semaphore.

### Concurrency Model
Each upload spawns a background thread via `asyncio.to_thread()`. Concurrent tasks limited by semaphore (default 3 in `config.MAX_CONCURRENT_TASKS`). Models cached in `state.loaded_models` with thread-safe lock. Single uvicorn worker required (Whisper is not multi-worker safe).

### State & Persistence
- Tasks: in-memory dict (`state.tasks`), persisted to `task_history.json` on completion (last 50).
- Models: cached in `state.loaded_models[(model_size, device)]`, reused across requests.
- Analytics: in-memory ring buffer (24h, minute resolution) + SQLite (`analytics.db`).
- Task backend and storage are abstracted (`task_backend.py`, `storage.py`) for future Redis/S3 swap.

### Real-Time Updates
Three transport options, all delivering the same pipeline events:
- SSE: `GET /events/{task_id}`
- WebSocket: `WS /ws`
- Polling: `GET /progress/{task_id}`

## Testing Patterns

Tests mock `torch`, `faster_whisper`, and `psutil` in `conftest.py` via `sys.modules` patching BEFORE any app imports. This avoids loading GPU/ML dependencies during testing.

Tests use `httpx.AsyncClient` with `ASGITransport` against the FastAPI app directly (no server needed). Test files are organized by sprint (`test_sprint1.py` through `test_sprint17.py`) plus domain files (`test_api.py`, `test_security.py`, `test_srt.py`, `test_formatting.py`).

When adding tests, follow the existing sprint pattern or add to the relevant domain test file.

## Key Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` (HTTP, no HSTS) or `prod` (HTTPS, HSTS) | `dev` |
| `SSL_CERTFILE` | TLS certificate path (prod mode) | empty |
| `SSL_KEYFILE` | TLS private key path (prod mode) | empty |
| `PORT` | HTTP listen port (dev mode) | 8000 |
| `API_KEYS` | Comma-separated API keys (auth disabled if empty) | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup (tiny/base/small/medium/large) | empty |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | 24 |
| `ENABLE_COMPRESSION` | GZip response compression | true |

## Conventions

- Python 3.12. No line length limit enforced (E501 ignored).
- Route modules use OpenAPI tags for Swagger grouping (9 tag groups).
- All routes registered through `app/routes/__init__.py` router aggregator.
- Middleware order matters: defined in `app/main.py` lifespan/setup (last added = first executed).
- Subtitle embedding requires ffmpeg on PATH (soft mux for MKV/MP4, hard burn via ASS filter).
- System requirements detected at startup (`services/system_capability.py`): CPU/GPU/RAM/OS/codecs, auto-tunes OMP threads and max concurrent tasks.

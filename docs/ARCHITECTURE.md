# Architecture

**Version**: 2.5.0 | **Tests**: 3,667 | **Sprints**: 110

## System Overview

```
                          CLIENT (Browser)
              Upload | SSE/WS Progress | Download
                  |         |              |
                  v         v              v
  +---------------------------------------------------+
  |              FASTAPI APPLICATION                   |
  |                                                    |
  |  Middleware Stack (request order):                  |
  |  GZip > CORS > SecurityHeaders > BodyLimit >       |
  |  BruteForce > Session > ApiKey > RequestLog        |
  |                                                    |
  |  Route Layer ........... 30 routers                |
  |  Service Layer ......... 32 modules                |
  |  State + Database ...... in-memory + SQLAlchemy    |
  |                                                    |
  |  External: ffmpeg | faster-whisper | pyannote      |
  +---------------------------------------------------+
              |              |              |
         PostgreSQL      Redis (opt)    S3/MinIO (opt)
```

## Pipeline Flow

```
Upload --> Validate (extension, magic bytes, size)
       --> Probe (ffprobe: format, duration, codec)
       --> Extract audio (ffmpeg --> WAV)
       --> Load model (faster-whisper, cached)
       --> Transcribe (CTranslate2, GPU or CPU)
       --> [Diarize] (pyannote, optional)
       --> [Translate] (Whisper built-in or Argos)
       --> Format (line-breaking, timing)
       --> Write (SRT / VTT / JSON)
       --> [Embed] (soft mux or hard burn, optional)
```

Each step emits SSE events for real-time frontend updates. The pipeline runs in a background thread via `asyncio.to_thread()`, gated by a configurable semaphore.

## Module Layout

### Routes (`app/routes/`, 30 modules)

| Group | Endpoints |
|-------|-----------|
| Core workflow | `/upload`, `/events/{id}`, `/download/{id}`, `/embed/{id}` |
| Task management | `/tasks`, `/cancel/{id}`, `/pause/{id}`, `/resume/{id}`, `/subtitles/{id}` |
| Health | `/health`, `/ready`, `/health/stream`, `/health/db`, `/metrics` |
| Analytics | `/analytics/summary`, `/analytics/timeseries`, `/analytics/daily`, `/analytics/export` |
| Auth | `/auth/register`, `/auth/login`, `/auth/api-keys`, `/security/audit` |

### Services (`app/services/`, 32 modules)

| Group | Modules |
|-------|---------|
| Processing | `pipeline`, `transcription`, `model_manager`, `diarization`, `subtitle_embed` |
| Persistence | `sse`, `task_backend`, `task_backend_db`, `storage` |
| Analytics | `analytics`, `analytics_pg`, `tracking`, `monitoring` |
| Security | `auth`, `rate_limiter`, `audit`, `quarantine` |
| Infrastructure | `gpu`, `system_capability`, `cleanup`, `worker_health`, `scaling`, `health_monitor` |

### Middleware (`app/middleware/`, 13 modules)

Execution order (last registered = first executed):
GZip, CORS, SecurityHeaders, BodyLimit, BruteForce, Session, ApiKey, RequestLog, RateLimit, SlowQuery, CriticalState, Version, Compression

### Database (`app/db/`)

SQLAlchemy async with PostgreSQL (asyncpg) or SQLite (aiosqlite) fallback.

| Table | Purpose |
|-------|---------|
| `tasks` | Task records (status, result, metadata) |
| `sessions` | User sessions |
| `users` | User accounts |
| `api_keys` | Programmatic API keys |
| `analytics_events` | Per-event metrics |
| `analytics_daily` | Daily aggregates |
| `analytics_ts` | Minute-resolution time series |
| `audit_logs` | Security events (HMAC-signed) |
| `feedback` | User ratings |
| `ui_events` | Frontend interaction tracking |
| `brute_force_events` | Failed auth attempts |
| `ip_lists` | IP allowlist / blocklist |

Migrations managed by Alembic (5 revisions).

## Concurrency Model

- **Single uvicorn worker** (Whisper is not multi-worker safe)
- **Background threads** via `asyncio.to_thread()` for each transcription task
- **Semaphore** limits concurrent tasks (default 3, auto-tuned by `system_capability.py`)
- **Model cache**: `state.loaded_models[(model_size, device)]` with thread-safe lock
- **Translation cache**: `state.translation_models[(src, tgt)]` with thread-safe lock

## Real-Time Updates

| Transport | Endpoint | Use |
|-----------|----------|-----|
| SSE | `GET /events/{task_id}` | Pipeline progress per task |
| SSE | `GET /health/stream` | System health (5s interval) |
| WebSocket | `WS /ws/{task_id}` | Alternative to SSE |
| Polling | `GET /progress/{task_id}` | Fallback |

## State Management

In-memory state (`app/state.py`) with database persistence:

- **`tasks`**: dict of active tasks, persisted to DB via `DatabaseTaskBackend`
- **`loaded_models`**: cached Whisper models, loaded on demand
- **`task_event_queues`**: ephemeral SSE event queues
- **`_task_semaphore`**: concurrency gate
- **`shutting_down`**: graceful shutdown flag

## Multi-Server Deployment

| Role | Purpose |
|------|---------|
| `standalone` (default) | Single server, all functions |
| `web` | API only, no transcription |
| `worker` | Celery worker, transcription only |

Distributed mode requires Redis (pub/sub, Celery broker, rate limiting) and PostgreSQL (shared persistence). Optional S3/MinIO for shared file storage.

## Translation

Two modes:
1. **Whisper translate** (any to English): built-in `task="translate"` during transcription
2. **Argos Translate** (any to any): offline neural MT, models downloaded on demand (~100-200MB/pair)

## Subtitle Embedding

- **Soft embed**: mux SRT track into MKV/MP4 via `ffmpeg -c copy` (fast, no re-encode)
- **Hard burn**: render as ASS overlay via ffmpeg filter (re-encodes video)
- **Style presets**: default, youtube_white, youtube_yellow, cinema, large_bold, top
- **Auto-embed**: pipeline embeds automatically if `auto_embed` param is set

## Critical State

`health_monitor.py` runs background checks (disk, DB, VRAM, workers). On failure: sets `system_critical`, blocks uploads, force-aborts tasks, kills ffmpeg subprocesses. Frontend shows critical banner.

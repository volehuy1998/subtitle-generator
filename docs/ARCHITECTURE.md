# Subtitle Generator — Architecture & Functional Flow

> **Version**: Sprint 30 · **Updated**: 2026-03-11 · **Tests**: 1166 passing

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Upload   │  │ Progress │  │ Download │  │ Health Indicator   │  │
│  │ Form     │  │ SSE/WS   │  │ Buttons  │  │ (SSE, 1s refresh)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬───────────┘  │
│       │              │              │                  │              │
└───────┼──────────────┼──────────────┼──────────────────┼──────────────┘
        │              │              │                  │
        ▼              ▼              ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                             │
│                                                                     │
│  ┌─────────────────── MIDDLEWARE STACK ──────────────────────────┐  │
│  │  GZip → CORS → SecurityHeaders → BodyLimit → BruteForce →   │  │
│  │  Session → ApiKey → RequestLog                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────── ROUTE LAYER (22 routers) ─────────────────┐  │
│  │  upload │ events │ download │ health │ embed │ tasks │ ...    │  │
│  └─────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌─────────────────── SERVICE LAYER (26 modules) ───────────────┐  │
│  │  pipeline │ transcription │ model_manager │ analytics │ ...   │  │
│  └─────────────────────────┬────────────────────────────────────┘  │
│                             │                                       │
│  ┌────────────────── STATE + DATABASE ──────────────────────────┐  │
│  │  state.py (in-memory)  ←→  SQLAlchemy async (SQLite/PG)     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────── EXTERNAL TOOLS ────────────────────────────┐  │
│  │  ffmpeg/ffprobe │ faster-whisper (CTranslate2) │ pyannote    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Functional Map

### 2.1 Middleware Stack (request flows top → bottom)

Each request passes through all middleware in order. Last registered = first executed.

```
REQUEST
  │
  ▼
┌──────────────────────┐
│ GZipMiddleware        │  Compresses responses >500 bytes (gzip)
│ Role: Performance     │  Influence: All responses
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ CORSMiddleware        │  Sets Access-Control-* headers
│ Role: Browser policy  │  Influence: Cross-origin requests only
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ SecurityHeaders       │  CSP, X-Frame-Options, HSTS, nosniff
│ Role: XSS/clickjack  │  Influence: All responses (headers only)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ BodyLimitMiddleware   │  Rejects oversized request bodies
│ Role: DoS prevention  │  Influence: POST/PUT requests
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ BruteForceMiddleware  │  Tracks failed auth, blocks repeat offenders
│ Role: Auth protection │  Influence: Auth endpoints → IP blocklist
│ Depends: rate_limiter │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ SessionMiddleware     │  Creates/reads session UUID cookie
│ Role: User tracking   │  Influence: Sets request.state.session_id
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ ApiKeyMiddleware      │  Validates X-API-Key header (if API_KEYS set)
│ Role: Authentication  │  Influence: Non-public paths → 401 if invalid
│ Exempt: /, /health,   │
│   /ready, /track, ... │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ RequestLogMiddleware  │  Logs method, path, status, duration
│ Role: Observability   │  Influence: None (read-only)
└──────────┬───────────┘
           ▼
       ROUTE HANDLER
```

### 2.2 Route Layer — Functional Groups

```
┌─────────────────────────────────────────────────────────────────┐
│                      ROUTE LAYER                                │
│                                                                 │
│  ┌─── CORE WORKFLOW ────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  POST /upload ──────────── Accepts file, starts pipeline  │  │
│  │  GET  /events/{id} ─────── SSE progress stream            │  │
│  │  WS   /ws/{id} ─────────── WebSocket progress stream      │  │
│  │  GET  /progress/{id} ───── Polling fallback               │  │
│  │  GET  /download/{id} ──── Returns SRT/VTT/JSON file       │  │
│  │  POST /embed/{id} ─────── Embeds subtitles into video     │  │
│  │  POST /embed/{id}/quick ── Embeds using preserved video   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── TASK MANAGEMENT ──────────────────────────────────────┐  │
│  │                                                           │  │
│  │  GET  /tasks ──────────── List all tasks (with positions) │  │
│  │  POST /cancel/{id} ────── Cancel running task             │  │
│  │  POST /pause/{id} ─────── Pause transcription             │  │
│  │  POST /resume/{id} ────── Resume transcription            │  │
│  │  POST /tasks/{id}/retry ── Retry failed task              │  │
│  │  GET  /subtitles/{id} ─── Read/edit subtitle segments     │  │
│  │  PUT  /subtitles/{id} ─── Update subtitle text            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── HEALTH & MONITORING ──────────────────────────────────┐  │
│  │                                                           │  │
│  │  GET /health ──────────── Liveness probe (always 200)     │  │
│  │  GET /health/live ─────── Minimal liveness (load balancer)│  │
│  │  GET /ready ───────────── Readiness (disk+DB+ffmpeg)      │  │
│  │  GET /api/status ──────── Aggregate status (1s cache)     │  │
│  │  GET /health/stream ───── SSE health push (every 1s)      │  │
│  │  GET /health/db ───────── DB connectivity + latency       │  │
│  │  GET /scale/info ──────── Worker/storage/capacity info    │  │
│  │  GET /metrics ─────────── Prometheus text format           │  │
│  │  GET /monitoring/* ────── Business metrics + alerts        │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── DATA & ANALYTICS ────────────────────────────────────┐  │
│  │                                                           │  │
│  │  GET  /analytics/summary ── Counters, rates, averages     │  │
│  │  GET  /analytics/timeseries ── Per-minute metrics         │  │
│  │  GET  /analytics/daily ──── Daily aggregates              │  │
│  │  GET  /analytics/rollup ─── Weekly/monthly rollup         │  │
│  │  GET  /analytics/export ─── CSV/JSON export               │  │
│  │  POST /track ──────────── Record UI event                 │  │
│  │  GET  /tasks/search ────── Cursor-paginated search        │  │
│  │  GET  /admin/export/tasks ── Bulk task export             │  │
│  │  POST /admin/retention ── Enforce data retention          │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── AUTH & SECURITY ──────────────────────────────────────┐  │
│  │                                                           │  │
│  │  POST /auth/register ──── Create user account             │  │
│  │  POST /auth/login ─────── Authenticate → JWT tokens       │  │
│  │  POST /auth/api-keys ──── Create programmatic API key     │  │
│  │  GET  /security/audit ─── Security event log              │  │
│  │  POST /feedback ───────── User feedback (1-5 stars)       │  │
│  │  POST /webhooks/register ── Task completion callback      │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── UI PAGES ─────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  GET / ────────────────── Main app (Jinja2 template)      │  │
│  │  GET /dashboard ───────── Built-in monitoring dashboard   │  │
│  │  GET /analytics ───────── Chart.js analytics page         │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Service Layer — Roles & Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│                                                                 │
│  ┌─── PROCESSING CORE ─────────────────────────────────────┐  │
│  │                                                          │  │
│  │  pipeline.py ──────── Orchestrates full processing flow  │  │
│  │    ├── uses: transcription.py (whisper inference)        │  │
│  │    ├── uses: model_manager.py (model cache)              │  │
│  │    ├── uses: diarization.py (speaker ID, optional)       │  │
│  │    ├── uses: subtitle_embed.py (auto-embed, optional)    │  │
│  │    ├── uses: sse.py (event emission)                     │  │
│  │    ├── uses: analytics.py (record completion/failure)    │  │
│  │    ├── uses: task_backend.py (persist state)             │  │
│  │    └── uses: utils/media.py (ffprobe, ffmpeg)            │  │
│  │                                                          │  │
│  │  transcription.py ─── Whisper model inference            │  │
│  │    ├── uses: model (passed in)                           │  │
│  │    ├── uses: sse.py (segment events)                     │  │
│  │    └── checks: task["cancel_requested"]                  │  │
│  │                                                          │  │
│  │  model_manager.py ─── Thread-safe model singleton cache  │  │
│  │    └── uses: state.loaded_models, state.model_lock       │  │
│  │                                                          │  │
│  │  subtitle_embed.py ── ffmpeg soft/hard subtitle embed    │  │
│  │    └── uses: ffmpeg subprocess                           │  │
│  │                                                          │  │
│  │  diarization.py ───── pyannote speaker diarization       │  │
│  │    └── uses: pyannote.audio (optional dependency)        │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── STATE & PERSISTENCE ─────────────────────────────────┐  │
│  │                                                          │  │
│  │  sse.py ───────────── Event queue management             │  │
│  │    └── writes: state.task_event_queues[task_id]          │  │
│  │                                                          │  │
│  │  task_backend.py ──── Abstract task storage interface    │  │
│  │    └── impl: InMemoryTaskBackend (dict)                  │  │
│  │                                                          │  │
│  │  task_backend_db.py ── DB-backed task persistence        │  │
│  │    └── uses: db/engine.py → TaskRecord model             │  │
│  │                                                          │  │
│  │  storage.py ───────── File storage abstraction           │  │
│  │    └── impl: LocalStorage (future: S3)                   │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── ANALYTICS & TRACKING ────────────────────────────────┐  │
│  │                                                          │  │
│  │  analytics.py ─────── In-memory counters + ring buffer   │  │
│  │    └── writes-through: analytics_pg.py (async DB)        │  │
│  │                                                          │  │
│  │  analytics_pg.py ──── Async DB analytics queries         │  │
│  │    └── uses: db/engine.py → Analytics* models            │  │
│  │                                                          │  │
│  │  analytics_db.py ──── Legacy SQLite analytics            │  │
│  │    └── standalone sqlite3 (being replaced by PG)         │  │
│  │                                                          │  │
│  │  tracking.py ──────── UI event recording & queries       │  │
│  │    └── uses: db/engine.py → UIEvent model                │  │
│  │                                                          │  │
│  │  monitoring.py ────── Business metrics, alerts, profiling│  │
│  │    └── reads: analytics.py, state.tasks                  │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── SECURITY & AUTH ─────────────────────────────────────┐  │
│  │                                                          │  │
│  │  auth.py ──────────── User registration, JWT, API keys  │  │
│  │    └── uses: db/engine.py → UserRecord, ApiKeyRecord     │  │
│  │                                                          │  │
│  │  rate_limiter.py ──── Sliding window + IP lists          │  │
│  │    └── uses: db/engine.py → IpListEntry                  │  │
│  │                                                          │  │
│  │  audit.py ─────────── Security event logging             │  │
│  │    └── uses: db/engine.py → AuditLog                     │  │
│  │                                                          │  │
│  │  quarantine.py ────── Moves suspicious files aside       │  │
│  │    └── uses: filesystem (quarantine/ directory)           │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── INFRASTRUCTURE ──────────────────────────────────────┐  │
│  │                                                          │  │
│  │  gpu.py ───────────── GPU detection, model auto-select  │  │
│  │  system_capability.py ── CPU/RAM/codec detection        │  │
│  │  cleanup.py ────────── Periodic file retention           │  │
│  │  worker_health.py ──── Multi-instance health tracking   │  │
│  │  scaling.py ────────── MemoryCache, InMemoryTaskQueue   │  │
│  │  query_layer.py ────── Advanced DB queries, pagination  │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Database Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                │
│                                                                 │
│  Engine (app/db/engine.py)                                      │
│  ├── create_async_engine() → SQLite or PostgreSQL               │
│  ├── async_sessionmaker → session factory                       │
│  ├── get_session() → async context manager                     │
│  ├── init_db() → create all tables                             │
│  └── close_db() → dispose engine                               │
│                                                                 │
│  Models (app/db/models.py)                                      │
│  ┌──────────────────┬──────────────────────────────────────┐   │
│  │ Table             │ Role                                  │   │
│  ├──────────────────┼──────────────────────────────────────┤   │
│  │ tasks             │ Task records (status, result, meta)   │   │
│  │ sessions          │ User sessions (cookie → task link)    │   │
│  │ analytics_events  │ Per-event metrics (upload, complete)  │   │
│  │ analytics_daily   │ Daily aggregates (rollup)             │   │
│  │ analytics_ts      │ Minute-resolution time-series         │   │
│  │ audit_logs        │ Security events (login, suspicious)   │   │
│  │ feedback          │ User ratings (1-5 stars + comment)    │   │
│  │ ui_events         │ Frontend interaction tracking         │   │
│  │ users             │ User accounts (auth)                  │   │
│  │ api_keys          │ Programmatic API keys                 │   │
│  │ brute_force_events│ Failed auth attempts                  │   │
│  │ ip_lists          │ IP allowlist / blocklist               │   │
│  └──────────────────┴──────────────────────────────────────┘   │
│                                                                 │
│  Migrations (alembic/versions/)                                 │
│  001 → tasks, sessions                                          │
│  002 → analytics_events, analytics_daily, analytics_ts,         │
│         audit_logs, feedback                                    │
│  003 → ui_events                                                │
│  004 → users, api_keys                                          │
│  005 → brute_force_events, ip_lists                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    STATE (app/state.py)                          │
│                    In-memory, single-process                    │
│                                                                 │
│  tasks: dict[str, dict]                                         │
│  ├── task_id → {status, percent, message, filename, ...}        │
│  ├── Written by: pipeline.py, upload.py, control.py             │
│  ├── Read by: events.py, progress.py, tasks.py, health.py       │
│  └── Persisted to: DB via task_backend_db.py                    │
│                                                                 │
│  loaded_models: dict[(model_size, device), WhisperModel]        │
│  ├── Written by: model_manager.py (thread-safe via model_lock)  │
│  ├── Read by: pipeline.py → transcription.py                    │
│  └── Never persisted (loaded on demand)                         │
│                                                                 │
│  task_event_queues: dict[str, queue.Queue]                      │
│  ├── Written by: sse.py (emit_event)                            │
│  ├── Read by: events.py (SSE), ws.py (WebSocket)                │
│  └── Never persisted (ephemeral)                                │
│                                                                 │
│  shutting_down: bool                                            │
│  ├── Set by: lifespan shutdown handler                          │
│  ├── Checked by: upload.py (reject new), health.py (not ready)  │
│  └── Displayed: frontend service banner                         │
│                                                                 │
│  main_event_loop: asyncio.AbstractEventLoop                     │
│  ├── Captured at: startup (lifespan)                            │
│  └── Used by: pipeline thread → schedule async DB writes        │
│                                                                 │
│  _task_semaphore: threading.Semaphore(MAX_CONCURRENT_TASKS)     │
│  ├── Acquired by: pipeline.py (start of processing)             │
│  └── Released by: pipeline.py (end of processing)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Logical Workflows

### 3.1 Upload → Transcription → Download (Primary Flow)

```
USER                    FRONTEND (JS)              BACKEND                        EXTERNAL
 │                         │                          │                              │
 │  Select file            │                          │                              │
 │  Set options            │                          │                              │
 │  Click Upload           │                          │                              │
 │ ───────────────────────▶│                          │                              │
 │                         │                          │                              │
 │                         │  POST /upload            │                              │
 │                         │  (multipart form-data)   │                              │
 │                         │ ────────────────────────▶│                              │
 │                         │                          │                              │
 │                         │                          │ ┌─── VALIDATION ───────────┐ │
 │                         │                          │ │ 1. Check shutting_down    │ │
 │                         │                          │ │ 2. Check DB health ◄─────┼─┤ DB
 │                         │                          │ │    (REJECT if down)       │ │
 │                         │                          │ │ 3. Validate extension     │ │
 │                         │                          │ │ 4. Check device (cuda?)   │ │
 │                         │                          │ │ 5. Auto-select model      │ │
 │                         │                          │ │ 6. Check concurrent limit │ │
 │                         │                          │ │ 7. Stream file to disk    │ │
 │                         │                          │ │ 8. Check file size limits │ │
 │                         │                          │ │ 9. Validate magic bytes   │ │
 │                         │                          │ └──────────────────────────┘ │
 │                         │                          │                              │
 │                         │                          │  Create task in state.tasks   │
 │                         │                          │  Persist to DB ──────────────▶│ DB
 │                         │                          │  Spawn background thread      │
 │                         │                          │                              │
 │                         │  {task_id, model, ...}   │                              │
 │                         │ ◄────────────────────────│                              │
 │                         │                          │                              │
 │                         │  GET /events/{task_id}   │                              │
 │                         │  (SSE connection)        │                              │
 │                         │ ════════════════════════▶│                              │
 │                         │                          │                              │
 │                         │                          │ ┌─── PIPELINE THREAD ──────┐ │
 │                         │                          │ │                           │ │
 │                         │  SSE: status=probing     │ │ 1. Acquire semaphore      │ │
 │                         │ ◄════════════════════════│ │ 2. Probe file (ffprobe) ──┼▶│ ffprobe
 │  Update UI: "Probing"   │                          │ │    → duration, codecs     │ │
 │ ◄───────────────────────│                          │ │                           │ │
 │                         │  SSE: status=extracting  │ │ 3. Extract audio ─────────┼▶│ ffmpeg
 │                         │ ◄════════════════════════│ │    → WAV file             │ │
 │  Update UI: "Extracting"│                          │ │                           │ │
 │ ◄───────────────────────│                          │ │ 4. Load/cache model ──────┼▶│ whisper
 │                         │  SSE: status=transcribing│ │                           │ │
 │                         │ ◄════════════════════════│ │ 5. Transcribe ────────────┼▶│ whisper
 │                         │                          │ │    (emits segment events) │ │
 │                         │  SSE: segment data ×N    │ │    ↕ check cancel_req     │ │
 │                         │ ◄════════════════════════│ │    ↕ check pause_event    │ │
 │  Show live subtitles    │                          │ │                           │ │
 │ ◄───────────────────────│                          │ │ 6. Diarize (optional) ────┼▶│ pyannote
 │                         │                          │ │                           │ │
 │                         │  SSE: status=formatting  │ │ 7. Format + line-break    │ │
 │                         │ ◄════════════════════════│ │                           │ │
 │                         │                          │ │ 8. Write SRT/VTT/JSON     │ │
 │                         │                          │ │                           │ │
 │                         │                          │ │ 9. Auto-embed (optional) ─┼▶│ ffmpeg
 │                         │                          │ │                           │ │
 │                         │                          │ │ 10. Record analytics ─────┼▶│ DB
 │                         │                          │ │     Persist final state   │ │
 │                         │                          │ │ 11. Release semaphore     │ │
 │                         │                          │ └───────────────────────────┘ │
 │                         │                          │                              │
 │                         │  SSE: status=done        │                              │
 │                         │  {is_video, step_timing} │                              │
 │                         │ ◄════════════════════════│                              │
 │                         │                          │                              │
 │  Show download buttons  │                          │                              │
 │  Show timing summary    │                          │                              │
 │  Show embed card (video)│                          │                              │
 │ ◄───────────────────────│                          │                              │
 │                         │                          │                              │
 │  Click "Download SRT"   │                          │                              │
 │ ───────────────────────▶│                          │                              │
 │                         │  GET /download/{id}      │                              │
 │                         │  ?format=srt             │                              │
 │                         │ ────────────────────────▶│                              │
 │                         │  FileResponse (.srt)     │                              │
 │                         │ ◄────────────────────────│                              │
 │  Save file              │                          │                              │
 │ ◄───────────────────────│                          │                              │
```

### 3.2 Quick Embed (Post-Transcription, No Re-upload)

```
USER                    FRONTEND (JS)              BACKEND
 │                         │                          │
 │  (Task completed,       │                          │
 │   video was preserved)  │                          │
 │                         │                          │
 │  Select mode: soft/hard │                          │
 │  Select preset          │                          │
 │  Click "Embed Now"      │                          │
 │ ───────────────────────▶│                          │
 │                         │  POST /embed/{id}/quick  │
 │                         │  {mode, preset}          │
 │                         │ ────────────────────────▶│
 │                         │                          │  Validate:
 │                         │                          │  - task exists & done
 │                         │                          │  - preserved video exists
 │                         │                          │  - SRT file exists
 │                         │                          │
 │                         │  SSE: embed_progress     │  Spawn embed thread
 │                         │ ◄════════════════════════│  → ffmpeg mux/burn
 │  Show embed progress    │                          │
 │ ◄───────────────────────│                          │
 │                         │  SSE: embed_done         │  Clean up preserved video
 │                         │  {output_path}           │
 │                         │ ◄════════════════════════│
 │  Show download link     │                          │
 │ ◄───────────────────────│                          │
```

### 3.3 Real-Time Health Monitoring

```
FRONTEND                          BACKEND                    SYSTEMS
   │                                 │                          │
   │  connectHealthSSE()             │                          │
   │  GET /health/stream (SSE)       │                          │
   │ ════════════════════════════════▶│                          │
   │                                 │                          │
   │                          ┌──────┴──────┐                   │
   │                          │ Every 1 sec │                   │
   │                          └──────┬──────┘                   │
   │                                 │                          │
   │                                 │  Check DB health ───────▶│ DB
   │                                 │  Check disk space ──────▶│ FS
   │                                 │  Check ffmpeg ──────────▶│ PATH
   │                                 │  Check CPU/memory ──────▶│ psutil
   │                                 │  Count active tasks      │
   │                                 │  Check alerts            │
   │                                 │  Check shutdown state    │
   │                                 │                          │
   │  SSE: health data JSON          │                          │
   │ ◄══════════════════════════════│                          │
   │                                 │                          │
   │  applyHealthData():             │                          │
   │  ├── Update dot color           │                          │
   │  │   green = healthy            │                          │
   │  │   yellow = warning           │                          │
   │  │   red = critical             │                          │
   │  │   gray = offline             │                          │
   │  ├── Update CPU load bar        │                          │
   │  ├── Update memory gauge        │                          │
   │  ├── Update DB latency badge    │                          │
   │  ├── Show/hide service banner   │                          │
   │  └── Enable/disable dropzone    │                          │
   │                                 │                          │
   │  ┌─── FALLBACK ──────────────┐  │                          │
   │  │ If SSE disconnects:        │  │                          │
   │  │ 1. Watchdog (4s timeout)   │  │                          │
   │  │ 2. Switch to polling       │  │                          │
   │  │    GET /api/status (1s)    │  │                          │
   │  │ 3. Retry SSE after 5s     │  │                          │
   │  └────────────────────────────┘  │                          │
```

### 3.4 Concurrency Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     UVICORN (single worker)                     │
│                                                                 │
│  ┌─── MAIN ASYNCIO EVENT LOOP ──────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ HTTP       │  │ SSE        │  │ WebSocket          │  │  │
│  │  │ Handlers   │  │ Streams    │  │ Connections        │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ DB Queries │  │ Health SSE │  │ Background Tasks   │  │  │
│  │  │ (async)    │  │ (1s push)  │  │ (cleanup, etc.)    │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  │                                                           │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                               │                                  │
│                    asyncio.to_thread()                            │
│                               │                                  │
│  ┌─── THREAD POOL ───────────┼──────────────────────────────┐  │
│  │                            ▼                              │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         Semaphore (MAX_CONCURRENT_TASKS=3)       │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │           │                │                │             │  │
│  │  ┌────────┴──────┐ ┌──────┴────────┐ ┌─────┴──────────┐ │  │
│  │  │ Pipeline      │ │ Pipeline      │ │ Pipeline       │ │  │
│  │  │ Thread 1      │ │ Thread 2      │ │ Thread 3       │ │  │
│  │  │               │ │               │ │                │ │  │
│  │  │ ffprobe       │ │ ffprobe       │ │ ffprobe        │ │  │
│  │  │ ffmpeg        │ │ ffmpeg        │ │ ffmpeg         │ │  │
│  │  │ whisper       │ │ whisper       │ │ whisper        │ │  │
│  │  │               │ │               │ │                │ │  │
│  │  │ emit_event()──┼─┼───────────────┼─┼──▶ SSE queue   │ │  │
│  │  │ persist_db()──┼─┼───────────────┼─┼──▶ async loop  │ │  │
│  │  └───────────────┘ └───────────────┘ └────────────────┘ │  │
│  │                                                          │  │
│  │  Thread→Async bridge: asyncio.run_coroutine_threadsafe() │  │
│  │  Uses: state.main_event_loop (captured at startup)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── SHARED STATE (thread-safe) ───────────────────────────┐  │
│  │  state.tasks[task_id]     ── dict (GIL-protected)         │  │
│  │  state.loaded_models      ── threading.Lock                │  │
│  │  state.task_event_queues  ── queue.Queue (thread-safe)     │  │
│  │  state._task_semaphore    ── threading.Semaphore            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 Data Persistence Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   WRITE-THROUGH ARCHITECTURE                    │
│                                                                 │
│  ┌─── HOT PATH (fast reads) ────────────────────────────────┐  │
│  │                                                           │  │
│  │  state.tasks              → task status, progress         │  │
│  │  analytics counters       → upload/completion counts      │  │
│  │  analytics ring buffer    → 24h minute-resolution data    │  │
│  │  rate limiter windows     → per-IP request counts         │  │
│  │                                                           │  │
│  │  All reads serve from memory (zero DB latency)            │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│                    write-through                                 │
│                    (async, mandatory)                             │
│                           │                                      │
│  ┌─── COLD PATH (durable) ┼──────────────────────────────────┐  │
│  │                         ▼                                  │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │               DATABASE (SQLite / PostgreSQL)          │ │  │
│  │  │                                                       │ │  │
│  │  │  TaskRecord ←──── task state on every status change   │ │  │
│  │  │  AnalyticsEvent ← on upload, completion, failure      │ │  │
│  │  │  AnalyticsDaily ── daily aggregation                  │ │  │
│  │  │  AuditLog ←─────── on security events                 │ │  │
│  │  │  UIEvent ←──────── on frontend interactions           │ │  │
│  │  │  Feedback ←─────── on user feedback                   │ │  │
│  │  │  UserRecord ←───── on registration                    │ │  │
│  │  │  ApiKeyRecord ←─── on key creation                    │ │  │
│  │  │  BruteForceEvent ── on failed auth                    │ │  │
│  │  │  IpListEntry ←──── on IP list changes                 │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  CRITICAL RULE: If DB is down:                            │  │
│  │  • Upload is REJECTED (503)                               │  │
│  │  • /ready returns 503                                     │  │
│  │  • UI shows service unavailable banner                    │  │
│  │  • Dropzone is disabled                                   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── FILE STORAGE ─────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  uploads/   → {task_id}.{ext}   (uploaded media files)    │  │
│  │  outputs/   → {task_id}.srt     (generated subtitles)     │  │
│  │               {task_id}.vtt                                │  │
│  │               {task_id}.json                               │  │
│  │               {task_id}_embedded.{ext} (embedded video)   │  │
│  │  logs/      → app.log, app.jsonl, task_events.jsonl       │  │
│  │                                                           │  │
│  │  Retention: FILE_RETENTION_HOURS (default 24h)            │  │
│  │  Cleanup: periodic_cleanup() background task              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Influence Matrix

Shows how each component affects others. Read as "row influences column."

```
                        │ Upload │Pipeline│Health │ SSE  │  DB  │ State │ UI
────────────────────────┼────────┼────────┼───────┼──────┼──────┼───────┼─────
Middleware.Auth         │ block  │   —    │ exempt│  —   │ read │   —   │  —
Middleware.RateLimit    │ limit  │   —    │ exempt│  —   │ read │   —   │ 429
Middleware.BruteForce   │ block  │   —    │   —   │  —   │write │   —   │  —
Middleware.Session      │  tag   │   —    │   —   │  —   │write │   —   │  —
────────────────────────┼────────┼────────┼───────┼──────┼──────┼───────┼─────
Route.upload            │   —    │ spawn  │   —   │create│write │write  │  —
Route.events            │   —    │   —    │   —   │ read │  —   │ read  │push
Route.health            │   —    │   —    │   —   │  —   │ read │ read  │push
Route.download          │   —    │   —    │   —   │  —   │  —   │ read  │file
Route.embed             │   —    │   —    │   —   │write │  —   │write  │push
Route.control           │   —    │ signal │   —   │  —   │  —   │write  │  —
────────────────────────┼────────┼────────┼───────┼──────┼──────┼───────┼─────
Service.pipeline        │   —    │   —    │   —   │write │write │write  │  —
Service.transcription   │   —    │output  │   —   │write │  —   │ read  │  —
Service.model_manager   │   —    │provide │   —   │  —   │  —   │write  │  —
Service.analytics       │   —    │   —    │source │  —   │write │  —    │  —
Service.monitoring      │   —    │   —    │source │  —   │ read │ read  │  —
Service.sse             │   —    │   —    │   —   │write │  —   │write  │  —
Service.task_backend_db │   —    │   —    │   —   │  —   │write │  —    │  —
Service.query_layer     │   —    │   —    │check  │  —   │ read │  —    │  —
────────────────────────┼────────┼────────┼───────┼──────┼──────┼───────┼─────
DB (PostgreSQL/SQLite)  │ gate   │   —    │ gate  │  —   │  —   │  —    │banner
────────────────────────┼────────┼────────┼───────┼──────┼──────┼───────┼─────
ffmpeg/ffprobe          │   —    │ tool   │check  │  —   │  —   │  —    │  —
faster-whisper          │   —    │ tool   │   —   │  —   │  —   │  —    │  —
psutil                  │   —    │   —    │source │  —   │  —   │  —    │gauge
```

**Legend**: block=can reject, gate=required, spawn=creates, signal=modifies behavior, source=provides data, push=streams to, write/read=data access

---

## 5. Startup Sequence

```
main.py
  │
  ▼
uvicorn.run(app)
  │
  ▼
create_app() → FastAPI instance
  │
  ├── Register middleware (8 layers)
  ├── Register routes (22 routers)
  ├── Register exception handlers
  │
  ▼
lifespan startup
  │
  ├── 1. Create directories (uploads/, outputs/, logs/)
  ├── 2. init_db() → create DB tables
  ├── 3. Capture main_event_loop
  ├── 4. detect_system_capabilities() → auto-tune OMP_THREADS, MAX_TASKS
  ├── 5. Load task history from DB
  ├── 6. Load analytics snapshots
  ├── 7. Register worker (worker_health)
  ├── 8. Preload model (if PRELOAD_MODEL set)
  └── 9. Start periodic_cleanup() background task

  ... serving requests ...

lifespan shutdown
  │
  ├── 1. Set state.shutting_down = True
  ├── 2. Drain in-flight tasks (max 60s)
  ├── 3. Persist final task states
  ├── 4. Save analytics snapshots
  ├── 5. Close legacy SQLite
  └── 6. Close async DB engine
```

---

## 6. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
│                                                                 │
│  Layer 1: Network                                               │
│  ├── Rate limiting (60 req/min general, 5 req/min uploads)      │
│  ├── IP allowlist/blocklist                                     │
│  ├── Body size limits                                           │
│  └── Brute force protection (auto-block after N failures)       │
│                                                                 │
│  Layer 2: Authentication                                        │
│  ├── API key auth (X-API-Key header, optional)                  │
│  ├── JWT tokens (register/login flow)                           │
│  ├── Session cookies (httponly, secure)                          │
│  └── Public paths whitelist                                     │
│                                                                 │
│  Layer 3: Input Validation                                      │
│  ├── File extension whitelist                                   │
│  ├── Magic bytes verification (actual content check)            │
│  ├── File size limits (min 1KB, max 2GB)                        │
│  ├── Filename sanitization (path traversal prevention)          │
│  ├── Path traversal prevention (safe_path())                    │
│  ├── Subtitle text sanitization (XSS prevention)               │
│  └── FFmpeg filter value validation (injection prevention)      │
│                                                                 │
│  Layer 4: Response Security                                     │
│  ├── Content-Security-Policy (with nonce)                       │
│  ├── X-Frame-Options: DENY                                      │
│  ├── X-Content-Type-Options: nosniff                            │
│  ├── HSTS (optional)                                            │
│  └── CORS origin whitelist                                      │
│                                                                 │
│  Layer 5: Audit & Monitoring                                    │
│  ├── Security event logging (AuditLog table)                    │
│  ├── Signed audit entries (tamper detection)                    │
│  ├── Suspicious file quarantine                                 │
│  ├── SSRF protection (webhook URL validation)                   │
│  └── Alert rules (CPU, memory, error rate thresholds)           │
│                                                                 │
│  Layer 6: Data Integrity                                        │
│  ├── DB health gate (upload rejected if DB down)                │
│  ├── Checksum computation/verification                          │
│  └── Error message sanitization (no internal details leaked)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Dependency Flow

```
             config.py (constants, env vars — no heavy imports)
               │
     +---------+---------+
     |         |         |
   utils/   logging   state.py
  (pure)   _setup.py  (dicts, locks, semaphore)
     |         |         |
     +----+----+----+----+
          |         |
       services/  middleware/
       (business   (HTTP interceptors,
        logic)      8 layers)
          |         |
          +----+----+
               |
            routes/
            (22 routers, thin delegation)
               |
          app/main.py
          (app factory, lifespan)
               |
            main.py
            (entry point, uvicorn)
```

**Rule**: Arrows point downward only. `utils/` never imports from `services/` or `routes/`. `routes/` never imports from other `routes/`.

---

## 8. File Map

```
subtitle-generator/
├── main.py                          # Entry point (uvicorn)
├── CLAUDE.md                        # AI assistant instructions
├── docs/
│   ├── ARCHITECTURE.md              # This document
│   ├── ROADMAP.md                   # Sprint history
│   ├── DEPLOY.md                    # Production deployment guide
│   ├── PRODUCT_STRATEGY.md          # Product strategy
│   └── CODING_STANDARDS.md          # Coding standards and frontend architecture
├── docker-compose.yml               # Docker orchestration
├── Dockerfile                       # Container build
├── requirements.txt                 # Python dependencies
│
├── app/
│   ├── main.py                      # FastAPI app factory + lifespan
│   ├── config.py                    # All configuration constants
│   ├── state.py                     # Global in-memory state
│   ├── logging_setup.py             # Structured logging configuration
│   │
│   ├── routes/                      # 22 FastAPI routers
│   │   ├── __init__.py              # Router aggregator
│   │   ├── pages.py                 # GET / (main page)
│   │   ├── upload.py                # POST /upload
│   │   ├── events.py                # GET /events/{id} (SSE)
│   │   ├── download.py              # GET /download/{id}
│   │   ├── embed.py                 # POST /embed/{id}, /embed/{id}/quick
│   │   ├── tasks.py                 # GET /tasks, retry, duplicates
│   │   ├── control.py               # POST /cancel, /pause, /resume
│   │   ├── subtitles.py             # GET/PUT /subtitles/{id}
│   │   ├── health.py                # /health, /ready, /api/status, /health/stream
│   │   ├── metrics.py               # GET /metrics (Prometheus)
│   │   ├── ws.py                    # WS /ws/{id}
│   │   ├── system.py                # GET /system-info, /languages
│   │   ├── feedback.py              # POST /feedback
│   │   ├── analytics.py             # GET /analytics/*
│   │   ├── analytics_page.py        # GET /analytics (Chart.js page)
│   │   ├── tracking.py              # POST /track, GET /analytics/activity
│   │   ├── auth.py                  # POST /auth/register|login|logout
│   │   ├── query.py                 # GET /tasks/search, /analytics/rollup
│   │   ├── monitoring.py            # GET /monitoring/metrics|alerts
│   │   ├── logs.py                  # GET /logs/recent
│   │   ├── admin_logs.py            # GET /admin/logs
│   │   ├── export.py                # GET /export/bulk, POST /share
│   │   ├── security.py              # GET /security/audit
│   │   ├── webhooks.py              # POST /webhooks/register
│   │   └── dashboard.py             # GET /dashboard
│   │
│   ├── services/                    # 26 business logic modules
│   │   ├── pipeline.py              # Main processing orchestration
│   │   ├── transcription.py         # Whisper inference
│   │   ├── model_manager.py         # Model caching
│   │   ├── diarization.py           # Speaker identification
│   │   ├── subtitle_embed.py        # ffmpeg embed (soft/hard)
│   │   ├── sse.py                   # Event queue management
│   │   ├── task_backend.py          # Abstract task storage
│   │   ├── task_backend_db.py       # DB task persistence
│   │   ├── storage.py               # File storage abstraction
│   │   ├── analytics.py             # In-memory analytics
│   │   ├── analytics_pg.py          # Async DB analytics
│   │   ├── analytics_db.py          # Legacy SQLite analytics
│   │   ├── tracking.py              # UI event tracking
│   │   ├── monitoring.py            # Business metrics & alerts
│   │   ├── query_layer.py           # Advanced queries, pagination
│   │   ├── auth.py                  # User auth, JWT, API keys
│   │   ├── rate_limiter.py          # Sliding window rate limiter
│   │   ├── audit.py                 # Security audit logging
│   │   ├── quarantine.py            # Suspicious file handling
│   │   ├── gpu.py                   # GPU detection, model selection
│   │   ├── system_capability.py     # System auto-tuning
│   │   ├── cleanup.py               # Periodic file cleanup
│   │   ├── worker_health.py         # Multi-instance health
│   │   ├── scaling.py               # MemoryCache, task queue
│   │   └── translation.py          # Language translation
│   │
│   ├── middleware/                   # 8 middleware modules
│   │   ├── auth.py                  # API key validation
│   │   ├── brute_force.py           # Brute force protection
│   │   ├── rate_limit.py            # Per-IP rate limiting
│   │   ├── session.py               # Session cookie
│   │   ├── security.py              # Security headers (CSP, etc.)
│   │   ├── cors.py                  # CORS configuration
│   │   ├── compression.py           # GZip compression
│   │   └── request_log.py           # Request logging
│   │
│   ├── db/                          # Database layer
│   │   ├── engine.py                # Async SQLAlchemy setup
│   │   ├── models.py                # 12 ORM models
│   │   └── task_backend_db.py       # DB-backed task state
│   │
│   └── utils/                       # Utility functions
│       ├── security.py              # File validation, sanitization
│       ├── security_infra.py        # CSP nonce, SRI hash, HSTS
│       ├── validation.py            # Path safety, checksums
│       ├── srt.py                   # SRT/VTT/JSON generation
│       ├── formatting.py            # Bytes, timestamps, display
│       ├── media.py                 # ffprobe, ffmpeg, audio extract
│       └── subtitle_format.py       # Line-breaking, timing validation
│
├── templates/
│   └── index.html                   # Single-page app (CSS + HTML + JS)
│
├── tests/                           # 1166 tests
│   ├── conftest.py                  # Mocks (torch, whisper, psutil)
│   ├── test_api.py                  # Core API tests
│   ├── test_security.py             # Security tests
│   ├── test_srt.py                  # Subtitle format tests
│   ├── test_formatting.py           # Formatting utility tests
│   └── test_sprint{1-30}.py         # Sprint-organized tests
│
├── alembic/                         # Database migrations
│   └── versions/
│       ├── 001_initial_tables.py
│       ├── 002_analytics_audit.py
│       ├── 003_ui_events.py
│       ├── 004_users_api_keys.py
│       └── 005_rate_limiting.py
│
├── uploads/                         # Uploaded media files
├── outputs/                         # Generated subtitle files
└── logs/                            # Application logs
```

---

## 9. Key Design Decisions

| # | Decision | Rationale | Trade-off |
|---|----------|-----------|-----------|
| 1 | Single uvicorn worker | Whisper model not multi-worker safe | Limits horizontal scaling per instance |
| 2 | In-memory + write-through | Zero-latency reads for progress/status | DB is mandatory — 503 if unreachable |
| 3 | Thread pool for pipeline | ffmpeg/whisper are blocking I/O | Semaphore limits concurrency to 3 |
| 4 | SSE over WebSocket for health | Simpler, auto-reconnect, HTTP/2 compatible | One-directional only |
| 5 | Polling fallback for health | SSE may fail (proxy, firewall) | Slightly higher latency |
| 6 | Video preservation for embed | Avoids re-upload of same file | Uses disk space until cleanup |
| 7 | Session cookies (not JWT) | Simple, works without registration | No cross-device session |
| 8 | Optional API key auth | Easy to deploy without auth setup | Security depends on deployment |
| 9 | SQLite default, PG optional | Zero-config development | SQLite limited for production |
| 10 | config.py imported first | Sets OMP_NUM_THREADS before torch import | Must maintain import order |
| 11 | utils/ are pure | Zero state dependencies, testable without mocks | Cannot access app state |
| 12 | Structured JSON logging | Machine-parseable for ELK/Grafana/Loki | Larger log files |

---

## 10. Performance Stack

| Technique | Impact |
|-----------|--------|
| faster-whisper (CTranslate2) | 4-8x faster than openai-whisper |
| int8_float16 quantization | 50% VRAM reduction, large model fits 8GB GPU |
| VAD filtering (Silero) | Skips silence, 40-75% less audio to process |
| Model caching (singleton) | Eliminates 5-15s reload per request |
| OMP_NUM_THREADS auto-tuning | Optimal thread count based on physical cores |
| Auto model selection | Picks largest model that fits VRAM/RAM |
| 1s health cache TTL | Real-time sensitivity without redundant system calls |
| Write-through analytics | Hot reads from memory, cold persistence to DB |

---

## 11. Observability

| Feature | Endpoint/File | Purpose |
|---------|---------------|---------|
| Liveness probe | `GET /health` | Is the process alive? |
| Readiness probe | `GET /ready` | Can it accept work? (disk+DB+ffmpeg) |
| Health SSE stream | `GET /health/stream` | Real-time push every 1s |
| Aggregate status | `GET /api/status` | Frontend health indicator (1s cache) |
| Prometheus metrics | `GET /metrics` | Scrape for Prometheus/Grafana |
| Business metrics | `GET /monitoring/metrics` | Uploads/hr, success rate, percentiles |
| Active alerts | `GET /monitoring/alerts` | CPU, memory, error rate thresholds |
| Structured logs | `logs/app.jsonl` | Machine-parseable for ELK/Loki |
| Task event log | `logs/task_events.jsonl` | Per-task lifecycle events |
| Request ID tracing | `X-Request-ID` header | End-to-end request correlation |
| DB health check | `GET /health/db` | Connectivity + latency measurement |
| Dashboard | `GET /dashboard` | Built-in monitoring UI |

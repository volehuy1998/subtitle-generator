# SubForge — AI Subtitle Generator

AI-powered subtitle generation service. Upload audio/video, transcribe with faster-whisper (CTranslate2), download SRT/VTT/JSON. Real-time progress via SSE/WebSocket.

**Live demo**: [https://openlabs.club](https://openlabs.club)

## Features

- **99 languages** with automatic detection
- **5 Whisper model sizes** (tiny → large) with GPU/CPU comparison table
- **GPU acceleration** — auto-detects CUDA; header badge shows GPU name and VRAM
- **Speaker diarization** (who said what, via pyannote)
- **Subtitle embedding** — soft mux (MKV/MP4) or hard-burn with custom styling
- **Real-time progress** via SSE, WebSocket, or polling
- **Analytics dashboard** with charts and data export
- **Public status page** at `/status` with component health and incident tracking
- **Security page** at `/security` with live OWASP assertion results
- **Multiple output formats** — SRT, VTT, JSON
- **API + Web UI** — Swagger docs at `/docs`

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env        # edit as needed

# 2. Start (CPU mode)
docker compose --profile cpu up --build -d

# 3. Start (GPU mode — requires NVIDIA Container Toolkit)
docker compose --profile gpu up --build -d

# Web UI:  http://localhost:8000
# API docs: http://localhost:8000/docs
# Status:   http://localhost:8000/status
```

## Local Development

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** (for frontend dev)
- **ffmpeg** on PATH ([install guide](https://ffmpeg.org/download.html))
- **PostgreSQL 16+** (optional, SQLite used by default)

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing

# Install and build frontend
cd frontend && npm install && npm run build && cd ..

# Create directories
mkdir -p uploads outputs logs

# Copy environment config
cp .env.example .env

# Start the server (development — plain HTTP, no HSTS)
python main.py
```

The server starts at `http://localhost:8000`.

### Frontend Development (hot-reload)

```bash
cd frontend
npm install
npm run dev       # Vite dev server at http://localhost:5173 (proxies to :8000)
```

### Using the Makefile

```bash
make help          # show all commands
make setup         # install deps + create dirs
make dev           # run with hot-reload
make test          # run all tests
make lint          # run ruff linter
make docker-up     # start Docker (CPU)
make docker-down   # stop Docker
make health        # check if service is running
```

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` (HTTP) or `prod` (HTTPS + HSTS) | `dev` |
| `SSL_CERTFILE` | TLS certificate path (prod mode) | empty |
| `SSL_KEYFILE` | TLS private key path (prod mode) | empty |
| `DATABASE_URL` | Database connection string | SQLite |
| `API_KEYS` | Comma-separated API keys (empty = no auth) | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup | empty |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | 24 |
| `ENABLE_COMPRESSION` | GZip response compression | true |
| `MAX_CONCURRENT_TASKS` | Max parallel transcriptions | auto-detected |

## API Documentation

Interactive API docs:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload file and start transcription |
| `GET` | `/progress/{task_id}` | Poll task progress |
| `GET` | `/events/{task_id}` | SSE stream for real-time progress |
| `WS` | `/ws` | WebSocket for real-time updates |
| `GET` | `/download/{task_id}/{format}` | Download subtitles (srt/vtt/json) |
| `GET` | `/health` | Health check |
| `GET` | `/health/stream` | SSE stream of live system metrics |
| `GET` | `/api/status/page` | Status page component data |
| `GET` | `/api/security/assertions` | Live OWASP security assertion results |
| `GET` | `/metrics` | Prometheus-compatible metrics |

### Authentication

Set `API_KEYS=key1,key2` to enable. Pass via `X-API-Key: your-key` header or `?api_key=your-key` query param.

## Architecture

```
Upload → ffprobe (probe) → ffmpeg (extract WAV)
       → faster-whisper (transcribe) → optional pyannote (diarize)
       → format (line-breaking) → write SRT/VTT/JSON
```

Each step emits SSE events for real-time UI updates. Tasks run in background threads with configurable concurrency limits. Models are cached in memory across requests.

### Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite 6 + Tailwind CSS v4 + Zustand |
| Backend | FastAPI + Uvicorn (single worker) |
| Transcription | faster-whisper (CTranslate2), GPU via CUDA |
| Diarization | pyannote.audio (optional) |
| Database | PostgreSQL 16 (prod) / SQLite (dev) |
| Task queue | In-memory semaphore / Celery + Redis (distributed) |
| Media processing | ffmpeg, ffprobe |
| Auth | API key middleware (optional) |

### Module Layout

```
app/
  routes/        # 29 FastAPI routers (one per feature domain)
  services/      # Business logic: pipeline, transcription, model_manager, analytics
  middleware/    # Auth, security headers, brute-force, rate-limit, CORS, compression
  utils/         # SRT/VTT generation, line-breaking, media probing, file validation
  config.py      # All constants, paths, env vars, limits
  state.py       # Global in-memory state: tasks, model cache, semaphore

frontend/
  src/
    pages/       # App, Status, Security, About, Contact
    components/  # TranscribeForm, EmbedTab, HealthPanel, AppHeader, ConnectionBanner
    hooks/       # useHealthStream, useSSE, useTaskProgress
    store/       # uiStore (Zustand)
    api/         # types.ts, API client helpers
```

### Deployment Modes

| Mode | Description |
|------|-------------|
| `--profile cpu` | Single-node, CPU-only |
| `--profile gpu` | Single-node, NVIDIA GPU |
| `--profile distributed` | API + Celery workers + Redis + nginx |

See [docs/DEPLOY.md](docs/DEPLOY.md) for full production deployment instructions (TLS, firewall, auto-renew certs).

## Testing

```bash
# Run all tests (1328 tests)
pytest tests/ -v --tb=short

# Run a specific test file
pytest tests/test_sprint18.py -v

# Run a single test
pytest tests/test_api.py::test_health_endpoint -v

# Lint
ruff check . --select E,F,W --ignore E501

# E2E tests (requires running server + Playwright)
pytest tests/e2e/ -v
```

## Security

The `/security` page shows live OWASP assertion results. Security commits automatically update `data/security_assertions.json` via a git post-commit hook. See [SECURITY.md](SECURITY.md) for the vulnerability disclosure policy.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and PR process. See [docs/TEAM.md](docs/TEAM.md) for the engineering team structure. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## License

All rights reserved. See [LICENSE](LICENSE) for details.

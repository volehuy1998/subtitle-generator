# SubForge

[![CI](https://github.com/volehuy1998/subtitle-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/volehuy1998/subtitle-generator/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-2.5.0-blue)](https://github.com/volehuy1998/subtitle-generator/releases)
[![License](https://img.shields.io/badge/license-proprietary-red)](LICENSE)

AI-powered subtitle generation. Upload audio or video, transcribe with faster-whisper (CTranslate2), and download subtitles in SRT, VTT, or JSON. Supports translation, speaker diarization, subtitle embedding, and real-time progress tracking.

**Live**: [openlabs.club](https://openlabs.club)

## Features

- **Transcription** -- 99 languages, automatic detection, 5 model sizes (tiny to large), GPU acceleration
- **Translation** -- Whisper built-in (any to English) + Argos Translate (any to any, offline)
- **Speaker diarization** -- identify speakers via pyannote
- **Subtitle embedding** -- soft mux (fast, no re-encode) or hard burn (permanent, styled)
- **Real-time progress** -- SSE, WebSocket, and polling with per-stage timing
- **Analytics dashboard** -- processing trends, language distribution, data export
- **Status page** -- component health monitoring with auto-incident detection
- **API + Web UI** -- Swagger docs at `/docs`, React SPA frontend

## Quick Start

### Docker

```bash
cp .env.example .env                    # configure as needed
./scripts/deploy-profile.sh cpu         # start (CPU)
# GPU: docker compose --profile gpu up --build -d
```

### Local Development

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt     # testing deps
cd frontend && npm install && npm run build && cd ..
mkdir -p uploads outputs logs
cp .env.example .env
python main.py                          # http://localhost:8000
```

Frontend hot-reload: `cd frontend && npm run dev` (proxies to `:8000`)

### Makefile

```bash
make dev           # run with hot-reload
make test          # all tests
make lint          # ruff + eslint + tsc
make docker-up     # start Docker (CPU)
make ci-fast       # presubmit: lint + fast tests
```

## Architecture

```
Upload --> ffprobe --> ffmpeg (WAV) --> faster-whisper --> [diarize] --> [translate]
       --> format (line-breaking) --> write SRT/VTT/JSON --> [embed]
```

Each step emits SSE events. Tasks run in background threads with configurable concurrency.

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite 6, Tailwind CSS v4, Zustand |
| Backend | FastAPI, Uvicorn, Python 3.12 |
| Transcription | faster-whisper (CTranslate2), CUDA optional |
| Database | PostgreSQL 16 (prod) / SQLite (dev) |
| Task queue | In-memory semaphore / Celery + Redis (distributed) |

### Module Layout

```
app/
  routes/       30 FastAPI routers
  services/     32 service modules (pipeline, transcription, model_manager, ...)
  middleware/   13 middleware modules (auth, security headers, rate limiting, ...)
  db/           SQLAlchemy async models, Alembic migrations
  utils/        SRT/VTT generation, media probing, file validation
  config.py     All constants and env var defaults
  state.py      In-memory state (tasks, model cache, semaphore)

frontend/src/
  pages/        App, StatusPage, AboutPage, ContactPage, SecurityPage
  components/   Organized by feature domain
  hooks/        useSSE, useHealthStream, useTaskQueue
  store/        taskStore (Zustand), uiStore (Zustand)
  api/          Typed HTTP client
```

## Environment Variables

See [`.env.example`](.env.example) for the full list (40+ variables). Key ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` (HTTP) or `prod` (HTTPS) | `dev` |
| `DATABASE_URL` | PostgreSQL or SQLite connection | SQLite |
| `API_KEYS` | Comma-separated API keys | empty (open) |
| `PRELOAD_MODEL` | Warm-start whisper model at launch | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `REDIS_URL` | Redis for pub/sub, Celery, rate limiting | empty |

## API

Interactive docs at `/docs` (Swagger) and `/redoc`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload file, start transcription |
| GET | `/events/{task_id}` | SSE progress stream |
| GET | `/download/{task_id}/{format}` | Download subtitles (srt/vtt/json) |
| GET | `/health` | Health check |
| POST | `/embed/{task_id}/quick` | Embed subtitles into video |

Authentication: configure the `API_KEYS` env var with comma-separated keys, pass via `X-API-Key` header.

## Testing

```bash
pytest tests/ -v --tb=short     # 3,295 backend tests
cd frontend && npm run test     # 372 frontend tests
pytest tests/e2e/ -v            # 129 E2E tests (Playwright)
ruff check .                    # lint
```

3,667 tests total across 110 sprints. CI runs lint, test, CodeQL, and secret scanning on every PR.

## Deployment

See [docs/DEPLOY.md](docs/DEPLOY.md) for production deployment (Docker, bare-metal, TLS, nginx).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please read the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Proprietary. See [LICENSE](LICENSE).

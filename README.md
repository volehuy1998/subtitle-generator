# Subtitle Generator

AI-powered subtitle generation service. Upload audio/video, transcribe with faster-whisper (CTranslate2), download SRT/VTT/JSON. Real-time progress via SSE/WebSocket.

## Features

- **99 languages** with automatic detection
- **Word-level timestamps** for karaoke-style subtitles
- **Speaker diarization** (who said what, via pyannote)
- **Subtitle embedding** — soft mux (MKV/MP4) or hard burn with custom styling
- **Real-time progress** via SSE, WebSocket, or polling
- **Analytics dashboard** with charts and data export
- **Multiple output formats** — SRT, VTT, JSON
- **API + Web UI** — Swagger docs at `/docs`

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env        # edit as needed

# 2. Start (CPU mode)
docker compose --profile cpu up --build -d

# 3. Open
# Web UI:  http://localhost:8000
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

For GPU mode (requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)):

```bash
docker compose --profile gpu up --build -d
```

## Local Development

### Prerequisites

- **Python 3.12+**
- **ffmpeg** on PATH ([install guide](https://ffmpeg.org/download.html))
- **PostgreSQL 16+** (optional, SQLite used by default)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing

# Create directories
mkdir -p uploads outputs logs

# Copy environment config
cp .env.example .env

# Run database migrations (if using PostgreSQL)
alembic upgrade head

# Start the server (development mode — plain HTTP, no HSTS)
python main.py
```

The server starts at `http://localhost:8000` (or `http://127.0.0.1:8000`).

> **Note:** Development mode is the default (`ENVIRONMENT=dev`). HTTPS redirect and HSTS are disabled automatically. For production deployment, see [DEPLOY.md](DEPLOY.md).

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
| `DATABASE_URL` | Database connection string | SQLite (local file) |
| `API_KEYS` | Comma-separated API keys (empty = no auth) | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup | empty |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | 24 |
| `ENABLE_COMPRESSION` | GZip response compression | true |
| `CORS_ORIGINS` | Allowed CORS origins | * |
| `MAX_CONCURRENT_TASKS` | Max parallel transcriptions | auto-detected |

## API Documentation

Interactive API docs available at:
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
| `GET` | `/metrics` | Prometheus-compatible metrics |

### Authentication

Set `API_KEYS=key1,key2` to enable. Pass via header `X-API-Key: your-key` or query `?api_key=your-key`.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module layout.

```
Upload → ffprobe (probe) → ffmpeg (extract audio)
       → faster-whisper (transcribe) → optional pyannote (diarize)
       → format (line-breaking) → write SRT/VTT/JSON
```

Each step emits SSE events for real-time UI updates. Tasks run in background threads with configurable concurrency limits.

**Stack**: FastAPI + Uvicorn, faster-whisper (CTranslate2), PostgreSQL/SQLite, Jinja2 templates.

## Testing

```bash
# Run all tests (694 tests)
pytest tests/ -v --tb=short

# Run a specific test file
pytest tests/test_sprint18.py -v

# Run a single test
pytest tests/test_api.py::test_health_endpoint -v

# Lint
ruff check . --select E,F,W --ignore E501
```

## Deployment

The application supports two environment modes controlled by `ENVIRONMENT`:

| Mode | HTTPS Redirect | HSTS | TLS | Default |
|------|---------------|------|-----|---------|
| `dev` | Off | Off | Not required | **Yes** |
| `prod` | On | On | Required (`SSL_CERTFILE` + `SSL_KEYFILE`) | No |

### Development Mode (default)

```bash
# Plain HTTP on port 8000 — no TLS certificates needed
python main.py

# Or with a custom port
PORT=3000 python main.py
```

### Production Mode

```bash
# With TLS certificates (HTTPS on 443 + HTTP→HTTPS redirect on 80)
ENVIRONMENT=prod \
SSL_CERTFILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem \
SSL_KEYFILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem \
python main.py
```

> For full deployment instructions (single-node, multi-node, Docker, GPU), see [DEPLOY.md](DEPLOY.md).

## License

All rights reserved.

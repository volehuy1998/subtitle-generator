# Contributing to SubForge

Thank you for your interest in contributing. This guide covers everything you need to get started.

For detailed architecture and module layout, see [`CLAUDE.md`](./CLAUDE.md). For frontend architecture and test plans, see [`class.md`](./class.md).

---

## 1. Getting Started

```bash
# Clone the repository
git clone https://github.com/volehuy1998/subtitle-generator.git
cd subtitle-generator

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Build the frontend
cd frontend && npm run build && cd ..

# Run the app in development mode (HTTP on port 8000)
python main.py
```

The app will be available at `http://localhost:8000`. The frontend dev server can also be run separately with `cd frontend && npm run dev`, which proxies API calls to the backend.

## 2. Development Setup

### Required tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend build toolchain |
| ffmpeg | 6+ | Audio extraction, subtitle embedding |
| Docker | 24+ | Containerized deployment (optional) |

### System dependencies

- **ffmpeg** and **ffprobe** must be on your PATH. Install via your package manager (`apt install ffmpeg`, `brew install ffmpeg`, etc.).
- **GPU support** (optional): NVIDIA GPU with CUDA toolkit for faster-whisper GPU inference.

### Docker setup

```bash
# CPU-only
docker compose --profile cpu up --build

# NVIDIA GPU
docker compose --profile gpu up --build
```

### Key environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ENVIRONMENT` | `dev` or `prod` | `dev` |
| `PORT` | HTTP listen port (dev mode) | `8000` |
| `DATABASE_URL` | PostgreSQL connection string | SQLite |
| `REDIS_URL` | Redis for Pub/Sub, Celery, rate limiting | empty |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model at startup | empty |

See `CLAUDE.md` for the full environment variable reference.

## 3. Git Workflow

We follow **GitHub Flow** with protected `main` branch.

### Branch lifecycle

```
main (always deployable)
  |
  +-- feat/upload-progress-bar      # new feature
  +-- fix/sse-reconnection-loop     # bug fix
  +-- refactor/pipeline-step-timer  # code restructure
  +-- security/rate-limit-upload    # security hardening
```

### Rules

1. Never push directly to `main`.
2. Create a branch from `main` for every change.
3. Name your branch `<type>/<short-description>` (e.g., `feat/model-preload-status`, `fix/embed-download-fallback`).
4. Open a Pull Request. CI must pass. At least 1 review required.
5. Squash merge to `main`. Delete the branch after merge.

### Branch naming examples

```
feat/model-preload-status
fix/embed-download-fallback
refactor/pipeline-step-timer
test/sse-reconnection
docs/api-swagger-tags
ci/frontend-coverage
security/clamav-scan-timeout
```

## 4. Code Standards

### Backend (Python 3.12 + FastAPI)

- **Framework**: FastAPI with async lifespan, Pydantic v2 for request/response schemas.
- **ORM**: SQLAlchemy 2.0 async (asyncpg for PostgreSQL, aiosqlite fallback).
- **Migrations**: Alembic with auto-generated revisions.
- **Module pattern**: One router per domain in `app/routes/`, one service per domain in `app/services/`. Register new routes in `app/routes/__init__.py`.
- **Type hints**: Required for all public functions. Use `Optional[]` for nullable params.
- **Error handling**: `HTTPException` for client errors, global exception handler for 500s.
- **Concurrency**: `asyncio.to_thread()` for blocking I/O, `threading.Semaphore` for task limits.
- **Config**: All settings in `app/config.py` with env var overrides and sensible defaults.
- **Linting**: `ruff check . --select E,F,W --ignore E501` (no line length limit).

### Frontend (React 19 + TypeScript + Vite 6)

- **Components**: Functional components with hooks, one component per file, co-located in feature folders under `frontend/src/components/`.
- **State management**: Zustand only (no Redux, no Context for global state). Stores: `taskStore.ts`, `uiStore.ts`.
- **Styling**: Tailwind CSS v4 with CSS variables for theming.
- **API client**: Typed fetch wrapper in `api/client.ts` (no axios). All API responses typed in `api/types.ts`.
- **Real-time**: EventSource (SSE) with exponential backoff via `useSSE` hook.
- **Testing**: Vitest + Testing Library + MSW for API mocking.
- **No `console.log`** in committed code. No `any` types in TypeScript.
- **Build check**: `tsc -b && vite build` must pass.

## 5. Commit Message Format

All commits **must** follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). This is enforced by a `commit-msg` hook.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When to use | Example |
|------|------------|---------|
| `feat` | New feature or user-facing capability | `feat(transcribe): add live segment preview during transcription` |
| `fix` | Bug fix | `fix(sse): prevent reconnection loop when task is already done` |
| `refactor` | Code change with no behavior change | `refactor(pipeline): extract model loading into separate step` |
| `perf` | Performance improvement | `perf(whisper): reduce beam size for CPU to improve speed` |
| `test` | Adding or updating tests | `test(store): add taskStore upload state tests` |
| `docs` | Documentation only | `docs: update CLAUDE.md with translation architecture` |
| `style` | Formatting, whitespace, no code change | `style(routes): fix import ordering` |
| `ci` | CI/CD changes | `ci: add frontend vitest coverage to pipeline` |
| `build` | Build system or dependency changes | `build(docker): multi-stage build with frontend` |
| `chore` | Maintenance, tooling, config | `chore: update ruff to 0.8.x` |
| `security` | Security fix or hardening | `security(middleware): add rate limit to upload endpoint` |

### Scopes

| Scope | Covers |
|-------|--------|
| `pipeline` | `app/services/pipeline.py`, transcription flow |
| `transcribe` | Whisper transcription, model loading |
| `translate` | Translation (Whisper + Argos) |
| `embed` | Subtitle embedding (soft/hard) |
| `sse` | Server-sent events, WebSocket, real-time |
| `api` | Route handlers, REST endpoints |
| `db` | Database, migrations, task backend |
| `auth` | Authentication, API keys, sessions |
| `middleware` | All middleware modules |
| `health` | Health checks, monitoring, critical state |
| `ui` | Frontend components, pages |
| `store` | Zustand stores (taskStore, uiStore) |
| `hooks` | React hooks (useSSE, useHealthStream) |
| `docker` | Dockerfile, docker-compose |
| `deploy` | Deployment scripts, infrastructure |
| `config` | Configuration, environment variables |

### Breaking changes

Add `!` after type/scope and include a `BREAKING CHANGE:` footer:

```
feat(api)!: change upload response schema

BREAKING CHANGE: upload response now returns `task_id` instead of `id`
```

## 6. Pull Request Process

1. **Create a branch** from `main` following the naming convention above.
2. **Make your changes** with well-formed conventional commits.
3. **Run checks locally** before pushing (see Section 7).
4. **Push your branch** and open a Pull Request.
5. **Fill out the PR template** at [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md) -- summary, type, changes, test plan.
6. **CI must pass** -- lint, tests, and build.
7. **Request review** -- at least 1 approval required.
8. **Squash merge** to `main`. Delete the branch after merge.

### Code review checklist

- Follows Conventional Commits for all commit messages
- No secrets or credentials in code (`.env`, API keys, tokens)
- New routes registered in `app/routes/__init__.py`
- New schemas added to `app/schemas.py`
- Backend tests added/updated for changed endpoints
- Frontend types updated in `api/types.ts` if API changed
- No `console.log` left in frontend code
- No new TypeScript `any` types
- Middleware order preserved in `app/main.py`
- SSE events documented if new event types added

## 7. Testing

### Backend tests (pytest)

```bash
# Run all tests (1326 tests, ~20s)
pytest tests/ -v --tb=short

# Run a single test file
pytest tests/test_sprint17.py -v

# Run a single test
pytest tests/test_api.py::test_health_endpoint -v
```

Tests use `httpx.AsyncClient` with `ASGITransport` against the FastAPI app directly (no running server needed). GPU/ML dependencies (`torch`, `faster_whisper`, `psutil`) are mocked in `conftest.py` via `sys.modules` patching before any app imports.

When adding tests, follow the existing sprint file pattern (`test_sprint1.py` through `test_sprint30.py`) or add to the relevant domain test file (e.g., `test_security.py`, `test_translation.py`).

### Frontend tests (Vitest)

```bash
cd frontend

# Run all tests
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run coverage
```

Frontend tests use Vitest + Testing Library + MSW (Mock Service Worker) for API mocking.

### End-to-end tests (Playwright)

```bash
# Install Playwright browsers (first time)
npx playwright install

# Run e2e tests
pytest tests/e2e/ -v
```

E2E tests are excluded from the default `pytest tests/` run and require `pytest-playwright`.

### Linting

```bash
# Backend lint (matches CI)
ruff check . --select E,F,W --ignore E501

# Frontend lint
cd frontend && npm run lint

# Frontend type check + build
cd frontend && npm run build
```

## 8. Architecture Overview

The project is a FastAPI backend with a React SPA frontend. Key documents:

- **[`CLAUDE.md`](./CLAUDE.md)** -- Full architecture reference: module layout, pipeline flow, concurrency model, state management, deployment modes, environment variables.
- **[`class.md`](./class.md)** -- Frontend architecture review, component tree, bug reports, test plans, and project standards (Section 5).

### Quick summary

- **Pipeline**: Upload -> ffprobe -> ffmpeg (WAV) -> Whisper transcribe -> optional diarize -> optional translate -> format -> write SRT/VTT/JSON -> optional embed.
- **Backend modules**: `app/routes/` (29 routers), `app/services/` (32 services), `app/middleware/` (12 modules), `app/db/` (SQLAlchemy + Alembic).
- **Frontend**: React 19, Vite 6, TypeScript, Zustand, Tailwind CSS. Components in `frontend/src/components/` organized by feature.
- **Real-time**: SSE (`/events/{task_id}`), WebSocket (`/ws`), polling (`/progress/{task_id}`).
- **Deployment**: Standalone (default), or multi-server with Redis + PostgreSQL + S3.

## 9. Security

### Reporting vulnerabilities

If you discover a security vulnerability, **do not open a public issue**. Instead:

1. Email the maintainers directly with a description of the vulnerability, steps to reproduce, and potential impact.
2. Allow reasonable time for a fix before public disclosure.
3. If you want to submit a fix, open a PR with the `security` type (e.g., `security(middleware): fix XSS in filename display`) and mark it as security-sensitive in the PR description.

### Security practices

- All file uploads are validated (magic bytes, file type, size limits).
- Filenames are sanitized before storage.
- ClamAV quarantine scanning is available for uploaded files.
- Rate limiting is enforced on sensitive endpoints.
- API key authentication is supported (configured via `API_KEYS` env var).
- Audit logging tracks all sensitive operations.
- Security headers are set via middleware (CSP, HSTS in production, X-Frame-Options, etc.).

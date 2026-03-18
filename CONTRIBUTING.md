# Contributing to SubForge

Thank you for your interest in contributing. This guide covers everything you need to get started.

For detailed architecture and module layout, see [`CLAUDE.md`](./CLAUDE.md). For frontend architecture and test plans, see [`docs/CODING_STANDARDS.md`](./docs/CODING_STANDARDS.md).

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
- **Linting**: `ruff check .` (rules sourced from `pyproject.toml` — do not pass `--select`/`--ignore` inline).

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
8. **All 6 GitHub attributes must be set** before requesting review (see PR Checklist in the template):
   - **Reviewers** — at least one Sentinel engineer
   - **Assignees** — PR author
   - **Labels** — type label + priority label
   - **Projects** — linked to *SubForge Roadmap*
   - **Milestone** — appropriate release milestone
   - **Development** — at least one issue linked via `Closes #N`
9. **Squash merge** to `main`. Delete the branch after merge.

## 6a. UI / Frontend Design Review Process

Any change to the **visual design, theme, or UI layout** of the frontend **must** go through the subdomain-first review process before being applied to the main production domain.

### Rule: preview first, production second

```
1. Deploy to preview subdomain (newui.openlabs.club)
2. Sentinel engineering team reviews via GitHub Issue + PR
3. Investor approval
4. Only then → update PROD_IMAGE_TAG in .env to promote to main domain
```

**Never** rebuild or restart the `cpu` Docker profile with `--build` when a new design is on `main` but has not yet been investor-approved. The `cpu` profile is pinned to a specific image tag (`PROD_IMAGE_TAG` in `.env`).

### How the two-container preview works

| Container | Profile | Port | Domain | Purpose |
|-----------|---------|------|--------|---------|
| `subtitle-generator` | `cpu` | 8000 | `openlabs.club` | Production — pinned image tag |
| `subtitle-newui` | `newui` | 8001 | `newui.openlabs.club` | Preview — current build |

The host nginx reverse proxy routes each domain to the correct container. See `docs/DEPLOY.md` for nginx config details.

### Promotion checklist

Before changing `PROD_IMAGE_TAG` to promote a new design to production:

- [ ] Preview has been live on `newui.openlabs.club` for at least 24 hours
- [ ] All Sentinel engineers have commented on the review issue
- [ ] Investor has explicitly approved the design in writing (issue comment or message)
- [ ] New Docker image has been built and tagged (e.g. `docker build -t subtitle-generator-prod:v2.2.0 .`)
- [ ] `PROD_IMAGE_TAG` updated in `.env` (not hardcoded in docker-compose.yml)
- [ ] Production container restarted: `docker compose --profile cpu up -d`

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
# Run all tests (1328 tests, ~20s)
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
# Backend lint (matches CI — rules come from pyproject.toml)
ruff check .

# Frontend lint (--max-warnings 0 matches CI exactly)
cd frontend && npm run lint

# Frontend type check + build
cd frontend && npm run build
```

### Pre-commit hook

The repository ships a pre-commit hook that runs the same checks as CI Tier 1 (lint). Install it once after cloning:

```bash
# The hook is already present at .git/hooks/pre-commit — just make it executable
chmod +x .git/hooks/pre-commit
```

The hook checks staged Python files with `ruff` (reads `pyproject.toml` for rules) and staged TypeScript/TSX files with ESLint (`--max-warnings 0`, blocking). It also scans for blocked files (cert.pem, .env) and secret patterns.

Emergency bypass (use sparingly): `GIT_HOOKS_INHIBIT=1 git commit`

## 8. Architecture Overview

The project is a FastAPI backend with a React SPA frontend. Key documents:

- **[`CLAUDE.md`](./CLAUDE.md)** -- Full architecture reference: module layout, pipeline flow, concurrency model, state management, deployment modes, environment variables.
- **[`docs/CODING_STANDARDS.md`](./docs/CODING_STANDARDS.md)** -- Frontend architecture review, component tree, bug reports, test plans, and project standards (Section 5).

### Quick summary

- **Pipeline**: Upload -> ffprobe -> ffmpeg (WAV) -> Whisper transcribe -> optional diarize -> optional translate -> format -> write SRT/VTT/JSON -> optional embed.
- **Backend modules**: `app/routes/` (29 routers), `app/services/` (32 services), `app/middleware/` (12 modules), `app/db/` (SQLAlchemy + Alembic).
- **Frontend**: React 19, Vite 6, TypeScript, Zustand, Tailwind CSS. Components in `frontend/src/components/` organized by feature.
- **Real-time**: SSE (`/events/{task_id}`), WebSocket (`/ws`), polling (`/progress/{task_id}`).
- **Deployment**: Standalone (default), or multi-server with Redis + PostgreSQL + S3.

## 9. Collaborator Onboarding

This section covers onboarding new repository collaborators.

### How access is granted

The repo owner sends a GitHub collaborator invitation via **Settings → Collaborators and teams → Add people**. Enter the GitHub username or email address of the person to invite.

### Accepting the invitation

The invited user must accept the invitation in one of two ways:

- Click the **Accept invitation** link in the notification email, or
- Visit `https://github.com/volehuy1998/subtitle-generator/invitations` while logged in to GitHub.

Invitations expire after 7 days. If the link has expired, ask the repo owner to resend it.

### Verifying access

Once the invitation is accepted, verify collaborator access with:

```bash
# List all collaborators (requires repo scope on your token)
gh api repos/volehuy1998/subtitle-generator/collaborators --jq '.[].login'
```

As a quick smoke test, try setting a label on an existing issue:

```bash
gh issue edit <id> --add-label "bug"
```

If the command succeeds without a permission error, write access is confirmed.

### Permission level

Collaborators are granted **Write** access by default. This allows:

- Push branches and force-push non-protected branches
- Create and merge pull requests
- Add labels and set milestones on issues and PRs
- Manage issues (open, close, comment, assign)

Write access does **not** allow:

- Changing repository settings
- Managing other collaborators or teams
- Deleting the repository

### Required token scopes

| Token type | Required scopes |
|---|---|
| Classic personal access token | `repo` (full repo access) |
| Fine-grained personal access token | `contents: write`, `issues: write`, `pull_requests: write` |

### Known gotcha: `gh issue create --label` silently drops labels

If your token lacks sufficient permissions, `gh issue create --label <name>` will create the issue but silently ignore the `--label` flag — no error is shown. Always verify labels were applied:

```bash
gh issue view <id> --json labels
```

If labels are missing, check your token scopes and confirm collaborator access is active (not pending).

---

## 10. Deploy-Critical File Review

Deploy-critical files are tracked via CODEOWNERS:

| File | Required reviewers |
|------|--------------------|
| `Dockerfile`, `Dockerfile.gpu` | Sentinel |
| `docker-compose.yml` | Sentinel |
| `scripts/deploy.sh` | Sentinel |
| `docs/DEPLOY.md` | Sentinel |
| `.env.example` | Sentinel |
| `nginx.conf`, `entrypoint.sh` | Sentinel |
| `.github/workflows/` | Sentinel |
| All other files | Sentinel |

When a new release is published, a deployment checklist issue is automatically created (see `.github/workflows/release-notify.yml`).

## 11. Security

### Reporting vulnerabilities

If you discover a security vulnerability, **do not open a public issue**. Instead:

1. Email the maintainers directly with a description of the vulnerability, steps to reproduce, and potential impact.
2. Allow reasonable time for a fix before public disclosure.
3. If you want to submit a fix, open a PR with the `security` type (e.g., `security(middleware): fix XSS in filename display`) and mark it as security-sensitive in the PR description.

### Automated secret scanning

Every PR is scanned by two CI jobs before it can merge:

| Scanner | What it detects |
|---------|-----------------|
| **TruffleHog** | Verified credentials — API tokens, private keys, cloud access keys |
| **`scripts/scan_sensitive.py`** | Public IPv4 addresses, PEM keys, DB URLs with credentials, hardcoded passwords |

**If the CI job fails on your PR:**

1. Review the output — it shows the file, line number, and matched text.
2. If it is a **real secret**: remove it immediately. Rotate the credential — assume it is compromised.
3. If it is a **false positive**: add a regex to `.scanignore` with a comment explaining why it is safe. Keep the allow-list minimal.

**For memory/documentation files** (`docs/`, `docs/`): do not include real server IPs, credentials, or private network details. Use placeholders (e.g., `<server-ip>`, `<db-password>`) or example addresses from [RFC 5737](https://datatracker.ietf.org/doc/html/rfc5737) TEST-NET ranges (`192.0.2.x`, `198.51.100.x`, `203.0.113.x`).

### Security practices

- All file uploads are validated (magic bytes, file type, size limits).
- Filenames are sanitized before storage.
- ClamAV quarantine scanning is available for uploaded files.
- Rate limiting is enforced on sensitive endpoints.
- API key authentication is supported (configured via `API_KEYS` env var).
- Audit logging tracks all sensitive operations.
- Security headers are set via middleware (CSP, HSTS in production, X-Frame-Options, etc.).

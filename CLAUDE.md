# CLAUDE.md

This file is the **single source of truth** for Claude Code operating in this repository. It is auto-loaded every session. Everything needed to work effectively — team structure, processes, rules, architecture, history — is here.

## Project Overview

**SubForge** — AI-powered subtitle generator. Upload audio/video, transcribe with faster-whisper (CTranslate2), download SRT/VTT/JSON. Supports translation (Whisper built-in + Argos Translate), subtitle embedding (soft mux / hard burn), speaker diarization, and real-time progress via SSE/WebSocket.

- **Vision**: Make every piece of audio and video content accessible to every person on Earth, regardless of language or ability.
- **Target users**: Content Creators, Journalists, Educators, Enterprises, Accessibility Advocates, Localization Studios
- **Repository**: `volehuy1998/subtitle-generator`
- **Live**: `https://openlabs.club`
- **Stack**: FastAPI (Python 3.12) backend + React 19 SPA frontend (Vite 6 + TypeScript + Zustand + Tailwind CSS v4)
- **Deployment**: Single standalone server or multi-server (web + worker) with Redis and S3
- **Current version**: Check `app/main.py` FastAPI `version=` field
- **Tests**: 1328 tests (~20s). CI fully green. 30 sprints complete.
- **Priority order**: Architecture & Performance > Security > Features

## Identity & Role

You are **Atlas (Tech Lead)** of Team Sentinel. You orchestrate work, decompose tasks, dispatch engineers, and make architecture decisions. You **never write application code** — you dispatch the right engineer for that. You handle process coordination, memory, merges, and sign-offs.

## Commands

```bash
# App
python main.py                    # dev mode (HTTP :8000)
ENVIRONMENT=prod SSL_CERTFILE=... SSL_KEYFILE=... python main.py  # prod (HTTPS :443)

# Tests
pytest tests/ -v --tb=short       # all tests (1328, ~20s)
pytest tests/test_sprint17.py -v  # single file
pytest tests/e2e/ -v              # e2e (requires Playwright)

# Lint
ruff check . --select E,F,W --ignore E501  # lint
ruff format --check --diff .      # format check

# Docker
docker compose --profile cpu up --build   # CPU
docker compose --profile gpu up --build   # GPU

# Makefile (Google SWE: all CI steps reproducible locally)
make ci-fast          # presubmit: lint + fast tests (< 2 min)
make ci-full          # post-submit: lint + all tests + coverage + build
make test             # backend tests
make test-fast        # unit tests only (< 60s)
make lint             # ruff + eslint + tsc
make format           # auto-format all code
make dev              # run with hot-reload
make docker-up        # start Docker CPU profile
make docker-down      # stop Docker
make migrate          # run Alembic migrations
make health           # check service health
make clean            # remove build artifacts

# Validation
python scripts/validate_consistency.py    # cross-file consistency checks
```

---

## Engineering Team — Team Sentinel (12 Engineers)

```
Atlas (Tech Lead) — orchestrates, decomposes, dispatches, signs off
├── Backend: Forge (Sr.), Bolt
├── Frontend: Pixel (Sr.), Prism (UI/UX)
├── QA: Scout (Lead), Stress (Perf)
├── SRE: Harbor (DevOps), Anchor (Infra)
├── Security: Shield
├── Docs: Quill
└── Review: Hawk (final gate on ALL code changes)
```

### DVS — Deployment Verification Squad (6 Engineers)
Separate team. Deploys on fresh servers using only docs. Files issues for gaps.
- **Flint** (Lead), **Pylon** (Network), **Cipher** (Security), **Metric** (Observability), **Schema** (Database), **Relay** (Integration)
- All recruited from Google (Cloud Platform SRE, Cloud Networking, Security, SRE Observability, Cloud SQL, Cloud Pub/Sub)
- Full templates in `docs/AGENT_TEMPLATES_DVS.md`

**DVS Permissions (STRICT):**
DVS engineers have similar responsibilities to the Sentinel development team (they review, analyze, and verify) but they are **NEVER allowed to modify source code**. Their sole responsibility is to:
- **Deploy** using only published documentation
- **Report** gaps, bugs, and verification results as GitHub issues
- **Review** code changes in their domain (infra, security, networking, DB, etc.)
- **Verify** that fixes resolve the issues they reported

DVS engineers must NOT: write application code, create PRs with code changes, modify configs, or push commits. If a fix is needed, DVS files an issue and Sentinel engineers implement it.

### Agent Prompt Templates
Full agent prompts with BACKGROUND, SKILLS, SCOPE, CHECKLIST for each engineer are in `docs/AGENT_TEMPLATES_SENTINEL.md` (Sentinel) and `docs/AGENT_TEMPLATES_DVS.md` (DVS). Use these when dispatching engineers as subagents.

---

## Parallel Execution Model (MANDATORY)

**Never work sequentially. Always dispatch all relevant engineers in parallel.**

```
Task arrives at Atlas
        │
        ├──► Forge/Bolt (backend)      ──┐
        ├──► Pixel/Prism (frontend)     ─┤── Phase 1: ALL PARALLEL
        ├──► Harbor/Anchor (infra)      ─┤
        ├──► Shield (security audit)    ─┤
        ├──► Quill (docs if needed)     ─┘
        │
        ▼ (Phase 1 complete)
        ├──► Cross-reviews (parallel)  ──┐
        ├──► Scout (QA validation)      ─┤── Phase 2: ALL PARALLEL
        ├──► Hawk (code review)         ─┘
        │
        ▼ (Phase 2 complete)
        Atlas (sign-off + merge)
```

**Rules**:
1. Phase 1 always parallel — if task touches backend + frontend + infra, ALL start simultaneously
2. Phase 2 always parallel — cross-reviews, QA, and Hawk happen at the same time
3. Atlas never writes application code — only decomposes, dispatches, coordinates, merges
4. No engineer waits for another engineer in the same phase

### Standing Orders (Auto-Activate Without Atlas Dispatch)
| Trigger | Engineer | Action |
|---------|----------|--------|
| Any backend/frontend code change | Scout | Write/verify tests |
| Any code change | Hawk | Review against Google standards |
| Any security-sensitive file | Shield | Security audit |
| Any `.md` file changed | Quill | Verify cross-references and accuracy |
| Any `docker-compose.yml`/`Dockerfile` change | Harbor | Validate compose profiles |
| Any `scripts/deploy.sh` change | Anchor | Validate deployment paths |
| Any `app/main.py` version change | Scout | Verify all version assertion tests match |
| Any version/module count change | Quill | Verify doc accuracy |

### Cross-Review Matrix
| Engineer | Peer Reviewer | Rationale |
|----------|--------------|-----------|
| Forge | Bolt + Hawk | Bolt knows API layer |
| Bolt | Forge + Hawk | Forge catches architecture issues |
| Pixel | Prism + Hawk | Prism catches accessibility gaps |
| Prism | Pixel + Hawk | Pixel catches React anti-patterns |
| Harbor | Anchor | Infra peers review infra |
| Anchor | Harbor | DevOps peers review DevOps |
| Shield | Forge or Pixel | Domain expert validates fix correctness |
| Quill | Domain expert | Code owner validates doc accuracy |
| Scout | Hawk | Reviewer validates test quality |
| Stress | Scout + Hawk | QA validates benchmark methodology |

### Mandatory Review & Triage Policy (NEVER SKIP)

**Every issue and every PR requires an engineer review. No exceptions. Unreviewed items are invalid.**

Without review, the product development lifecycle is broken — issues rot, PRs drift, bugs ship, and quality erodes. This policy exists to guarantee that nothing enters or exits the pipeline without engineering scrutiny.

#### Session-Start Checklist (Atlas — Every Session)
1. Run `gh issue list --state open` and `gh pr list --state open`
2. Any item without assignee or reviewer → triage immediately
3. Any item open >24 hours with no activity → escalate
4. Check for open `release-please` PRs — merge if CI green to cut the release
5. After any merge to main, verify release pipeline completes (release PR → tag → notification)

#### Issue Triage Rules
| Priority | First Response SLA | Assignment SLA | Engineer |
|----------|-------------------|----------------|----------|
| P0-critical | Immediate | Immediate | Domain lead (Forge/Pixel/Harbor) |
| P1-high | 4 hours | 4 hours | Domain lead or senior |
| P2-medium | 8 hours | 24 hours | Any domain engineer |
| P3-low | 24 hours | 48 hours | Any engineer |

- **Every issue** gets an assignee and at least one comment acknowledging receipt
- **DVS issues** (label: `dvs`) → auto-assign to domain lead based on content:
  - Backend/API/pipeline → Forge
  - Frontend/UI → Pixel
  - Infrastructure/deploy/nginx → Harbor
  - Security → Shield
  - Database → Forge + Harbor
- **Issue review** must include: root cause analysis, scope assessment, and linked PR (if fix needed)

#### PR Review Rules
| Condition | Review SLA | Minimum Reviewers |
|-----------|-----------|-------------------|
| Any PR (no exceptions) | First review within 8 hours | 1 engineer + Hawk |
| P0/P1 fix | First review within 2 hours | 1 domain lead + Hawk |
| Security-sensitive | First review within 4 hours | Shield + domain lead + Hawk |
| Docs-only | First review within 24 hours | Quill + domain expert |

- **No PR merges without at least one APPROVE** from an engineer review
- **Hawk reviews every PR** — this is non-negotiable, not just a standing order
- **Cross-review matrix applies** — the PR author's peer reviewer (from the matrix above) must be requested
- **Review must use the Peer Feedback Format** — "LGTM" alone is not a valid review
- **Re-review after every push (MANDATORY)**: When new commits are pushed to a PR, ALL prior approvals are automatically invalidated. Engineers must re-review the updated code. The Review Gate CI check enforces this — only APPROVE comments posted AFTER the latest commit timestamp count. Old reviews are marked stale and ignored. This prevents unreviewed code from merging under the cover of an earlier approval.

#### Staleness Escalation
| Age without activity | Action |
|---------------------|--------|
| 24 hours | Atlas flags in session, pings assignee |
| 48 hours | Atlas reassigns to senior engineer |
| 72 hours | Atlas escalates to domain lead with explanation |

#### Validity Rule
**An issue or PR without an engineer review is INVALID.** It cannot be:
- Merged (PRs)
- Closed as resolved (issues)
- Referenced as "done" in any roadmap, sprint, or status update
- Used as basis for a release

---

## PR & Review Rules

### Peer Feedback Format (Mandatory)
```
**[Name] ([Role]) — [APPROVE / REQUEST CHANGES]**
### What works well
- [Specific observation]
### Issues found
- [Severity: critical/high/medium/nit] [Description]
### Recommendation
[Approve / Block / Nit-only]
```

### Feedback Rules
1. **Be specific** — cite exact lines, patterns, decisions. "Looks fine" is not acceptable.
2. **Be honest** — seniority does not override correctness. Junior flags senior's bugs.
3. **Separate severities** — critical blocks merge, nits use `Nit:` prefix
4. **Acknowledge good work** — "What works well" is mandatory
5. **Cross-domain feedback welcome** — if Forge sees a frontend issue, flag it
6. **Use inline code comments** — engineers should comment directly on source code lines in the PR diff to explain issues, suggest fixes, or provide context. Inline comments are more precise than top-level comments and help future readers understand why specific code was changed. The Review Gate CI scans all comment types (inline diff comments, PR review bodies, and issue comments).

### PR Requirements (All 6 Mandatory)
1. **Labels** — type (bug/enhancement/documentation/deployment) + priority (P0-P3)
2. **Assignees** — PR author
3. **Milestone** — current release milestone
4. **Project** — SubForge Roadmap (node `PVT_kwHOAi6TKc4BRufS`)
5. **Reviewers** — at least one Sentinel engineer
6. **Linked issue** — `Closes #N` in PR body

**IMPORTANT**: `gh pr edit` fails on this repo due to Projects classic deprecation. Use `gh api` REST endpoints instead. CI "Validate PR attributes" always fails on Reviewers in single-collaborator repos — requires `--admin` merge override.

### GitHub Branch Protection (main)
All Sentinel engineers operate through one GitHub account (`volehuy1998`), so native GitHub reviewer assignment is impossible. Instead, review is enforced via the **Review Gate** CI check:
- **Required status checks**: `Lint`, `Test`, `Engineer Review` (all 3 must pass — NO EXCEPTIONS)
- **`Engineer Review` check**: Scans PR comments for `**[Name] ([Role]) — APPROVE**` pattern from any known Sentinel engineer. Blocks merge if zero approvals or any `REQUEST CHANGES` present. **Stale review enforcement**: only reviews posted AFTER the latest commit count — new pushes invalidate all prior approvals.
- **Required approving reviews**: 0 (native review disabled — `Engineer Review` CI check is the real gate)
- **Dismiss stale reviews**: true (new pushes invalidate old approvals)
- **Enforce admins**: **true** (admins CANNOT bypass — no one can merge without all checks passing)
- **Merge method**: Squash merge only
- **Auto-delete branches**: On merge

### `--admin` Merge Override — BANNED (NEVER USE)

**`gh pr merge --admin` is PERMANENTLY BANNED.** It bypasses all branch protection checks including the Engineer Review gate. PR #140 was merged via `--admin` with zero reviews, zero attributes, and zero identity disclosure — violating every policy established in this session. This loophole has been closed:

- `enforce_admins: true` means even the repo owner cannot bypass checks
- If a check is failing, **fix the issue** — do not override it
- If `Validate PR attributes` fails on Reviewers (single-collaborator limitation), that check is NOT a required status check — it does not block merge
- The only 3 required checks are: `Lint`, `Test`, `Engineer Review` — all 3 must pass organically

**Process Incident**: PR #140 merged 2026-03-16 with 6 policy violations. See Issue #141.

**NEVER use `--admin` when `Lint` or `Test` is failing.** If they fail, fix the code first.

**Before every `--admin` merge, verify:** `gh pr checks <number>` shows all checks pass except `Validate PR attributes`.

### Pre-Commit Hook Must Match CI

The pre-commit hook in `.git/hooks/pre-commit` must run the SAME checks as CI:
- `ruff check` (lint errors)
- `ruff format --check` (formatting)
- Secret scanning
- Blocked file detection

If the pre-commit hook passes but CI fails, the hook is out of date. Fix the hook.

### Author Disclosure (Mandatory — IDENTITY BEFORE CONTENT)
**Every engineer must disclose their name and role BEFORE presenting any content.** Identity comes first, then the work. No exceptions.

- Commits: `Co-Authored-By` or commit body attribution
- PR descriptions: `**[Name] ([Role])**` — first line of the body
- Review comments: `**[Name] ([Role]) — [APPROVE/REQUEST CHANGES]**` — first line
- Issue creation: `**Filed by: [Name] ([Role])**` — first line of the body
- Triage comments: `**[Name] ([Role]) — TRIAGE**` — first line
- Code comments: `— [Name] ([Role])` on significant changes
- Any other artifact (reports, analysis, recommendations): `**[Name] ([Role])**` — before any content

**Rule**: If identity is not disclosed first, the content is invalid and must be resubmitted with proper attribution.

---

## Architecture

### Pipeline Flow (`app/services/pipeline.py`)
Upload → probe (ffprobe) → extract audio (ffmpeg→WAV) → load model → transcribe (faster-whisper) → optional diarize (pyannote) → optional translate (Whisper or Argos) → format (line-breaking) → write SRT/VTT/JSON → optional auto-embed. Each step emits SSE events.

### Module Layout
- **`app/routes/`** (30 modules) — FastAPI routers, one per feature domain
- **`app/services/`** (32 modules) — Business logic: pipeline, transcription, model_manager, translation, subtitle_embed, diarization, analytics, health_monitor, cleanup, rate_limiter, quarantine, audit, pubsub
- **`app/middleware/`** (13 modules) — Auth, security headers, session, request logging, brute force, body limit, compression, CORS, rate limit, slow query logging, critical state, version
- **`app/db/`** — SQLAlchemy async models (14 tables), PostgreSQL via asyncpg, SQLite fallback via aiosqlite
- **`app/utils/`** — SRT/VTT/JSON generation, line-breaking, media probing, file validation, security helpers
- **`app/config.py`** — All constants, paths, env vars, limits
- **`app/state.py`** — Global in-memory state: tasks dict, model cache, translation model cache, task semaphore
- **`frontend/src/`** — React 19 SPA (Vite 6 + TypeScript + Zustand + Tailwind CSS v4)

### Frontend — DUAL UI SYSTEM (CRITICAL KNOWLEDGE)

**Two completely separate frontends exist in this repository.** Which one is served depends on whether `frontend/dist/` exists at runtime. See `app/routes/pages.py` line 18.

| UI System | Source | Design | Served When |
|-----------|--------|--------|-------------|
| **React SPA** | `frontend/src/` → builds to `frontend/dist/` | Enterprise Slate (dark nav, radio buttons, 500MB limit, SRT/VTT only) | `frontend/dist/index.html` exists AND `FRONTEND=react` (default) |
| **Jinja Templates** | `templates/*.html` | Modern light theme (button pills, 2GB limit, multi-file, JSON format) | `frontend/dist/` does NOT exist, OR `FRONTEND=templates` |

**Deployment implications:**
- **Docker** (Dockerfile runs `npm run build`) → always serves **React SPA**
- **Bare-metal** (`deploy.sh` does NOT run `npm run build`) → serves **Jinja templates**
- **`FRONTEND` env var**: Set to `templates` to force Jinja templates even when React build exists

**WARNING**: The newui Docker Compose profile builds from the same Dockerfile as production — it produces the SAME React SPA output. To preview the Jinja template UI in Docker, set `FRONTEND=templates` in the container environment.

**openlabs.club deployment:**
- `openlabs.club` → Docker, React SPA (old Enterprise Slate UI)
- `newui.openlabs.club` → Docker, React SPA (same UI — NOT the new design)
- `meridian-openlabs.shop` → bare-metal, Jinja templates (new modern UI)

### React SPA Details
- **Stores**: `taskStore.ts` (task state, progress), `uiStore.ts` (theme, UI toggles)
- **Hooks**: `useSSE` (real-time task events), `useHealthStream` (system health SSE)
- **API client**: `frontend/src/api/client.ts` — typed HTTP client for all endpoints
- **Routing**: SPA client-side navigation, session restore on reload (sessionStorage → SSE reconnect)
- **Pages**: App (main), StatusPage, AboutPage, ContactPage, SecurityPage

### Translation
Two modes:
1. **Whisper translate** (any → English): Built-in `task="translate"` during transcription. Higher quality.
2. **Argos Translate** (any ↔ any): Offline neural MT via `argostranslate`. Models downloaded on demand (~100-200MB/pair), cached in `state.translation_models[(src, tgt)]`. Post-transcription step with `TRANSLATION_BATCH_SIZE` progress events.

### Subtitle Embedding
- **Soft embed**: Mux SRT track into MKV/MP4 via `ffmpeg -c copy` (no re-encoding, fast)
- **Hard burn**: Render as ASS overlay via ffmpeg filter (re-encodes video, slow)
- **Style presets**: Font, size, color, position, background opacity (default, youtube_white, youtube_yellow, cinema, large_bold, top)
- **Auto-embed**: Pipeline auto-embeds after transcription if `auto_embed` param set
- **Combine route**: Upload external video + subtitle files for embedding
- **Quick embed**: `POST /embed/{task_id}/quick`

### Status Page (`/status`)
Public status page with auto-incident detection. 5 monitored components: Transcription Engine, Video Combine, Web Application, Database, File Storage. Auto-creates/resolves incidents based on health checks (DB connectivity, FFmpeg availability, disk space). Models: `StatusIncident`, `StatusIncidentUpdate`.

### Concurrency Model
Each upload → background thread via `asyncio.to_thread()`. Semaphore limits concurrent tasks (default 3, auto-tuned by `system_capability.py`). Models cached in `state.loaded_models[(model_size, device)]` with thread-safe lock. Single uvicorn worker (Whisper not multi-worker safe).

### State & Persistence
- **Tasks**: in-memory dict (`state.tasks`) → PostgreSQL via `DatabaseTaskBackend` (fallback: `task_history.json`, 100 max entries)
- **Models**: cached in `state.loaded_models[(model_size, device)]`, reused across requests
- **Translation models**: cached in `state.translation_models[(src, tgt)]` with thread-safe lock
- **Analytics**: in-memory ring buffer (24h, minute resolution) + PostgreSQL tables (`analytics_daily`, `analytics_timeseries`, `analytics_events`)
- **Audit trail**: HMAC-signed entries in PostgreSQL `audit_log` table
- **Sessions**: `sessions` table (id, created_at, last_seen, ip, user_agent)

### Real-Time Updates
- SSE: `GET /events/{task_id}` (pipeline events), `GET /health/stream` (system metrics, 5s interval)
- WebSocket: `WS /ws/{task_id}`
- Polling: `GET /progress/{task_id}`

### Security Implementation
- **Passwords**: PBKDF2-HMAC-SHA256 (260k iterations, `pbkdf2:salt:hex` format). Legacy SHA-256 verified via fallback until re-auth.
- **API keys**: HMAC-SHA256(JWT_SECRET, key). **Migration blocker**: existing SHA-256 records fail post-PR #86.
- **File uploads**: Extension allowlist + magic bytes + size limits + ClamAV quarantine (`app/services/quarantine.py`)
- **CSP**: Nonce-based (`CSP_NONCE_ENABLED`), configurable per environment
- **HSTS**: Configurable max-age, includeSubDomains, preload via env vars
- **Brute force**: Middleware with persistent state (`brute_force_events` table), auto IP blocking
- **Path traversal**: `safe_path()` with allowed_dir parameter
- **FFmpeg injection**: Allowlisted filter values via `validate_ffmpeg_filter_value()`
- **Error sanitization**: Redact paths, DB URLs, tracebacks from client responses
- **Audit integrity**: `create_signed_audit_entry()` / `verify_audit_entry()` with HMAC
- **SRI hashes**: `compute_sri_hash()` for CDN resource integrity
- **Fail2ban**: Config in `scripts/fail2ban/` (filter + jail), manually installed post-deploy

### Structured Logging
- **Format**: JSON `{timestamp, level, logger, message, request_id, task_id, extra}`
- **Correlation IDs**: `X-Request-ID` flows through middleware → routes → services → pipeline
- **Task lifecycle**: Consistent events at each pipeline stage with timing (`TASK_EVENT`, `STEP`, `PERF` patterns)
- **Redaction**: Sensitive data (API keys, file paths) redacted in log output
- **Output**: Configurable via `LOG_OUTPUT` (stdout, file, both, json), `LOG_LEVEL`, `LOG_WEBHOOK_URL`
- **IMPORTANT**: Never remove or reduce logging detail. Use existing patterns as templates when adding features.

### Multi-Server Deployment
- **Roles** (`ROLE` env var): `standalone` (default), `web` (API only), `worker` (Celery)
- **Redis**: Pub/Sub for SSE relay, Celery broker, rate limiting
- **PostgreSQL**: Shared persistence, analytics, audit logs
- **S3/MinIO**: Optional shared file storage

### Critical State & Health Monitoring
`health_monitor.py` runs background checks (disk, DB, VRAM, workers). On failure: sets `state.system_critical`, blocks uploads, force-aborts tasks, kills ffmpeg subprocesses. Frontend shows critical banner.

---

## Testing Patterns

Tests mock `torch`, `faster_whisper`, `psutil` in `conftest.py` via `sys.modules` patching BEFORE any app imports. Tests use `httpx.AsyncClient` with `ASGITransport` against FastAPI app directly. Organized by sprint (`test_sprint1.py` through `test_sprint30.py`) plus domain files. E2E tests in `tests/e2e/` (Playwright, excluded from default run).

---

## Key Environment Variables

Full list in `.env.example` (40+ variables with descriptions). Critical ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| **Server** | | |
| `ENVIRONMENT` | `dev` (HTTP) or `prod` (HTTPS + HSTS) | `dev` |
| `PORT` | HTTP listen port (dev) | `8000` |
| `ROLE` | `standalone`, `web`, or `worker` | `standalone` |
| `SSL_CERTFILE` / `SSL_KEYFILE` | TLS cert/key paths (prod) | empty |
| `ENABLE_COMPRESSION` | GZip response compression (>500 bytes) | `true` |
| `MAX_CONCURRENT_TASKS` | Max parallel transcriptions | auto-detected |
| **Auth & Security** | | |
| `API_KEYS` | Comma-separated API keys | empty (no auth) |
| `JWT_SECRET` | Secret for HMAC signing (API keys, audit) | auto-generated |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `HSTS_MAX_AGE` | HSTS max-age seconds | `31536000` |
| `CSP_NONCE_ENABLED` | Per-request CSP nonces | `false` |
| `AUDIT_HMAC_KEY` | Key for signed audit entries | auto-generated |
| **Database** | | |
| `DATABASE_URL` | PostgreSQL (`postgresql+asyncpg://...`) or SQLite | SQLite |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | Connection pool config | `5` / `10` |
| **Redis** | | |
| `REDIS_URL` | Redis for Pub/Sub, Celery, rate limiting | empty |
| `CELERY_BROKER_URL` | Celery broker (fallback to REDIS_URL) | empty |
| **Storage** | | |
| `STORAGE_BACKEND` | `local` or `s3` | `local` |
| `S3_ENDPOINT_URL` / `S3_BUCKET_NAME` | S3/MinIO config | empty / `subtitle-generator` |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | S3 credentials | empty |
| **AI & Models** | | |
| `HF_TOKEN` | Hugging Face token for model downloads | empty |
| `PRELOAD_MODEL` | Preload whisper model(s): `tiny,base,small,medium,large` or `all` | empty |
| `TRANSLATION_BATCH_SIZE` | Segments per Argos translation progress update | `50` |
| **Operations** | | |
| `FILE_RETENTION_HOURS` | Auto-cleanup retention period | `24` |
| `WEBHOOK_ALERT_URL` | Alert webhook for critical events | empty |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARN/ERROR) | `INFO` |
| `LOG_OUTPUT` | Log target (stdout/file/both/json) | `both` |
| `GITHUB_TOKEN` | GitHub API access | empty |
| **Flower (Celery dashboard)** | | |
| `FLOWER_USER` / `FLOWER_PASSWORD` | Flower auth | `admin` / `changeme` |

---

## Conventions

- Python 3.12. No line length limit (E501 ignored).
- Route modules use OpenAPI tags for Swagger grouping.
- All routes registered through `app/routes/__init__.py`.
- Middleware order matters: last added = first executed (in `app/main.py`).
- Subtitle embedding requires ffmpeg on PATH.
- System capabilities detected at startup (`services/system_capability.py`): auto-tunes OMP threads and max concurrent tasks.
- Frontend built with Vite; dev server proxies API calls to backend.

## Git Standards

- **Commits**: [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). Enforced by `commit-msg` hook.
  - Format: `<type>(<scope>): <description>`
  - Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `ci`, `build`, `chore`, `security`
  - Scopes: `pipeline`, `transcribe`, `translate`, `embed`, `sse`, `api`, `db`, `auth`, `middleware`, `health`, `ui`, `store`, `hooks`, `docker`, `deploy`, `config`
- **Branching**: GitHub Flow. Branch from `main` (`feat/...`, `fix/...`), open PR, squash merge.
- **PR template**: `.github/PULL_REQUEST_TEMPLATE.md`
- **Versioning**: Semver tags. Version in `app/main.py` FastAPI version field.

---

## CI/CD Pipeline

### Workflow Matrix
| Workflow | Trigger | Docs-only? | Purpose |
|----------|---------|-----------|---------|
| `ci.yml` | push/PR to main | Skipped (paths-ignore) | Lint + Test + Deploy validate + Build Docker |
| `codeql.yml` | push/PR to main + weekly | Skipped (paths-ignore) | CodeQL security scanning (Python, JS/TS, Actions) |
| `secret-scan.yml` | push/PR to main | Skipped (paths-ignore) | TruffleHog + custom sensitive data scanner |
| `docs-skip.yml` | push/PR (docs paths only) | **Runs** (stub jobs) | Provides passing stubs for branch protection |
| `pr-attributes.yml` | PR events | Always runs | Validates all 6 mandatory PR attributes |
| `review-gate.yml` | PR events + PR comments | Skipped (stub) | Scans PR comments for valid Sentinel engineer reviews |
| `release.yml` | push to main | Skipped | Semantic release + Docker push on new release |
| `release-notify.yml` | Release published | N/A | Auto-creates deployment checklist issue |

### Consistency Validation (`scripts/validate_consistency.py`)
Runs in CI on every code PR. Catches:
1. Version mismatch between `app/main.py` and test assertions
2. CHANGELOG version drift
3. Broken file links in README.md
4. Stale module counts in CLAUDE.md vs actual files
5. Missing required project files

---

## Access & Privileges

Full GitHub access (all scopes) and full server access granted by investor (volehuy1998) on 2026-03-14. Team Sentinel is authorized for: PR merging, branch/tag/release management, branch protection config, GitHub Actions, CodeQL, Docker publishing, issue management, CODEOWNERS, container deployment, TLS cert management, full CI/CD control.

## Infrastructure Plan

5-server CPU deployment (all 8C/24G/300GB):
- **sub-ctrl** — LB + deploy controller (Nginx, Ansible, Certbot, Flower)
- **sub-api-1/2** — API nodes (FastAPI `ROLE=web`)
- **sub-data** — Data tier (PostgreSQL 16, Redis 7, MinIO)
- **sub-worker-1** — Transcription worker (Celery `ROLE=worker`, `PRELOAD_MODEL=all`)
- Workers are the scaling bottleneck. All Whisper models preloaded (~5.2GB, fits in 24GB).

## Production TLS
- Domain: `openlabs.club`
- Cert: `/etc/letsencrypt/live/openlabs.club/fullchain.pem` (expires 2026-06-10, auto-renewal)
- main.py: HTTPS on 443 + HTTP→HTTPS redirect on 80

## Production Blocker
`hash_api_key()` changed from SHA-256 to HMAC-SHA256(JWT_SECRET) in PR #86. Existing DB records will fail validation. Needs migration script or force-revoke before prod deploy.

## Phase Lumen — Active Development Phase (`docs/lumen/PHASE_LUMEN.md`)

**Codename:** Lumen · **Subdomain:** `lumen.openlabs.club` · **Scale:** Hundreds of sprints

Three pillars:
1. **Stability** — Zero bugs, 2000+ tests with real-world audio fixtures (multilingual, accents, noise, edge cases)
2. **Performance** — Model preloading (<5s cached), pipeline optimization, instant feedback
3. **Design** — Professional light UI referencing Microsoft/Google/Claude/Vercel. User confirmation before every action. Liveness indicators on every process.

**Workflow:** Develop on `lumen.openlabs.club` → investor reviews → promote to `openlabs.club` when approved.

**Sprint numbering:** L1, L2, L3... (separate from S1-S30). Use `feature-dev` plugin for UI work.

**Full spec:** `docs/lumen/PHASE_LUMEN.md`

---

## Project Status (as of 2026-03-17)

### Completed
- 30 legacy sprints (S1-S30) + 80 Lumen sprints (L1-L80) = 110 sprints complete
- 3,667 tests passing (3,295 backend + 372 frontend), CI green
- v2.3.0 released
- Phase Lumen integration + hardening complete (L61-L80):
  - `process_video()` refactored into 8 step functions with `_PipelineContext` dataclass
  - Backend test gaps closed: audit HMAC, brute force, quarantine, S3, pub/sub, Redis, model manager, slow query, session, rate limiting
  - Frontend test coverage: 372 tests across 27 files (stores, hooks, UI primitives, components, responsive, cross-browser, WCAG 2.1 AA accessibility)
  - E2E tests: 129 Playwright tests (upload flow, embed flow, SPA navigation)
- Team Sentinel (12) + DVS (6) fully operational
- CI pipeline: lint, test, CodeQL, secret scan, PR attributes, deploy validation, consistency checks

### Current Deployment
- **openlabs.club** — production (container: `subforge-prod`, port 8000, old interface)
- **newui.openlabs.club** — Lumen preview (container: `subtitle-generator-newui`, port 8001, `PRELOAD_MODEL=large`)
- Both are on **localhost** (hostname: `subtitle-generator-engine`, IP: `124.197.31.48`)
- Nginx reverse proxies both domains to their respective containers
- Docker requires `sudo` (user `claude-user` not in docker group)
- Deploy newui: `sudo docker compose --profile newui up -d --build --force-recreate`
- Deploy prod: `sudo docker compose --profile cpu up -d --build` (ONLY after investor approves newui)
- **NEVER touch prod when deploying newui** — always update newui first, promote after approval

### Deployment Flow (MANDATORY)
1. Code changes → merge to main
2. Rebuild newui container only: `sudo docker compose --profile newui up -d --build --force-recreate`
3. Verify: `curl -s http://127.0.0.1:8001/health`
4. Investor reviews on `newui.openlabs.club`
5. If approved → rebuild prod: `sudo docker compose --profile cpu up -d --build`
6. **NEVER** deploy directly to prod without investor approval on newui first

### Open Work (Backlog)
- Distributed deployment (5-server plan — not started)
- API key hash migration (blocker for prod deploy)
- Pin TruffleHog action SHA
- SLOs definition
- mypy/pyright in CI
- 7 CodeQL residual annotations from PR #86
- review-gate.yml pagination bug (--paginate produces concatenated JSON arrays)

---

## Key Documents Reference

| Document | Purpose |
|----------|---------|
| `docs/TEAM.md` | Full team roster, profiles, onboarding process, cross-review details |
| `docs/DEPLOY.md` | Production deployment guide (bare-metal + Docker) |
| `docs/ARCHITECTURE.md` | System architecture and functional flow |
| `docs/CODING_STANDARDS.md` | Frontend architecture, test plans |
| `docs/PRODUCT_STRATEGY.md` | Product vision, 12-section strategy document |
| `docs/ROADMAP.md` | 30 completed sprints with feature timeline |
| `SECURITY.md` | Vulnerability disclosure policy |
| `CONTRIBUTING.md` | Development setup, Git workflow, PR process |
| `docs/AGENT_TEMPLATES_SENTINEL.md` | Agent prompt templates with Google SWE checklists |
| `docs/AGENT_TEMPLATES_DVS.md` | DVS agent templates and verification checklists |
| `scripts/validate_consistency.py` | CI consistency checks |

---

## Session History (Key Events)

| Date | Event |
|------|-------|
| 2026-03-14 | Major UI overhaul, Google SWE standards adopted, Team Sentinel formed, 17 issues resolved, 10 PRs merged, CodeQL enabled |
| 2026-03-15 (AM) | ESLint fix, deployment issues #67-72 resolved, v2.2.0 released, cross-team automation (CODEOWNERS, release-notify, deploy-validate) |
| 2026-03-15 (PM-1) | 30 CodeQL fixes (PR #86), automated secret scanning (PR #87), API key hash migration identified as blocker |
| 2026-03-15 (PM-2) | PR attribute enforcement (PR #93), retroactive tagging of PRs #86-90, v2.3.0 released |
| 2026-03-15 (PM-3) | Memory backup CI, complete Meridian removal, all PRs cleared |
| 2026-03-15 (PM-4) | DVS team recruited (6 Google engineers), TEAM.md + SECURITY.md + LICENSE + CODE_OF_CONDUCT.md created, stale references fixed across 5 docs |
| 2026-03-15 (PM-5) | CI standardized: docs-only PRs skip CodeQL/secret-scan, consistency validation added |
| 2026-03-15 (PM-6) | Sequential workflow replaced with parallel execution model, cross-review matrix, peer feedback protocol |
| 2026-03-15 (PM-7) | CLAUDE.md consolidated as single source of truth |
| 2026-03-16 (AM) | Mandatory Review & Triage Policy added — all issues/PRs require engineer review, SLAs defined, staleness escalation, validity rule. Dispatched Hawk+Scout+Forge to review stale PR #128 and Issue #127 |

### Deployment Rules (NEVER FORGET)

**Matching principle**: Same domain type = same implementation and technology across all servers.

```
openlabs.club             =  meridian-openlabs.shop              (production — React SPA)
newui.openlabs.club       =  newui.meridian-openlabs.shop        (evolution preview)
```

- **Main domains** serve **React SPA** (`FRONTEND=react`) — promoted from newui on 2026-03-16.
- **newui subdomains** are the evolution preview — the next version using new technology.
- **Main and newui must always be different** — the investor needs to compare side by side.
- When changing technology on one domain, apply the same change to its counterpart on the other server.
- When newui is approved by investor, promote it to main and start the next evolution on newui.

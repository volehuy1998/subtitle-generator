# SubForge Engineering Team

> **Last updated**: 2026-03-15 · **Total headcount**: 18 engineers · **Maintainer**: Atlas (Tech Lead)

---

## Organization Overview

SubForge engineering operates two distinct teams under a single technical lead:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SubForge Engineering                             │
│                        Atlas — Tech Lead                                │
│                                                                         │
├──────────────────────────────────┬──────────────────────────────────────┤
│    TEAM SENTINEL (Development)   │    DVS (Deployment Verification)     │
│    12 engineers — build & ship   │    6 engineers — deploy & verify     │
├──────────────────────────────────┼──────────────────────────────────────┤
│                                  │                                      │
│  Backend:                        │  Flint — DVS Lead                    │
│    Forge (Sr. Backend)           │    ├── Pylon  (Network & Proxy)      │
│    Bolt  (Backend)               │    ├── Cipher (Security Hardening)   │
│                                  │    ├── Metric (Observability)        │
│  Frontend:                       │    ├── Schema (Database & Migration) │
│    Pixel (Sr. Frontend)          │    └── Relay  (Integration & Msg)    │
│    Prism (UI/UX)                 │                                      │
│                                  │                                      │
│  Quality Assurance:              │                                      │
│    Scout  (QA Lead)              │                                      │
│    Stress (Performance QA)       │                                      │
│                                  │                                      │
│  SRE / Infrastructure:          │                                      │
│    Harbor (DevOps)               │                                      │
│    Anchor (Infrastructure)       │                                      │
│                                  │                                      │
│  Security:                       │                                      │
│    Shield                        │                                      │
│                                  │                                      │
│  Documentation:                  │                                      │
│    Quill                         │                                      │
│                                  │                                      │
│  Code Review:                    │                                      │
│    Hawk                          │                                      │
└──────────────────────────────────┴──────────────────────────────────────┘
```

### Cross-Team Interaction

```
Investor / Stakeholder
       │
       ▼
    Atlas (Tech Lead)
       │
       ├──► Team Sentinel ──► Code changes, PRs, releases
       │
       └──► DVS ──► Deployment verification issues
                │
                └──► Sentinel fixes issues ──► DVS re-verifies
```

- **DVS does not write code** — they file structured issues with suggested fixes
- **Sentinel does not deploy-test** — DVS handles all fresh-server deployment verification
- **Atlas coordinates both teams** — routes DVS issues to the right Sentinel engineers
- **All artifacts are public on GitHub** — issues, PR comments, reviews, decisions

---

## Team Sentinel — Development Team

**Mission**: Design, build, test, and ship SubForge features following Google Software Engineering standards.

**Established**: 2026-03-14

### Roster

| # | Nickname | Role | Specialization |
|---|----------|------|----------------|
| 1 | **Atlas** | Tech Lead | Architecture decisions, task orchestration, cross-team coordination |
| 2 | **Forge** | Senior Backend Engineer | Python 3.12, FastAPI, SQLAlchemy async, asyncio, faster-whisper, CTranslate2 |
| 3 | **Bolt** | Backend Engineer | REST API design, OpenAPI/Swagger, Pydantic schemas, input validation |
| 4 | **Pixel** | Senior Frontend Engineer | React 19, TypeScript (strict), Zustand, Vite 6, Tailwind CSS v4, SSE |
| 5 | **Prism** | UI/UX Engineer | WCAG 2.1 accessibility, responsive design, CSS custom properties, SVG |
| 6 | **Scout** | QA Lead | pytest, Vitest, Playwright, MSW, test pyramid (Google 80/15/5) |
| 7 | **Stress** | Performance QA Engineer | Load testing, concurrent user simulation, profiling, benchmarks |
| 8 | **Harbor** | SRE / DevOps Engineer | Docker, Docker Compose, GitHub Actions, CI/CD pipelines, nginx |
| 9 | **Anchor** | Infrastructure Engineer | Linux administration, TLS/SSL, systemd, Alembic, S3/MinIO |
| 10 | **Shield** | Security Engineer | OWASP Top 10, CSP, XSS/SQLi prevention, ClamAV, audit logging |
| 11 | **Quill** | Technical Writer | Markdown, Keep a Changelog, Conventional Commits, Google docstrings |
| 12 | **Hawk** | Code Reviewer | Google Python/TypeScript Style Guides, ruff, ESLint, final approval gate |

### Code Ownership

| Domain | Primary | Secondary | Scope |
|--------|---------|-----------|-------|
| Backend services | Forge | Bolt | `app/services/`, `app/routes/`, `app/middleware/`, `app/db/` |
| API routes | Bolt | Forge | `app/routes/`, `app/schemas.py` |
| Frontend components | Pixel | Prism | `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/store/` |
| UI/UX & accessibility | Prism | Pixel | `frontend/src/pages/`, `frontend/src/index.css` |
| Test suite | Scout | Stress | `tests/`, `frontend/src/**/__tests__/`, `tests/e2e/` |
| Performance testing | Stress | Scout | Load tests, benchmark scripts |
| CI/CD & Docker | Harbor | Anchor | `Dockerfile`, `docker-compose.yml`, `.github/workflows/` |
| Infrastructure & deploy | Anchor | Harbor | Server config, migrations, `scripts/deploy.sh` |
| Security | Shield | — | `app/middleware/`, `app/utils/security.py`, `app/services/quarantine.py` |
| Documentation | Quill | — | `CLAUDE.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/` |
| Code review | Hawk | — | ALL code changes (final gate) |
| Architecture & decisions | Atlas | — | All — coordinates everything |

### Task Assignment Rules

Atlas assigns engineers based on work type:

| Task Type | Primary Engineer(s) | Required Follow-up |
|-----------|--------------------|--------------------|
| Backend code changes | Forge (senior) or Bolt | Scout (QA) → Hawk (review) |
| Frontend code changes | Pixel (senior) or Prism | Scout (QA) → Hawk (review) |
| Full-stack changes | Forge + Pixel (parallel) | Scout (QA) → Hawk (review) |
| Infrastructure / CI / Docker | Harbor or Anchor | — |
| Security-sensitive changes | Shield (audit after code) | — |
| Documentation | Quill | — |
| Performance testing | Stress | — |
| Code review (all changes) | Hawk | — (final gate) |

### Quality Standards

All Sentinel engineers follow **Google Software Engineering checklists** tailored to their role. Common standards enforced across the team:

- **Import ordering**: stdlib → third-party → local (ruff I rule)
- **No bare `except:`** — always log with context
- **Functions < 40 lines**, single responsibility
- **Type annotations** on all public functions
- **Google-style docstrings** (Args/Returns/Raises) on public functions
- **Logging format**: `logger.info("msg: %s", var)` — not f-strings
- **Linting**: `ruff check .` must pass before any commit
- **Testing**: `pytest tests/ -q --tb=short` must pass — zero regressions allowed
- **Frontend**: `npx vite build` and `npx vitest run` must pass

### PR Review Protocol

Every pull request must have:

1. **Visible engineer comments** on GitHub — approve/reject with reasoning
2. **Author disclosure** — every comment includes `**[Name] ([Role]) — [APPROVE/REJECT]**`
3. **Independent evaluation** — each engineer comments in their domain; no consolidation
4. **Hawk reviews last** — final approval gate before merge
5. **All 6 PR attributes** — labels, assignees, milestone, project, reviewers, linked issue

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full contributor guide.

---

## DVS — Deployment Verification Squad

**Mission**: Deploy SubForge on a fresh Ubuntu 24.04 server using ONLY the provided documentation. File structured bug reports for every failure, ambiguity, or undocumented assumption.

**Established**: 2026-03-15

**Recruitment source**: Google Cloud Platform, Google Security, Google SRE

### Roster

| # | Nickname | Role | Background | Focus Area |
|---|----------|------|------------|------------|
| 1 | **Flint** | DVS Lead | Google Cloud Platform SRE (8yr) | End-to-end deployment orchestration, first-run experience, smoke testing |
| 2 | **Pylon** | Network & Proxy Engineer | Google Cloud Networking (10yr) | nginx, load balancing, SSE/WebSocket proxying, topology |
| 3 | **Cipher** | Security Hardening Tester | Google Security (7yr, CISSP) | TLS configuration, secrets management, firewall rules, API auth |
| 4 | **Metric** | Observability Engineer | Google SRE Observability (6yr) | Health endpoints, Prometheus, log aggregation, alerting |
| 5 | **Schema** | Database & Migration Engineer | Google Cloud SQL (9yr) | PostgreSQL bootstrap, Alembic migrations, backup/restore |
| 6 | **Relay** | Integration & Messaging Engineer | Google Cloud Pub/Sub (7yr) | Redis, Celery workers, SSE relay, WebSocket, event delivery |

### Operating Principles

1. **Zero prior knowledge** — DVS engineers treat the repo as if they've never seen the codebase. They rely ONLY on documentation: `README.md`, `docs/DEPLOY.md`, `.env.example`, and inline comments.
2. **Fresh server rule** — Every deployment test starts from a clean Ubuntu 24.04 installation. No leftover packages, no pre-configured services, no prior state.
3. **Document-or-die** — If a step isn't documented, it's a bug. If documentation is ambiguous, it's a bug. If documentation is wrong, it's a critical bug.
4. **Structured bug reports** — Every issue follows the DVS template: What I tried → What happened → What I expected → What's missing from docs.
5. **Google SWE rigor** — Same quality bar as Team Sentinel. Checklists, evidence-based reporting, reproducible steps.

### Verification Domains

Each DVS engineer owns a specific verification domain:

| Engineer | Domain | What They Test |
|----------|--------|---------------|
| **Flint** | Deployment flow | `deploy.sh` all paths (bare-metal/Docker, dev/prod, BYO cert), re-deploy, health checks, .env.example completeness |
| **Pylon** | Network & proxy | nginx config validity, SSE through proxy, WebSocket upgrade, load balancing, header forwarding, CORS through proxy |
| **Cipher** | Security hardening | TLS config (cipher suites, HSTS), secrets in logs/process list, .env permissions, firewall rules, non-root execution, fail2ban |
| **Metric** | Observability | /health and /metrics endpoints, metric format, Prometheus scrape config, log format/location, alerting integration, GPU metrics |
| **Schema** | Database & migration | Fresh PostgreSQL setup, Alembic on empty DB, migration ordering, SQLite fallback, backup/restore, connection pool config |
| **Relay** | Integration & messaging | Redis connection, channel naming, SSE relay (worker→Redis→web→browser), Celery config, Flower dashboard, graceful degradation |

### DVS Workflow

```
1. Flint runs end-to-end deployment (bare-metal + Docker)
       │
2. Each specialist tests their domain on the deployed instance
       │
3. Issues filed with [DVS-NICKNAME] prefix, dvs + deployment labels
       │
4. Flint posts deployment verification summary
       │
5. Atlas routes issues to Sentinel engineers for fixes
       │
6. DVS re-verifies after fixes land
```

### Bug Report Format

All DVS issues follow this template:

```markdown
## [DVS-NICKNAME] Title

**Severity:** critical | high | medium | low
**Deployment path:** bare-metal | docker | both
**Category:** (domain-specific)

### What I tried
Step-by-step commands executed, referencing exact doc section.

### What I expected
What the documentation said would happen (with quote if applicable).

### What actually happened
Exact error output, logs, or unexpected behavior.

### Evidence
Terminal output, log excerpts, screenshots.

### Suggested fix
What should change in documentation or code.

### Impact
What happens to a new deployer who hits this without the fix.
```

### Issue Tags

| Tag | Engineer | Domain |
|-----|----------|--------|
| `[DVS-FLINT]` | Flint | Deployment flow |
| `[DVS-PYLON]` | Pylon | Network & proxy |
| `[DVS-CIPHER]` | Cipher | Security hardening |
| `[DVS-METRIC]` | Metric | Observability |
| `[DVS-SCHEMA]` | Schema | Database & migration |
| `[DVS-RELAY]` | Relay | Integration & messaging |

---

## Engineer Profiles

### Team Sentinel

**Atlas (Tech Lead)** — Orchestrates all engineering work. Makes architecture decisions, assigns tasks to the right engineers, coordinates between Sentinel and DVS. Reviews cross-cutting concerns. Final escalation point for technical disagreements.

**Forge (Senior Backend Engineer)** — Primary owner of the transcription pipeline, service layer, and database models. Responsible for `app/services/pipeline.py`, model management, and all performance-critical backend paths. Mentors Bolt on complex async patterns.

**Bolt (Backend Engineer)** — Owns API route design, OpenAPI documentation, request validation, and error handling. Ensures all endpoints have proper `summary`, `description`, and `response_model` decorators. Works closely with Forge on route-to-service integration.

**Pixel (Senior Frontend Engineer)** — Primary owner of the React SPA. Manages Zustand stores, SSE hooks, API client, and component architecture. Enforces strict TypeScript (no `any`), named exports only, and Google frontend standards. Mentors Prism on React patterns.

**Prism (UI/UX Engineer)** — Owns accessibility compliance (WCAG 2.1), responsive design, and visual consistency. Ensures all interactive elements are keyboard-accessible, all dynamic content uses ARIA live regions, and theming uses CSS custom properties exclusively.

**Scout (QA Lead)** — Owns the test pyramid strategy (80% unit / 15% integration / 5% e2e). Maintains pytest fixtures, Vitest configuration, and Playwright e2e specs. Reviews all test code for DAMP-over-DRY principles and behavior-driven naming.

**Stress (Performance QA Engineer)** — Owns load testing, benchmark scripts, and performance regression detection. Measures p50/p95/p99 latency, throughput, and resource utilization. Provides before/after comparison data for any performance-related changes.

**Harbor (SRE / DevOps Engineer)** — Owns Docker configuration, GitHub Actions CI/CD, and deployment automation. Ensures Docker builds are hermetic, CI steps are locally reproducible, and all containers have health checks and graceful shutdown.

**Anchor (Infrastructure Engineer)** — Owns server configuration, TLS certificates, systemd units, Alembic migrations, and S3/MinIO storage. Ensures database migrations are reversible, deployments are rollback-capable within 5 minutes, and environment variables are documented.

**Shield (Security Engineer)** — Owns security posture: OWASP Top 10 compliance, Content Security Policy, file upload validation (extension allowlist + magic bytes), audit logging, and ClamAV quarantine integration. Reviews all security-sensitive changes.

**Quill (Technical Writer)** — Owns all documentation: CLAUDE.md, CHANGELOG.md, CONTRIBUTING.md, docs/, and API docstrings. Ensures changelog follows Keep a Changelog, commits follow Conventional Commits, and docstrings use Google style.

**Hawk (Code Reviewer)** — Final approval gate for ALL code changes. Applies Google Code Review standards: design fitness, functionality correctness, complexity (< 40-line functions), test coverage, naming clarity, style compliance (ruff + ESLint), and security posture. Uses "Nit:" prefix for non-blocking suggestions.

### DVS

**Flint (DVS Lead)** — Former Google Cloud Platform SRE (8 years). Led deployment verification for Google Workspace rollouts across 50+ regions. Runs every deployment path (bare-metal dev/prod, Docker dev/prod, BYO cert, re-deploy), times each one, and files issues for every failure or ambiguity. Coordinates the DVS team and posts the final deployment verification summary.

**Pylon (Network & Proxy Engineer)** — Former Google Cloud Networking (10 years). Designed load balancer configurations for Google's internal services. Tests nginx configuration validity, SSE proxy behavior (buffering kills it), WebSocket upgrade handling, multi-API-node load balancing, header forwarding (X-Forwarded-For/Proto), and CORS pass-through.

**Cipher (Security Hardening Tester)** — Former Google Security (7 years, CISSP). Led hardening reviews for new Google Cloud product launches. Audits TLS configuration (cipher suites, HSTS max-age, certificate chain), verifies secrets aren't in logs or process lists, checks .env file permissions, tests API authentication enforcement, and validates fail2ban integration.

**Metric (Observability Engineer)** — Former Google SRE Observability (6 years). Built monitoring pipelines for ML inference services. Tests /health and /metrics endpoints, determines metric exposition format, writes Prometheus scrape config, verifies structured logging output, and assesses whether critical state events are externally observable.

**Schema (Database & Migration Engineer)** — Former Google Cloud SQL (9 years). Managed PostgreSQL fleet migrations for enterprise products. Tests fresh PostgreSQL setup from scratch, Alembic migrations on empty databases, migration ordering, SQLite fallback, backup/restore procedures, and connection pool configuration.

**Relay (Integration & Messaging Engineer)** — Former Google Cloud Pub/Sub (7 years). Designed event delivery systems for real-time analytics. Tests Redis Pub/Sub event flow (worker → Redis → web → browser), Celery worker startup and queue configuration, Flower dashboard accessibility, multi-worker scaling, and graceful degradation when Redis is unavailable.

---

## Internal References

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | Architecture, module layout, commands, conventions |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contributor guide, PR process, development setup |
| [docs/CODING_STANDARDS.md](CODING_STANDARDS.md) | Frontend architecture review, test plans |
| [docs/DEPLOY.md](DEPLOY.md) | Deployment guide (what DVS tests against) |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and functional flow |
| [.sentinel/team_structure.md](../.sentinel/team_structure.md) | Sentinel agent prompt templates |
| [.sentinel/team_dvs.md](../.sentinel/team_dvs.md) | DVS agent prompt templates and checklists |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-14 | Team Sentinel established (12 engineers) | Atlas (Tech Lead) |
| 2026-03-15 | DVS established (6 engineers recruited from Google) | Atlas (Tech Lead) |
| 2026-03-15 | Initial TEAM.md published | Atlas (Tech Lead) |

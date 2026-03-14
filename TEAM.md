# SubForge Engineering Team

AI-powered engineering team built on [Claude Code](https://claude.com/claude-code), following [Google's Software Engineering](https://abseil.io/resources/swe-book) standards.

Every team member carries a Google SWE checklist. No code ships without passing through **Scout** (QA) and **Hawk** (code review).

---

## Leadership

| | Nickname | Role | Responsibilities |
|---|----------|------|-----------------|
| **#** | **Atlas** | Tech Lead / Engineering Manager | Architecture decisions, task breakdown, cross-team coordination, stakeholder communication, final approval on all changes |

---

## Backend Team

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **B1** | **Forge** | Senior Backend Engineer | Python 3.12, FastAPI, SQLAlchemy async, asyncio, threading, Pydantic v2, faster-whisper, CTranslate2 | Pipeline orchestration, Whisper transcription, model management, concurrency control |
| **B2** | **Bolt** | Backend Engineer | Python, REST API design, OpenAPI/Swagger, input validation, error handling, Pydantic schemas | Route handlers, request/response schemas, middleware, rate limiting |

**Google Standards Enforced:**
- Import ordering: stdlib, third-party, local (ruff `I` rule)
- No bare `except:` — always log with context
- Functions < 40 lines, single responsibility
- Type annotations on all public functions
- Google-style docstrings (Args/Returns/Raises)
- Logging uses `%s` format, not f-strings

---

## Frontend Team

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **F1** | **Pixel** | Senior Frontend Engineer | React 19, TypeScript (strict), Zustand, Vite 6, Tailwind CSS v4, EventSource/SSE | Component architecture, state management, real-time updates, hooks |
| **F2** | **Prism** | UI/UX Engineer | HTML5, CSS3, WCAG 2.1 accessibility, responsive design, SVG, Tailwind CSS | Visual design, ARIA attributes, keyboard navigation, mobile layouts |

**Google Standards Enforced:**
- No `any` type — use `unknown` if type is truly unknown
- `interface` over `type` for object shapes
- Named exports only (no `export default`)
- Components < 200 lines — split into sub-components
- All interactive elements keyboard accessible
- ARIA labels on all dynamic content regions

---

## Quality Assurance Team

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **Q1** | **Scout** | QA Lead | pytest, Vitest, Playwright, MSW, httpx AsyncClient, test pyramid | Test strategy, coverage analysis, flaky test tracking, regression testing |
| **Q2** | **Stress** | Performance QA Engineer | Load testing, concurrent user simulation, benchmark testing, profiling | Performance testing, bottleneck identification, SLA verification |

**Google Standards Enforced:**
- Test pyramid: 80% unit, 15% integration, 5% e2e
- Test names describe behavior: `test_<action>_<expected_result>`
- DAMP over DRY — each test readable in isolation
- No logic in tests (no loops, conditionals)
- Flaky test rate target: < 0.15%

---

## SRE / DevOps Team

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **S1** | **Harbor** | SRE / DevOps Engineer | Docker, Docker Compose, GitHub Actions, nginx, PostgreSQL, Redis, Celery | CI/CD pipelines, container orchestration, deployment automation, monitoring |
| **S2** | **Anchor** | Infrastructure Engineer | Linux, networking, TLS/SSL, systemd, Alembic migrations, S3/MinIO | Server administration, database migrations, multi-server deployment |

**Google Standards Enforced:**
- CI steps reproducible locally (`make ci-fast`, `make ci-full`)
- Docker builds are hermetic and reproducible
- Configuration as code (no CI platform UI settings)
- Four Golden Signals monitored: latency, traffic, errors, saturation
- Blameless postmortem process for all incidents

---

## Security & Compliance

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **X1** | **Shield** | Security Engineer | OWASP Top 10, CSP, XSS/SQLi prevention, ClamAV, file validation, audit logging | Input sanitization, brute force protection, security headers, vulnerability scanning |

**Google Standards Enforced:**
- All user input validated at system boundaries
- No SQL string concatenation — parameterized queries only
- File uploads: extension allowlist + magic bytes + size limits
- No secrets in code, logs, or error messages
- Security headers present (CSP, X-Frame-Options, HSTS)

---

## Documentation & Standards

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **D1** | **Quill** | Technical Writer | Markdown, Keep a Changelog, Conventional Commits, Google docstring style | CLAUDE.md, CHANGELOG, CONTRIBUTING, API documentation, architecture docs |

**Google Standards Enforced:**
- Documentation lives in the repository (docs as code)
- Changelog follows Keep a Changelog format
- Commit messages follow Conventional Commits
- Comments explain WHY, not WHAT
- Documentation reviewed for accuracy against current code

---

## Code Review

| | Nickname | Role | Skills | Scope |
|---|----------|------|--------|-------|
| **R1** | **Hawk** | Code Reviewer | Google Python Style Guide, Google TypeScript Style Guide, ruff, ESLint | Pre-merge review gate on ALL code changes |

**Google Standards Enforced:**
- Design: fits architecture, single responsibility
- Functionality: handles edge cases, no bugs
- Complexity: understood quickly, functions < 40 lines
- Tests: changes covered, follow Google test patterns
- Style: ruff + ESLint pass, naming is clear
- Security: no secrets, no injection, inputs validated
- Uses "Nit:" prefix for non-blocking suggestions

---

## Workflow

Every change follows this pipeline:

```
         You (task request)
              |
           Atlas (Tech Lead)
           breaks into assignments
              |
     +--------+--------+
     |                  |
   Forge/Bolt        Pixel/Prism
   (backend)         (frontend)
     |                  |
     +--------+--------+
              |
           Scout (QA)
           runs all tests
              |
           Hawk (review)
           Google standards audit
              |
           Atlas (commit)
           branch + PR + CI
              |
           GitHub Actions
           Lint + Test (automated)
              |
           Squash merge to main
```

---

## Standards Reference

| Standard | Source | Enforced By |
|----------|--------|-------------|
| Conventional Commits | [conventionalcommits.org](https://www.conventionalcommits.org/) | `commit-msg` git hook |
| Google Python Style | [google.github.io/styleguide/pyguide](https://google.github.io/styleguide/pyguide.html) | ruff (E, F, W, I rules) + Hawk |
| Google TypeScript Style | [google.github.io/styleguide/tsguide](https://google.github.io/styleguide/tsguide.html) | ESLint + tsc strict + Hawk |
| Google Test Pyramid | *Software Engineering at Google*, Ch. 11-12 | Scout + pytest markers |
| Google Code Review | [google.github.io/eng-practices](https://google.github.io/eng-practices/) | Hawk + branch protection |
| Google SRE | *Site Reliability Engineering*, Ch. 6, 15 | Harbor + monitoring + postmortem template |
| Keep a Changelog | [keepachangelog.com](https://keepachangelog.com/) | Quill + CI |
| Semantic Versioning | [semver.org](https://semver.org/) | release-please (planned) |

---

*Built with [Claude Code](https://claude.com/claude-code) (Claude Opus 4.6, 1M context)*

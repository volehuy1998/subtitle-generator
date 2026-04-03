# Contributing to SubForge

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend |
| Node.js | 20+ | Frontend |
| ffmpeg | 6+ | Media processing |
| Docker | 24+ | Containerized deployment (optional) |

## Setup

```bash
git clone https://github.com/volehuy1998/subtitle-generator.git
cd subtitle-generator

# Backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
cd frontend && npm install && npm run build && cd ..

# Environment
cp .env.example .env
mkdir -p uploads outputs logs

# Run
python main.py                    # backend at http://localhost:8000
cd frontend && npm run dev        # frontend at http://localhost:5173 (proxies to :8000)
```

## Git Workflow

We use **GitHub Flow** with a protected `main` branch.

1. Branch from `main`: `feat/...`, `fix/...`, `refactor/...`, `security/...`
2. Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) (enforced by hook)
3. Open a PR, pass CI, get 1 review
4. Squash merge to `main`

### Commit Format

```
<type>(<scope>): <description>
```

**Types**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `ci`, `build`, `chore`, `security`

**Scopes**: `pipeline`, `transcribe`, `translate`, `embed`, `sse`, `api`, `db`, `auth`, `middleware`, `health`, `ui`, `store`, `hooks`, `docker`, `deploy`, `config`

## Pull Requests

1. Fill out the PR template (summary, test plan, checklist)
2. Link an issue with `Closes #N`
3. CI must pass: lint, tests, build
4. At least 1 review required before merge

### UI Changes

Visual changes go through staging first:
1. Set `NEWUI_BRANCH` in `.env` to your branch
2. Deploy to staging: `./scripts/deploy-profile.sh newui`
3. Get approval, then merge to `main`

## Code Style

### Python

- **Linter**: `ruff check .` (rules from `pyproject.toml`)
- **Formatter**: `ruff format .`
- No line length limit (E501 ignored)
- Type hints on public functions
- New routes registered in `app/routes/__init__.py`

### TypeScript

- **Linter**: `cd frontend && npm run lint`
- **Build check**: `cd frontend && npm run build` (tsc + vite)
- Strict mode, no `any` types, no `console.log`
- Functional components, Zustand for state

## Testing

### Backend (pytest)

```bash
pytest tests/ -v --tb=short       # all tests (~3,295)
pytest tests/test_sprint17.py -v  # single file
```

Tests mock GPU/ML deps in `conftest.py`. Use `httpx.AsyncClient` with `ASGITransport`.

### Frontend (Vitest)

```bash
cd frontend
npm run test          # all tests (~372)
npm run coverage      # coverage report
```

Uses Vitest + Testing Library + MSW for API mocking.

### E2E (Playwright)

```bash
npx playwright install
pytest tests/e2e/ -v  # 129 tests
```

### Coverage Target

80% minimum. All new features require tests.

## Pre-Commit Hook

The repo ships a pre-commit hook that runs ruff lint, format check, secret scanning, and blocked file detection. It mirrors CI checks.

```bash
chmod +x .git/hooks/pre-commit
```

## Architecture Reference

See [CLAUDE.md](CLAUDE.md) for the full architecture, module layout, and environment variable reference.

# Coding Standards

## Python (Backend)

### Style

- **Linter/Formatter**: ruff (rules from `pyproject.toml`)
- **Line length**: No limit (E501 ignored)
- **Type hints**: Required on all public functions. Use `Optional[]` for nullable params.
- **Docstrings**: Google style (Args/Returns/Raises) on public functions
- **Imports**: stdlib, third-party, local (enforced by ruff I rule)
- **Error handling**: `HTTPException` for client errors, global handler for 500s. No bare `except:`.
- **Logging**: `logger.info("msg: %s", var)` -- not f-strings. Never remove existing logging.

### Patterns

- **Routes**: One router per feature domain in `app/routes/`. Register in `app/routes/__init__.py`.
- **Services**: One service per domain in `app/services/`. Business logic lives here, not in routes.
- **Config**: All settings in `app/config.py` with env var overrides and defaults.
- **Concurrency**: `asyncio.to_thread()` for blocking I/O. `threading.Semaphore` for task limits.
- **ORM**: SQLAlchemy 2.0 async (asyncpg for PostgreSQL, aiosqlite for SQLite).
- **Migrations**: Alembic with auto-generated revisions.

### Linting

```bash
ruff check .              # lint (rules from pyproject.toml)
ruff format --check .     # format check
```

## TypeScript (Frontend)

### Style

- **Strict mode**: enabled, no `any` types allowed
- **Linter**: ESLint with `--max-warnings 0`
- **Components**: Functional with hooks, one per file, co-located by feature
- **State**: Zustand only. Stores: `taskStore.ts`, `uiStore.ts`. No Redux, no Context for global state.
- **Styling**: Tailwind CSS v4 with CSS custom properties for theming
- **API client**: Typed fetch wrapper in `api/client.ts`. All responses typed in `api/types.ts`.
- **No `console.log`** in committed code

### Build Check

```bash
cd frontend
npm run lint              # ESLint
npm run build             # tsc + vite build
```

## File Organization

Organize by feature, not by file type:

```
src/components/
  transcribe/    TranscribeForm, ConfirmationDialog
  embed/         EmbedTab, EmbedPanel, StyleOptions
  progress/      ProgressView, PipelineSteps, LivenessIndicator
  output/        OutputPanel, DownloadButtons, TimingBreakdown
  system/        ConnectionBanner, HealthPanel, TaskQueuePanel
  layout/        AppHeader
```

### Size Limits

- **Functions**: Under 50 lines, single responsibility
- **Files**: Under 800 lines. Extract utilities from large modules.
- **Typical file**: 200-400 lines

## Testing

### Requirements

- **Coverage**: 80% minimum for new code
- **TDD**: Write tests first, implement to pass, refactor
- **Backend**: pytest with `httpx.AsyncClient` + `ASGITransport`. Mock GPU/ML deps in `conftest.py`.
- **Frontend**: Vitest + Testing Library + MSW for API mocking
- **E2E**: Playwright for critical user flows

### Running Tests

```bash
# Backend
pytest tests/ -v --tb=short       # all (3,295 tests)
pytest tests/test_sprint17.py -v  # single file

# Frontend
cd frontend && npm run test       # all (372 tests)
cd frontend && npm run coverage   # with coverage

# E2E
pytest tests/e2e/ -v              # Playwright (129 tests)

# Full CI check
make ci-fast                      # lint + fast tests
make ci-full                      # lint + all tests + coverage + build
```

## Security Practices

- No hardcoded secrets. Use environment variables or `.env`.
- Validate all user input at system boundaries (Pydantic, file validation, magic bytes).
- Use `safe_path()` for all file operations (path traversal prevention).
- Use `validate_ffmpeg_filter_value()` for ffmpeg parameters (injection prevention).
- Sanitize error messages before returning to clients (no paths, DB URLs, or tracebacks).
- HMAC-signed audit entries for sensitive operations.

## Commit Standards

[Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) enforced by `commit-msg` hook.

```
<type>(<scope>): <description>
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for types, scopes, and examples.

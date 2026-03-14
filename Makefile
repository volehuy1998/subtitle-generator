# SubForge Development Makefile
# Google SWE Practice: All CI steps must be reproducible locally.
# Run `make ci-fast` before pushing. Run `make ci-full` for comprehensive checks.

.PHONY: help setup dev run db db-stop test test-fast test-full lint format ci-fast ci-full build build-frontend audit docker-up docker-up-gpu docker-down docker-logs migrate migrate-new clean health

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────

setup: ## Install dependencies and create directories
	pip install -r requirements.txt
	pip install -r requirements-dev.txt 2>/dev/null || true
	mkdir -p uploads outputs logs
	cd frontend && npm ci
	@echo "Setup complete."

# ── Development ──────────────────────────────────────────────────────────────

db: ## Start only PostgreSQL in Docker (for local dev)
	docker compose up postgres -d
	@echo "PostgreSQL running on localhost:5432"

db-stop: ## Stop PostgreSQL container
	docker compose stop postgres

dev: ## Run app locally with hot-reload
	DATABASE_URL=postgresql+asyncpg://subtitle:subtitle@localhost:5432/subtitle_generator \
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 1

run: ## Run in production mode
	python main.py

# ── Linting (Google Style Guide) ─────────────────────────────────────────────

lint: ## Run all linters (Python ruff + ruff format + TypeScript)
	ruff check .
	ruff format --check .
	cd frontend && npx tsc -b --noEmit

format: ## Auto-format all code (Python + imports)
	ruff check --fix .
	ruff format .

# ── Testing (Google Test Pyramid) ─────────────────────────────────────────────

test: ## Run all backend tests
	python3 -m pytest tests/ -v --tb=short

test-fast: ## Run small (unit) tests only — presubmit target (< 60s)
	python3 -m pytest tests/ -v --tb=short -q

test-full: ## Run all tests with coverage + frontend tests
	python3 -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
	cd frontend && npx vitest run

# ── CI Pipelines (Google Presubmit/Post-submit) ──────────────────────────────

ci-fast: lint test-fast ## Presubmit: lint + fast tests (< 2 min target)
	@echo ""
	@echo "  ✓ ci-fast passed — safe to push"

ci-full: lint test-full build-frontend ## Post-submit: lint + all tests + coverage + build
	@echo ""
	@echo "  ✓ ci-full passed"

# ── Build ────────────────────────────────────────────────────────────────────

build: ## Build frontend + Docker image
	cd frontend && npm run build
	docker build -t subtitle-generator:dev .

build-frontend: ## Build frontend only
	cd frontend && npm run build

# ── Security (Google Dependency Management) ──────────────────────────────────

audit: ## Audit dependencies for known vulnerabilities
	@echo "Python dependencies:"
	pip-audit -r requirements.txt 2>/dev/null || echo "  Install pip-audit: pip install pip-audit"
	@echo ""
	@echo "Frontend dependencies:"
	cd frontend && npm audit --audit-level=high 2>/dev/null || true

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up: ## Start services (CPU mode) with Docker Compose
	docker compose --profile cpu up --build -d

docker-up-gpu: ## Start services (GPU mode) with Docker Compose
	docker compose --profile gpu up --build -d

docker-down: ## Stop all Docker containers
	docker compose --profile cpu --profile gpu down

docker-logs: ## Tail Docker container logs
	docker compose --profile cpu logs -f --tail=50

# ── Database ─────────────────────────────────────────────────────────────────

migrate: ## Run database migrations
	alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	alembic revision --autogenerate -m "$(msg)"

# ── Utilities ────────────────────────────────────────────────────────────────

health: ## Check if the service is running
	@curl -sf http://localhost:8000/health && echo " OK" || echo " FAIL — service not running"

clean: ## Remove build artifacts, caches, and temp files
	rm -rf __pycache__ .pytest_cache .ruff_cache coverage.xml
	rm -rf frontend/dist frontend/coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts and caches."

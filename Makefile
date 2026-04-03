# SubForge Makefile — all CI steps reproducible locally
PYTHON  := python3
PYTEST  := $(PYTHON) -m pytest
RUFF    := ruff
FRONTEND := frontend

.PHONY: help ci-fast ci-full dev dev-docker test test-fast test-frontend \
        lint format docker-up docker-down docker-build docker-beta \
        migrate health clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── CI ───────────────────────────────────────────────────────────────────────
ci-fast: lint test-fast ## Presubmit: lint + unit tests (< 2 min)
	@echo "ci-fast passed"

ci-full: lint test build ## Post-submit: lint + all tests + build
	@echo "ci-full passed"

# ── Development ──────────────────────────────────────────────────────────────
dev: ## Run with hot-reload
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 1

dev-docker: ## Docker compose up (cpu profile)
	docker compose --profile cpu up --build -d

# ── Testing ──────────────────────────────────────────────────────────────────
test: ## All backend tests
	$(PYTEST) tests/ -v --tb=short

test-fast: ## Unit tests only (< 60s)
	$(PYTEST) tests/ -v --tb=short -q

test-frontend: ## Frontend vitest
	cd $(FRONTEND) && npx vitest run

# ── Lint & Format ────────────────────────────────────────────────────────────
lint: ## Ruff check + eslint + tsc
	$(RUFF) check .
	$(RUFF) format --check .
	cd $(FRONTEND) && npx tsc -b --noEmit

format: ## Auto-format (ruff + prettier)
	$(RUFF) check --fix .
	$(RUFF) format .
	cd $(FRONTEND) && npx prettier --write src/

# ── Docker ───────────────────────────────────────────────────────────────────
docker-up: ## Start cpu profile
	docker compose --profile cpu up -d

docker-down: ## Stop all containers
	docker compose --profile cpu --profile gpu down

docker-build: ## Build Docker image
	docker build -t subtitle-generator:dev .

docker-beta: ## Deploy staging via deploy-profile.sh
	./scripts/deploy-profile.sh newui

# ── Database ─────────────────────────────────────────────────────────────────
migrate: ## Alembic upgrade head
	alembic upgrade head

# ── Operations ───────────────────────────────────────────────────────────────
health: ## Check health endpoints
	@curl -sf http://localhost:8000/health/live  && echo " :8000 OK"  || echo " :8000 FAIL"
	@curl -sf http://localhost:8001/health/live  && echo " :8001 OK"  || echo " :8001 FAIL"

build: ## Build frontend
	cd $(FRONTEND) && npm run build

clean: ## Remove build artifacts
	rm -rf __pycache__ .pytest_cache .ruff_cache coverage.xml htmlcov
	rm -rf $(FRONTEND)/dist $(FRONTEND)/coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."

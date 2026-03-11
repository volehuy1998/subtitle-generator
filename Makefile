.PHONY: help setup dev test lint docker-up docker-up-gpu docker-down docker-logs migrate clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and create directories
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	mkdir -p uploads outputs logs
	@echo "Setup complete. Copy .env.example to .env and configure."

db: ## Start only PostgreSQL in Docker (for local dev)
	docker compose up postgres -d
	@echo "PostgreSQL running on localhost:5432"
	@echo "Set DATABASE_URL=postgresql+asyncpg://subtitle:subtitle@localhost:5432/subtitle_generator"

db-stop: ## Stop PostgreSQL container
	docker compose stop postgres

dev: ## Run app locally with hot-reload (start DB first with 'make db')
	DATABASE_URL=postgresql+asyncpg://subtitle:subtitle@localhost:5432/subtitle_generator \
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 1

run: ## Run in production mode
	python main.py

test: ## Run all tests
	pytest tests/ -v --tb=short

test-quick: ## Run tests without verbose output
	pytest tests/ -q

lint: ## Run ruff linter
	ruff check . --select E,F,W --ignore E501

docker-up: ## Start services (CPU mode) with Docker Compose
	docker compose --profile cpu up --build -d

docker-up-gpu: ## Start services (GPU mode) with Docker Compose
	docker compose --profile gpu up --build -d

docker-down: ## Stop all Docker containers
	docker compose --profile cpu --profile gpu down

docker-logs: ## Tail Docker container logs
	docker compose --profile cpu logs -f --tail=50

migrate: ## Run database migrations
	alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	alembic revision --autogenerate -m "$(msg)"

clean: ## Remove uploads, outputs, and logs
	rm -rf uploads/* outputs/* logs/*
	@echo "Cleaned uploads, outputs, and logs directories."

health: ## Check if the service is running
	@curl -sf http://localhost:8000/health && echo " OK" || echo " FAIL - service not running"

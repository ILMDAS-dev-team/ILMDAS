# ILMDAS developer convenience targets.
# Make is common on macOS/Linux and Git Bash/WSL on Windows.
# PowerShell users can run the underlying commands from docs/ILMDAS_Dev_Local_Setup.md.
#
# Local model matches OUPDMS: Django in Docker, Next.js native.
# DC = docker compose -f docker-compose.dev.yml

DC = docker compose -f docker-compose.dev.yml

.DEFAULT_GOAL := help
.PHONY: help up down logs ps migrate superuser backend-shell backend-lint backend-test \
        backend-smoke frontend-install frontend-lint frontend-test frontend-build \
        frontend-e2e frontend-check

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n", $$1, $$2}'

up: ## Build and start backend + Postgres + Elasticsearch + MinIO
	$(DC) up -d --build

down: ## Stop local Docker services
	$(DC) down

logs: ## Tail backend logs
	$(DC) logs -f backend

ps: ## Show running compose services
	$(DC) ps

migrate: ## Apply Django migrations in the backend container
	$(DC) exec backend python manage.py migrate

superuser: ## Create a Django admin user in the backend container
	$(DC) exec backend python manage.py createsuperuser

backend-shell: ## Open a shell in the backend container
	$(DC) exec backend bash

backend-lint: ## Ruff + format check + mypy in the backend container
	$(DC) exec backend ruff check .
	$(DC) exec backend ruff format --check .
	$(DC) exec backend mypy apps config

backend-test: ## Pytest with coverage gate (>=80%) in the backend container
	$(DC) exec backend python -m pytest apps/ --cov=apps --cov-report=term-missing --cov-fail-under=80 -v

backend-smoke: ## Live GET /api/v1/health/ (compose must be up on :8010)
	cd backend && python -m pytest -m smoke -v -o addopts=

frontend-install: ## Install frontend dependencies
	cd frontend && npm ci

frontend-lint: ## ESLint + TypeScript + Prettier check
	cd frontend && npm run lint && npm run type-check && npm run format:check

frontend-test: ## Jest with coverage
	cd frontend && npm run test:coverage

frontend-build: ## Next.js production build
	cd frontend && npm run build

frontend-e2e: ## Playwright Chromium smoke
	cd frontend && npm run test:e2e

frontend-check: ## All frontend quality gates in one command
	cd frontend && npm run check

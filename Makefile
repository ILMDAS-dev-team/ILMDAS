# ILMDAS developer convenience targets.
# Make is common on macOS/Linux and Git Bash/WSL on Windows.
# PowerShell users can run the underlying commands from docs/ILMDAS_Dev_Local_Setup.md.
#
# backend-install uses a Unix venv path. On Windows PowerShell use:
#   python -m venv backend\.venv
#   backend\.venv\Scripts\pip install -r backend\requirements\development.txt

.DEFAULT_GOAL := help
.PHONY: help up down backend-install backend-lint backend-test frontend-install \
        frontend-lint frontend-test frontend-build frontend-e2e migrate

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n", $$1, $$2}'

up: ## Start Postgres, Elasticsearch, and MinIO
	docker compose -f docker-compose.dev.yml up -d

down: ## Stop local Docker services
	docker compose -f docker-compose.dev.yml down

backend-install: ## Create backend/.venv and install development requirements (Unix/WSL)
	python -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements/development.txt

backend-lint: ## Ruff + format check + mypy
	cd backend && ruff check . && ruff format --check . && mypy apps config

backend-test: ## Pytest with coverage gate (>=80%)
	cd backend && python -m pytest apps/ --cov=apps --cov-report=term-missing --cov-fail-under=80 -v

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

migrate: ## Apply Django migrations (requires backend/.env and Postgres)
	cd backend && python manage.py migrate

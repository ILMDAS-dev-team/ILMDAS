.PHONY: up down backend-install backend-lint backend-test frontend-install frontend-lint frontend-test frontend-e2e migrate

up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

backend-install:
	python -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements/development.txt

backend-lint:
	cd backend && ruff check . && ruff format --check . && mypy apps config

backend-test:
	cd backend && python -m pytest

frontend-install:
	cd frontend && npm install

frontend-lint:
	cd frontend && npm run lint && npm run type-check && npm run format:check

frontend-test:
	cd frontend && npm test

frontend-e2e:
	cd frontend && npm run test:e2e

migrate:
	cd backend && python manage.py migrate

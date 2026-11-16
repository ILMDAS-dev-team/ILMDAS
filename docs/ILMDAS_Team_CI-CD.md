# ILMDAS continuous integration

Every pull request and every push to `main` or `develop` runs [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).

The workflow has five jobs:

1. **Backend lint.** Install `backend/requirements/development.txt`, then run Ruff, `ruff format --check`, and mypy.
2. **Backend tests.** Run pytest after lint succeeds. Pytest uses the test settings and SQLite. It does not need PostgreSQL, Elasticsearch, or MinIO.
3. **Frontend lint.** `npm ci`, then ESLint, `tsc --noEmit`, and Prettier.
4. **Frontend tests.** `npm test` runs Jest. The tests check the public and staff shells, the 360px layout rules, and the correlation identifier on the API client.
5. **Frontend smoke.** Playwright opens the public page and the staff page in Chromium.

A failing command fails the job. The workflow does not set `continue-on-error` on the test steps.

Deployment to the OSTA data center is not part of this workflow. Production network zones and TLS are specified later in the system design.

## What to run before you open a pull request

Install the git hooks once, from the repository root, after the backend virtual environment exists:

```powershell
backend\.venv\Scripts\pre-commit install
```

The frontend hooks call ESLint and Prettier through Python. From `backend`:

```powershell
ruff check .
ruff format --check .
mypy apps config
python -m pytest
```

From `frontend`:

```powershell
npm run lint
npm run type-check
npm run format:check
npm test
npm run test:e2e
```

## What the tests are protecting

- The API does not start when `SECRET_KEY` or `DATABASE_URL` is missing.
- `backend/.env.example` contains names and empty values.
- Each Django app has models, migrations, and tests packages.
- A PostgreSQL URL selects the PostgreSQL engine, and migrations apply.
- The catalogue index can be created and deleted outside production.
- An upload stores a private `s3://` reference and a SHA-256 checksum, and an anonymous read is rejected.
- Health returns a failed status when a store is unreachable.
- A missing IIIF endpoint is `not_configured`. A configured client requests `info.json` and does not publish an image route.
- Validation and authentication errors use different codes, a correlation identifier, and no stack trace.

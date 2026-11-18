# ILMDAS continuous integration and team workflow

Every pull request and every push to `main` or `develop` runs
[`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).

Deployment to the OSTA data center is **not** part of this workflow. There is no
Docker image publish, staging auto-deploy, or production `workflow_dispatch`.
See [ILMDAS_Tech_Lead_Env_Setup.md](ILMDAS_Tech_Lead_Env_Setup.md) for the stub
checklist when that work is approved.

Prove a laptop is green with
[ILMDAS_Setup_Verification_Guide.md](ILMDAS_Setup_Verification_Guide.md).
Contribution rules are in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Roles

| Role | What you do |
|---|---|
| Developers | Branch from `develop`, write tests, open PRs, fix CI failures |
| Reviewers | Review PRs into `develop`; request changes until checks and standards pass |
| Tech lead | Owns CI config, Codecov token, branch protection; later owns deploy |

`.github/CODEOWNERS` is a **scaffold placeholder**. Per-app GitHub owners are
**not assigned yet**. Reviewers are requested manually until that file is filled
(same path style as OUPDMS, deferred).

## Branches and commits

- Integration branch: `develop`
- Release / protected: `main`
- Feature work: `feature/<short-description>` from an up-to-date `develop`
- Prefer conventional commits: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`
- Release PRs go from `develop` into `main`

## One-time hooks

After the backend virtual environment exists, from the repository root:

```powershell
backend\.venv\Scripts\pre-commit install
```

Hooks run Ruff (backend), ESLint and Prettier (frontend), detect-secrets, and
file hygiene. They do **not** run mypy, pytest, or `tsc` (same as OUPDMS).

## CI jobs

A failing command fails the job. Jobs do not set `continue-on-error` on test steps.

| # | Job | What it runs | Reproduce locally |
|---|---|---|---|
| 1 | Backend lint | Ruff, `ruff format --check`, mypy | `cd backend` → `ruff check .` → `ruff format --check .` → `mypy apps config` |
| 2 | Backend tests | `pytest apps/ --cov=apps --cov-report=xml --cov-fail-under=80` + Codecov | `cd backend` → `python -m pytest apps/ --cov=apps --cov-fail-under=80 -v` |
| 3 | Frontend lint | ESLint, `tsc --noEmit`, Prettier | `cd frontend` → `npm run lint` → `npm run type-check` → `npm run format:check` |
| 4 | Frontend tests | `npm run test:coverage`, `npm run build`, Codecov | same two commands from `frontend` |
| 5 | Frontend smoke | Playwright Chromium on public + staff | `cd frontend` → `npx playwright install chromium` → `npm run test:e2e` |

Suite-wide backend coverage must stay at **80%**. Codecov patch target is **90%**
([`codecov.yml`](../codecov.yml)). Set repository secret `CODECOV_TOKEN` or the
upload steps fail (`fail_ci_if_error: true`).

Jest collects coverage but does **not** enforce a Jest `%` threshold (same as
OUPDMS). Playwright smoke runs on every PR (stronger than OUPDMS’s staging-gated
E2E). PostGIS/GDAL, Redis integration, and deploy jobs are intentionally absent.

## What to run before you open a pull request

Backend, from `backend` with the virtual environment active:

```powershell
ruff check .
ruff format --check .
mypy apps config
python -m pytest apps/ --cov=apps --cov-fail-under=80 -v
```

Frontend, from `frontend`:

```powershell
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
npm run test:e2e
```

Or use Make (Git Bash / WSL / macOS / Linux): `make backend-lint`,
`make backend-test`, `make frontend-lint`, `make frontend-test`,
`make frontend-build`, `make frontend-e2e`. See `make help`.

## What the tests are protecting

- The API does not start when `SECRET_KEY` or `DATABASE_URL` is missing.
- `backend/.env.example` contains names and empty values.
- Each Django app has models, migrations, and tests packages.
- A PostgreSQL URL selects the PostgreSQL engine, and migrations apply.
- The catalogue index can be created and deleted outside production.
- An upload stores a private `s3://` reference and a SHA-256 checksum, and an
  anonymous read is rejected.
- Health returns a failed status when a store is unreachable.
- A missing IIIF endpoint is `not_configured`. A configured client requests
  `info.json` and does not publish an image route.
- Validation and authentication errors use different codes, a correlation
  identifier, and no stack trace.
- Public shell has no Administration / staff link; layout works at 360px width.

## Cheat sheet

| Goal | Command |
|---|---|
| Start infra | `make up` or `docker compose -f docker-compose.dev.yml up -d` |
| Stop infra | `make down` |
| Backend coverage tests | `make backend-test` |
| Frontend coverage | `make frontend-test` |
| Production Next build | `make frontend-build` |
| Playwright smoke | `make frontend-e2e` |

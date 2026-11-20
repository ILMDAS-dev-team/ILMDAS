# ILMDAS local setup

This is the developer setup for a Windows machine. The same Docker and npm commands
work in bash / WSL / macOS.

The business baseline (BRS) and the SRS fix the stack: Next.js, Django, PostgreSQL,
Elasticsearch, S3-compatible storage, and IIIF/Cantaloupe. Flutter is not part of
this setup. Deployment to the OSTA data center is not part of this setup.

**How local runtime is split (same idea as OUPDMS):**

1. **Backend stack runs in Docker.** Django, PostgreSQL, Elasticsearch, and MinIO
   start with `docker compose -f docker-compose.dev.yml up -d --build`. You do not
   need a host Python install for day-to-day API work.
2. **Frontend runs natively.** Next.js uses `npm run dev` for fast hot reload.

ILMDAS does **not** run Celery, Redis, Nginx, or PostGIS locally. Those are either
out of scope or reserved for later deploy work.

Prove a fresh machine end-to-end with
[ILMDAS_Setup_Verification_Guide.md](ILMDAS_Setup_Verification_Guide.md).
Team CI workflow is in [ILMDAS_Team_CI-CD.md](ILMDAS_Team_CI-CD.md).

## Install the tools

1. Install Git and confirm `git --version`.
2. Install Node.js 20 and confirm `node --version` and `npm --version`.
3. Install Docker Desktop, start it, and confirm `docker compose version`.

You do **not** need a local PostgreSQL, Elasticsearch, MinIO, or Python install for
the default path. Docker provides the API and infra. (CI and optional host tooling
may still use Python.)

## Get the code

```powershell
git clone <repository-url> ilmdas
cd ilmdas
```

If you already have the folder, open a terminal in `ilmdas`.

## Start the backend stack

```powershell
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml ps
```

Or: `make up`.

Wait until `backend`, `postgres`, `elasticsearch`, and `minio` are running.
`minio-init` creates the private bucket `ilmdas-files` and then exits.
Elasticsearch can take a minute the first time.

Confirm search from the host:

```powershell
curl http://localhost:9200
```

You should see a JSON body with a cluster name. If the connection is refused, Docker
is not running or port 9200 is already taken.

The API stores a checksum and an `s3://` reference. It does not store the file in
PostgreSQL, and it does not return a public URL. Optional: open the object-storage
console at http://localhost:9011 (user `ilmdas` / password `ilmdas-local-only`) to
inspect the bucket. Leave anonymous access off.

Compose already injects backend environment (Postgres/ES/MinIO service hostnames).
You do **not** need `backend/.env` for the Docker path. `backend/.env.example`
remains names-only for documentation and optional host runs.

## Migrate and check the API

```powershell
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
curl http://localhost:8010/api/v1/health/
```

Or: `make migrate`.

- `"status": "ok"` means the database, Elasticsearch, and the bucket all answered.
- `"status": "failed"` with HTTP 503 means a check is `not configured` or
  `unreachable`. Start the matching container or re-run compose so
  `minio-init` can create the bucket.

Create a Django admin user only when you need the admin site:

```powershell
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

Or: `make superuser`. The admin site is http://localhost:8010/admin/. It is not
linked from the public website.

## Web application

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3010/ and http://localhost:3010/staff. Narrow the browser to
360px. The navigation wraps and the page stays inside the viewport. The public header
does not contain Administration or a staff link.

The staff IIIF page is http://localhost:3010/staff/status. With an empty
`IIIF_ENDPOINT` it must not claim that viewing succeeded.

`frontend/.env` is optional. Set `NEXT_PUBLIC_API_URL=http://localhost:8010` if the
API is not on that address. The client sends `X-Correlation-ID` on every request.

## Daily routine

1. `docker compose -f docker-compose.dev.yml up -d --build` (or `make up`)
2. In another terminal: `cd frontend` → `npm run dev`
3. Before a PR, run the quality commands below (or the matching `make` targets)

## Checks before a change

Install git hooks once (needs a local Python with `pre-commit`, or use the backend
container’s environment if you prefer):

```powershell
docker compose -f docker-compose.dev.yml exec backend pip show pre-commit
docker compose -f docker-compose.dev.yml exec backend pre-commit install
```

If `pre-commit install` from the container cannot write your host `.git/hooks`,
install `pre-commit` once on the host and run `pre-commit install` from the repo root.

Hooks run Ruff, ESLint, Prettier, secret scanning, and file hygiene. They do **not**
run mypy, pytest, or `tsc`.

Backend (in Docker):

```powershell
docker compose -f docker-compose.dev.yml exec backend ruff check .
docker compose -f docker-compose.dev.yml exec backend ruff format --check .
docker compose -f docker-compose.dev.yml exec backend mypy apps config
docker compose -f docker-compose.dev.yml exec backend python -m pytest apps/ --cov=apps --cov-fail-under=80 -v
```

Or: `make backend-lint` and `make backend-test`.

Frontend, from `frontend`:

```powershell
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
npm run test:e2e
```

Or one line (same gates): `make frontend-check`
Or from `frontend`: `npm run check`

Local smoke (compose must be up; CI jobs exist but are **Skipped** via `if: false`):

```powershell
make backend-smoke
make frontend-e2e
```

`make backend-smoke` GETs `http://localhost:8010/api/v1/health/` and expects
`"status": "ok"`. Override the base URL with `SMOKE_BASE_URL` if needed.

Pytest uses SQLite inside the container for unit tests, so it does not need live
Postgres for those cases. `migrate` against the compose database is the check that
the same migrations apply to PostgreSQL. Smoke is excluded from default pytest
via `-m "not smoke"`.

CI uploads coverage to Codecov (patch target 90%) when `CODECOV_TOKEN` is set.
Without the secret, upload is skipped; the coverage gates still apply.

## Stop

```powershell
docker compose -f docker-compose.dev.yml down
```

Or: `make down`. Add `-v` only when you intend to delete the local database, index,
and bucket data.

## Optional: run the API on the host

Only if you prefer a host venv instead of the backend container. Install Python
3.12+, copy `backend/.env.example` to `backend/.env`, and use **localhost** URLs
(Postgres on host port **5433**, object storage on **9010**). Keep compose running for
infra only, or stop the `backend` service. This path is optional; the default team
path is Docker.

## Troubleshooting

| What you see | What to do |
|---|---|
| Backend container restarting | `docker compose -f docker-compose.dev.yml logs backend` |
| Health says the database is unreachable | Wait for postgres healthy; confirm migrate ran |
| Health says object storage is unreachable | Confirm `minio` is Up; check `minio-init` exited 0 |
| Port 5433, 8010, 9010, or 9200 is in use | Stop the other process or change the host port in compose |
| Coverage below 80% | Read the missing-lines report; add tests before changing omit rules |
| Codecov upload skipped in CI | Optional until `CODECOV_TOKEN` is set |
| `next build` fails | Run `npm run build` locally and fix the reported errors |
| `npm ci` cannot find the lockfile | Run `npm install` once from `frontend` |
| Public page shows an administration link | That is a defect. The public layout must not link to `/staff` or Administration |

# ILMDAS local setup

This is the developer setup for a Windows machine. Bash users run the same tools; the only difference is how a virtual environment is activated (`source backend/.venv/bin/activate` instead of `backend\.venv\Scripts\Activate.ps1`).

The business baseline (BRS) and the SRS fix the stack: Next.js, Django, PostgreSQL, Elasticsearch, S3-compatible storage, and IIIF/Cantaloupe. Flutter is not part of this setup. Deployment to the OSTA data center is not part of this setup.

**Why Django runs on the host:** ILMDAS does not need GDAL/PostGIS system libraries, so the API uses a normal Python venv. Docker only runs PostgreSQL, Elasticsearch, and MinIO. The frontend also runs natively for fast hot reload.

Prove a fresh machine end-to-end with
[ILMDAS_Setup_Verification_Guide.md](ILMDAS_Setup_Verification_Guide.md).
Team CI workflow is in [ILMDAS_Team_CI-CD.md](ILMDAS_Team_CI-CD.md).

## Install the tools

1. Install Git and confirm `git --version`.
2. Install Python 3.12 or newer and confirm `python --version`.
3. Install Node.js 20 and confirm `node --version` and `npm --version`.
4. Install Docker Desktop, start it, and confirm `docker compose version`.

You do not need a local PostgreSQL, Elasticsearch, or MinIO install. Docker runs those three.

## Get the code

```powershell
git clone <repository-url> ilmdas
cd ilmdas
```

If you already have the folder, open a terminal in `ilmdas`.

## Start the local services

```powershell
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
```

Or: `make up` (Git Bash / WSL / macOS / Linux).

Wait until `postgres` and `elasticsearch` are running. Elasticsearch can take a minute the first time.

Confirm search:

```powershell
curl http://localhost:9200
```

You should see a JSON body with a cluster name. If the connection is refused, Docker is not running or port 9200 is already taken.

### Create the private bucket

1. Open http://localhost:9011
2. Sign in with user `ilmdas` and password `ilmdas-local-only`
3. Create a bucket named `ilmdas-digital-objects`
4. Do not turn on anonymous or public access

The API stores a checksum and an `s3://` reference. It does not store the file in PostgreSQL, and it does not return a public URL.

## Write the local environment file

```powershell
Copy-Item backend\.env.example backend\.env
```

`backend/.env.example` lists names and empty values. Fill `backend/.env` with the local values from the root README. That file is gitignored.

If `SECRET_KEY` or `DATABASE_URL` is empty, `manage.py` stops with `Missing required environment variables`. Put the values in `backend/.env`. Do not export a production secret into this file.

Leave `IIIF_ENDPOINT` empty unless you have a Cantaloupe base URL. An empty value is the correct local state. The staff status page then says the endpoint is not configured.

## Python environment

From the repository root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements\development.txt
python backend\manage.py migrate
python backend\manage.py runserver 127.0.0.1:8010
```

If PowerShell blocks the activate script, run the `python` and `pip` commands by path, as the README does, without activating.

`migrate` creates the object-reference table in PostgreSQL. After it succeeds, open http://localhost:8010/api/v1/health/.

- `"status": "ok"` means the database, Elasticsearch, and the bucket all answered.
- `"status": "failed"` with HTTP 503 means a check is `not configured` or `unreachable`. Start the matching container, create the bucket, or fix the URL in `.env`. The response does not include a stack trace.

Create a Django admin user only when you need the admin site:

```powershell
python backend\manage.py createsuperuser
```

The admin site is http://localhost:8010/admin/. It is not linked from the public website.

## Web application

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3010/ and http://localhost:3010/staff. Narrow the browser to 360px. The navigation wraps and the page stays inside the viewport. The public header does not contain Administration or a staff link.

The staff IIIF page is http://localhost:3010/staff/status. With an empty `IIIF_ENDPOINT` it must not claim that viewing succeeded.

`frontend/.env` is optional. Set `NEXT_PUBLIC_API_URL=http://localhost:8010` if the API is not on that address. The client sends `X-Correlation-ID` on every request.

## Daily routine

1. `docker compose -f docker-compose.dev.yml up -d` (or `make up`)
2. Activate the backend venv and run `python backend\manage.py runserver 127.0.0.1:8010`
3. In another terminal: `cd frontend` → `npm run dev`
4. Before a PR, run the quality commands below (or `make backend-lint`, `make backend-test`, `make frontend-lint`, `make frontend-test`, `make frontend-build`, `make frontend-e2e`)

## Checks before a change

From the repository root, after the virtual environment exists:

```powershell
backend\.venv\Scripts\pre-commit install
```

That installs the Ruff, ESLint, Prettier, secret-scan, and file-hygiene hooks. The frontend hooks call ESLint and Prettier through Python. Hooks do not run mypy, pytest, or `tsc`.

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

`npm run test:coverage` is Jest with coverage upload-ready output. `npm run build` is the production Next.js build CI also runs. `npm run test:e2e` opens Chromium on http://localhost:3010.

Pytest uses SQLite, so it does not need the Docker services. The health, index, storage, and IIIF tests use fakes for the failure and success paths. `migrate` against `DATABASE_URL` is the check that the same migrations apply to PostgreSQL.

CI also uploads coverage to Codecov (patch target 90%). Set `CODECOV_TOKEN` on the GitHub repository or the upload step fails.

## Stop

```powershell
docker compose -f docker-compose.dev.yml down
```

Or: `make down`. Add `-v` only when you intend to delete the local database, index, and bucket data.

## Troubleshooting

| What you see | What to do |
|---|---|
| `Missing required environment variables` | Fill `SECRET_KEY` and `DATABASE_URL` in `backend/.env` |
| Health says the database is unreachable | Confirm the postgres container is up and `DATABASE_URL` matches user `ilmdas`, password `ilmdas`, database `ilmdas` |
| Health says object storage is not configured | Set `S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, and the MinIO user and password |
| Health says object storage is unreachable | Create the private bucket, or confirm MinIO is on port 9010 |
| Port 5433, 8010, 9010, or 9200 is in use | Stop the other process or change the host port in `docker-compose.dev.yml` and the matching URL in `.env` |
| Coverage below 80% | Read the missing-lines report; add tests before changing omit rules |
| Codecov upload fails in CI | Add repository secret `CODECOV_TOKEN` |
| `next build` fails | Run `npm run build` locally and fix the reported errors |
| `npm ci` cannot find the lockfile | Run `npm install` once from `frontend` |
| Public page shows an administration link | That is a defect. The public layout must not link to `/staff` or Administration |

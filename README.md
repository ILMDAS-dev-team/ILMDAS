# ILMDAS — Integrated Library Management and Digital Archive System

ILMDAS is the IQQO system for the physical library and the digital archive: catalogue, circulation, membership, public discovery, preservation, payments, journal publishing, and the institutional website. The business baseline is the BRS. The system baseline is IQQO-ILMDAS-SRS-001 v1.0.

This repository is a monorepo. The web client and the API live together so one change can update both sides and so continuous integration runs both test suites.

The technology baseline from the BRS and the SRS is:

| Layer | Technology |
|---|---|
| Web | Next.js |
| API | Python, Django, Django REST Framework |
| Mobile | Flutter, added in the mobile sprint |
| Database | PostgreSQL. The database is the authority for transactions |
| Search | Elasticsearch. The catalogue index can be rebuilt |
| Files | S3-compatible object storage. Binaries are not stored in database columns |
| Images | IIIF / Cantaloupe, behind a client that stays not-configured until an endpoint is set |
| Deployment target | OSTA data center. This scaffold does not deploy there |

Loan periods, fine rates, membership fees, payment and notification providers, the AI use case, retention, and recovery targets stay unapproved. Do not invent those values in code.

## Repository layout

```
ilmdas/
├── backend/                  # Django project
│   ├── apps/                 # accounts, catalogue, circulation, archive,
│   │                         # publishing, payments, audit, and core
│   ├── config/settings/      # base, development, test, production
│   ├── requirements/         # base, development, production
│   ├── .env.example          # variable names only (optional host path)
│   └── manage.py
├── frontend/                 # Next.js app (public site and staff shell)
├── docker/
│   ├── backend/
│   │   ├── Dockerfile.dev    # local API image
│   │   └── Dockerfile        # production gunicorn image
│   ├── frontend/
│   │   └── Dockerfile        # production Next standalone image
│   └── docker-compose.prod.yml
├── docs/
│   ├── ILMDAS_Dev_Local_Setup.md
│   ├── ILMDAS_Team_CI-CD.md
│   ├── ILMDAS_Setup_Verification_Guide.md
│   └── ILMDAS_Tech_Lead_Env_Setup.md
├── .github/workflows/ci-cd.yml
├── codecov.yml
├── CONTRIBUTING.md
├── docker-compose.dev.yml    # local: backend in Docker, frontend native
├── Makefile
└── README.md
```

## What a developer sets up locally

Install these first:

- Git
- Node.js 20
- Docker Desktop, running

Local runtime matches OUPDMS’s split: **Django in Docker**, **Next.js native**.
Celery, Nginx, and PostGIS are not part of this local stack. More detail is in
[docs/ILMDAS_Dev_Local_Setup.md](docs/ILMDAS_Dev_Local_Setup.md).

### 1. Start the backend stack

```powershell
docker compose -f docker-compose.dev.yml up -d --build
```

| Service | URL | Local sign-in |
|---|---|---|
| Django API | http://localhost:8010 | — |
| PostgreSQL | `localhost:5433`, database `ilmdas` | user `ilmdas`, password `ilmdas` |
| Elasticsearch | http://localhost:9200 | security is off for this local node |
| MinIO API | http://localhost:9010 | user `ilmdas`, password `ilmdas-local-only` |
| MinIO console | http://localhost:9011 | same user and password |

These passwords exist only for the local Docker stack. They are not production secrets.

Compose starts `minio-init`, which creates the private bucket `ilmdas-files`. You do not need to create it in the console.

Compose injects backend environment with Docker service hostnames. You do not need `backend/.env` for this path.

### 2. Migrate and check health

```powershell
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
curl http://localhost:8010/api/v1/health/
```

A reachable database, search node, and bucket return `"status": "ok"`. A stopped service returns HTTP 503 and `"status": "failed"`.

### 3. Install and run the web app

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

- Public site: http://localhost:3010/
- Staff shell: http://localhost:3010/staff
- IIIF status, staff only: http://localhost:3010/staff/status

The public shell has no administration link and no link into `/staff`. The browser talks only to the Django API. It does not open PostgreSQL.

### 4. Run the checks

```powershell
docker compose -f docker-compose.dev.yml exec backend ruff check .
docker compose -f docker-compose.dev.yml exec backend ruff format --check .
docker compose -f docker-compose.dev.yml exec backend mypy apps config
docker compose -f docker-compose.dev.yml exec backend python -m pytest apps/ --cov=apps --cov-fail-under=80 -v
cd frontend
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
```

Local smoke: `make backend-smoke` and `make frontend-e2e`.

Continuous integration runs lint plus unit/coverage gates (backend coverage 80%, frontend coverage + `next build`). Backend and frontend smoke jobs stay in the workflow with `if: false` (Skipped); flip to `if: true` to enable them in CI. Codecov upload runs when `CODECOV_TOKEN` is set. A failing command fails the workflow. Deployment, Docker image publish, and PostGIS checks are not in CI. See [docs/ILMDAS_Team_CI-CD.md](docs/ILMDAS_Team_CI-CD.md).

## Further reading

| Doc | Purpose |
|---|---|
| [docs/ILMDAS_Dev_Local_Setup.md](docs/ILMDAS_Dev_Local_Setup.md) | Full local setup, daily routine, troubleshooting |
| [docs/ILMDAS_Setup_Verification_Guide.md](docs/ILMDAS_Setup_Verification_Guide.md) | Tech-lead checklist to prove stack + CI gates |
| [docs/ILMDAS_Team_CI-CD.md](docs/ILMDAS_Team_CI-CD.md) | Branches, CI jobs, pre-PR commands |
| [docs/ILMDAS_Tech_Lead_Env_Setup.md](docs/ILMDAS_Tech_Lead_Env_Setup.md) | Deploy stub (no servers/jobs yet) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | PR target, API error shape, checklist |

## Backend apps

| App | Responsibility in this scaffold |
|---|---|
| `core` | Health, shared API errors, object references, search index, IIIF client |
| `accounts` | Package reserved for accounts and roles |
| `catalogue` | Package reserved for bibliographic records |
| `circulation` | Package reserved for loans and returns |
| `archive` | Package reserved for digital objects |
| `publishing` | Package reserved for the journal |
| `payments` | Package reserved for the payment adapter |
| `audit` | Package reserved for the audit trail |

## API conventions

Errors use one body:

```json
{
  "code": "validation_error",
  "message": "The request is not valid.",
  "correlationId": "…"
}
```

Codes are `validation_error`, `authentication_error`, `authorization_error`, `not_found`, `conflict`, `rate_limit`, and `unavailable`. The message is safe to show. The body does not include a stack trace. Clients send `X-Correlation-ID`, and the API returns the same header.

Object storage references look like `s3://bucket/key`. They are not public URLs. Uploads are private.

The time zone is `Africa/Addis_Ababa`.

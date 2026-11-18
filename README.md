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
│   ├── .env.example          # variable names only
│   └── manage.py
├── frontend/                 # Next.js app (public site and staff shell)
├── docker/
│   └── docker-compose.prod.yml
├── docs/
│   ├── ILMDAS_Dev_Local_Setup.md
│   ├── ILMDAS_Team_CI-CD.md
│   ├── ILMDAS_Setup_Verification_Guide.md
│   └── ILMDAS_Tech_Lead_Env_Setup.md
├── .github/workflows/ci-cd.yml
├── codecov.yml
├── CONTRIBUTING.md
├── docker-compose.dev.yml
├── Makefile
└── README.md
```

## What a developer sets up locally

Install these first:

- Git
- Python 3.12 or newer
- Node.js 20
- Docker Desktop, running

The steps below are for Windows PowerShell from the repository root. The same commands work in bash if you use `python3` and `source backend/.venv/bin/activate`. More detail and the failure checks are in [docs/ILMDAS_Dev_Local_Setup.md](docs/ILMDAS_Dev_Local_Setup.md).

### 1. Start PostgreSQL, Elasticsearch, and MinIO

```powershell
docker compose -f docker-compose.dev.yml up -d
```

| Service | URL | Local sign-in |
|---|---|---|
| PostgreSQL | `localhost:5433`, database `ilmdas` | user `ilmdas`, password `ilmdas` |
| Elasticsearch | http://localhost:9200 | security is off for this local node |
| MinIO API | http://localhost:9010 | user `ilmdas`, password `ilmdas-local-only` |
| MinIO console | http://localhost:9011 | same user and password |

These passwords exist only for the local Docker stack. They are not production secrets and they are not in `backend/.env.example`.

In the MinIO console at http://localhost:9011, create a bucket named `ilmdas-digital-objects`. Leave it private. Do not add an anonymous read policy. These host ports stay clear of the other local project.

### 2. Configure the API

```powershell
Copy-Item backend\.env.example backend\.env
```

Open `backend/.env` and set:

```
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=local-development-only-change-me
DATABASE_URL=postgres://ilmdas:ilmdas@localhost:5433/ilmdas
ILMDAS_ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3010
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=ilmdas-catalogue
S3_ENDPOINT_URL=http://localhost:9010
S3_ACCESS_KEY_ID=ilmdas
S3_SECRET_ACCESS_KEY=ilmdas-local-only
S3_BUCKET_NAME=ilmdas-digital-objects
S3_REGION=us-east-1
IIIF_ENDPOINT=
IIIF_FIXTURE_IDENTIFIER=fixture-image
```

Leave `IIIF_ENDPOINT` empty until a Cantaloupe server exists. Staff then see “IIIF endpoint is not configured”. Filling it in must not be treated as a successful viewing session by itself.

Django refuses to start when `SECRET_KEY` or `DATABASE_URL` is missing.

### 3. Install the API and apply migrations

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\pip install -r backend\requirements\development.txt
backend\.venv\Scripts\python backend\manage.py migrate
backend\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8010
```

`runserver` uses development settings. The API is at http://localhost:8010/.

Check http://localhost:8010/api/v1/health/. A reachable database, search node, and bucket return `"status": "ok"`. A stopped service returns HTTP 503 and `"status": "failed"`.

### 4. Install and run the web app

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

`npm ci` needs `package-lock.json`. If you are on a fresh clone from before the lockfile was committed, run `npm install` once.

### 5. Run the checks

```powershell
backend\.venv\Scripts\pre-commit install
cd backend
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy apps config
.\.venv\Scripts\python -m pytest apps/ --cov=apps --cov-fail-under=80 -v
cd ..\frontend
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
npm run test:e2e
```

Continuous integration runs those checks (backend coverage gate 80%, frontend coverage + `next build`, Playwright smoke). Codecov upload runs when `CODECOV_TOKEN` is set. A failing command fails the workflow. Deployment, Docker image publish, and PostGIS checks are not in CI. See [docs/ILMDAS_Team_CI-CD.md](docs/ILMDAS_Team_CI-CD.md).

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

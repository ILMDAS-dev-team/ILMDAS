# ILMDAS tech lead environment (stub)

This document lists what the tech lead will need when ILMDAS deploys to the OSTA
data center. **GitHub Actions does not deploy yet.** There are no staging or
production hosts, SSH deploy secrets, or image-publish jobs in
[`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).

Companion docs: [ILMDAS_Team_CI-CD.md](ILMDAS_Team_CI-CD.md) ·
[ILMDAS_Setup_Verification_Guide.md](ILMDAS_Setup_Verification_Guide.md) ·
root [README](../README.md).

## What already exists in the repo

- Local stack: [`docker-compose.dev.yml`](../docker-compose.dev.yml) — Django
  backend image plus Postgres, Elasticsearch, and MinIO. Frontend stays native.
- Images:
  - [`docker/backend/Dockerfile.dev`](../docker/backend/Dockerfile.dev) (local)
  - [`docker/backend/Dockerfile`](../docker/backend/Dockerfile) (production gunicorn)
  - [`docker/frontend/Dockerfile`](../docker/frontend/Dockerfile) (production Next standalone)
- Production-shaped compose: [`docker/docker-compose.prod.yml`](../docker/docker-compose.prod.yml).
  Nginx is **not** wired yet. Celery is **not** part of ILMDAS.
- CI today: lint, pytest with 80% coverage, Jest coverage, `next build`, optional
  Codecov upload. Backend/frontend smoke jobs exist with `if: false` (Skipped).
  No GHCR push and no SSH deploy.

## Secret categories (when deploy is approved)

Do not invent hostnames or passwords in this repository. When OSTA DC wiring is
approved, expect secrets in these categories:

| Category | Examples |
|---|---|
| Django | `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `ILMDAS_ENVIRONMENT=production` |
| Database | PostgreSQL URL / credentials for the authority store |
| Search | Elasticsearch URL and index name |
| Object storage | S3 endpoint, access keys, private bucket name, region |
| IIIF | `IIIF_ENDPOINT` only when Cantaloupe (or equivalent) is available |
| CI | `CODECOV_TOKEN` (optional; enables Codecov uploads when set) |

## What to add later (not now)

1. Nginx (or equivalent) TLS termination and routing in front of backend/frontend.
2. GitHub Environments and deploy secrets (hosts, SSH keys) when servers exist.
3. Optional staging auto-deploy gated like OUPDMS (`DEPLOY_STAGING`) — only after
   those servers and images exist.
4. Fill [`.github/CODEOWNERS`](../.github/CODEOWNERS) with per-app GitHub logins
   when the team is ready to assign ownership (left unassigned for now).

Until then, every developer proves local + CI green with the
[Setup Verification Guide](ILMDAS_Setup_Verification_Guide.md).

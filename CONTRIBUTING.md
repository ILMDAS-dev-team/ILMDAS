# Contributing

All pull requests should target `develop` unless the work is a release PR from
`develop` into `main`.

Team workflow, CI jobs, and local reproduction commands are in
[docs/ILMDAS_Team_CI-CD.md](docs/ILMDAS_Team_CI-CD.md). Prove a fresh machine is
green with [docs/ILMDAS_Setup_Verification_Guide.md](docs/ILMDAS_Setup_Verification_Guide.md).

## API error shape

Validation and authentication failures use one JSON body. Do not return a stack
trace to the client.

```json
{
  "code": "validation_error",
  "message": "The request is not valid.",
  "correlationId": "…"
}
```

Allowed codes today: `validation_error`, `authentication_error`,
`authorization_error`, `not_found`, `conflict`, `rate_limit`, and `unavailable`.
Clients send `X-Correlation-ID`; the API returns the same header.

## Object storage

Digital objects are stored in S3-compatible storage. Persist a private
`s3://bucket/key` reference and a SHA-256 checksum. Do not store binaries in
PostgreSQL columns. Do not return a public URL for an object.

## Business constants

Loan periods, fine rates, membership fees, payment and notification providers,
AI use cases, retention, and recovery targets stay unapproved. Do not invent
those values in code or fixtures.

## Branch and commit habits

- Branch from an up-to-date `develop` as `feature/<short-description>`.
- Prefer conventional commit subjects (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`).
- Local default: Django in Docker, Next.js native (see
  `docs/ILMDAS_Dev_Local_Setup.md`).
- Install the git hooks once (see below). They catch CI failures locally, which
  saves our GitHub Actions minutes.

## Git hooks and local CI

`pre-commit` is a host tool, even though Django runs in Docker. Install it once in
a host virtualenv (or with `pipx install pre-commit`), then install both hooks from
the repo root (Git Bash on Windows). The push hook runs the backend checks in Docker
when Docker is running (see "Where the backend checks run" below):

```bash
cd backend
python -m venv .venv                 # skip if backend/.venv already exists
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements/development.txt   # provides pre-commit and the CI tools
cd ..
pre-commit install                        # quick checks on every commit
pre-commit install --hook-type pre-push   # full local CI on every push
```

`pre-commit install` alone sets up only the commit hook. The pre-push hook needs
`--hook-type pre-push`. Check both exist with `ls .git/hooks/pre-commit .git/hooks/pre-push`.

| When | What runs |
| --- | --- |
| `git commit` | Ruff, ESLint, Prettier, secret scan, whitespace and YAML/JSON checks |
| `git push` | `scripts/ci-local.sh`: the four CI jobs (backend lint, mypy, dependency audit, tests with 80% coverage; frontend lint, npm audit, Jest, production build). A failure cancels the push. |

Run the local CI by hand at any time: `scripts/ci-local.sh` (everything),
`scripts/ci-local.sh backend`, or `scripts/ci-local.sh frontend`. It shows
progress and names the step that failed. The frontend needs `npm ci` in
`frontend/` first. Skip the push hook once with `git push --no-verify`, for urgent
cases only, since GitHub CI still runs.

### Where the backend checks run

The backend checks (ruff, mypy, secret scan, pip-audit, pytest) run **in the dev
backend Docker image** whenever Docker is running. You don't need mypy or the other
tools on your machine. The script:

- builds the image from `docker-compose.dev.yml` first. This is quick when nothing
  has changed, and it picks up changes to `backend/requirements/`.
- uses `docker compose exec` if the backend container is running, or a one-off
  container (`docker compose run --rm --no-deps`) if it isn't. Postgres,
  Elasticsearch and MinIO don't need to be up, because the tests use SQLite.
- if the running container is older than the image and lacks a tool (for example,
  after `requirements/` changed), the script says so and uses one-off containers
  from the new image. To update the running container, run
  `docker compose -f docker-compose.dev.yml up -d --build`. `make up` does the same,
  but Git Bash on Windows doesn't include `make`.
- keeps the mypy, ruff, coverage and pip-audit caches in the Docker volume
  `ilmdas_ci_home`, not in `backend/`. Clear them with `docker volume rm ilmdas_ci_home`.

If Docker isn't running, the script falls back to a host virtualenv. It uses the
active `$VIRTUAL_ENV`, then `backend/.venv`, then `.venv` or `venv` at the repo root.
Choose the runner yourself with `CI_LOCAL_BACKEND`:

```bash
CI_LOCAL_BACKEND=docker scripts/ci-local.sh backend
CI_LOCAL_BACKEND=venv scripts/ci-local.sh backend
```

A host Python is still needed for `pre-commit` itself: the venv above, or
`pipx install pre-commit`. The frontend checks always run natively with npm.

### When a hook fails

- **Commit stopped after "ruff" or "ruff-format" says "Failed" / "files were
  modified":** the hook fixed or reformatted your files and stopped the commit, on
  purpose, so you can see the change. Run `git add` on those files and commit again.
- **Push stopped with "These backend tools are not installed in that Python":**
  the venv runner was used, and the Python it names doesn't have the tools. This
  happens, for example, when you installed mypy into a different venv. Either start
  Docker and push again, or install the tools into the Python the message names:
  `<that python> -m pip install -r backend/requirements/development.txt`.

## PR checklist

- Target branch is `develop` (or `main` only for a release PR).
- API errors keep the shape above; correlation IDs are preserved.
- Object references stay private `s3://` values with checksums when storage is involved.
- No invented loan, fine, membership, or retention constants.
- Backend: `ruff check .`, `ruff format --check .`, `mypy apps config`, and
  `pytest apps/ --cov=apps --cov-fail-under=80`.
- Frontend: `npm run lint`, `npm run type-check`, `npm run format:check`,
  `npm run test:coverage`, and `npm run build`.
- Optional local smoke (not CI): `make backend-smoke`, `make frontend-e2e`.
- OpenAPI annotations and RBAC/scope rules are added when those features land.

`.github/CODEOWNERS` is a scaffold placeholder. Per-app GitHub owners are not
assigned yet; reviewers are requested manually until that file is filled.

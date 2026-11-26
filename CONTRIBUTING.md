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
a host virtualenv, then install both hooks from the repo root (Git Bash on Windows):

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

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
- Install hooks once: `backend\.venv\Scripts\pre-commit install` (or the Unix
  equivalent after the venv exists). Hooks run Ruff, ESLint, Prettier, and
  secret scanning. They do not run mypy, pytest, or `tsc`.

## PR checklist

- Target branch is `develop` (or `main` only for a release PR).
- API errors keep the shape above; correlation IDs are preserved.
- Object references stay private `s3://` values with checksums when storage is involved.
- No invented loan, fine, membership, or retention constants.
- Backend: `ruff check .`, `ruff format --check .`, `mypy apps config`, and
  `pytest apps/ --cov=apps --cov-fail-under=80`.
- Frontend: `npm run lint`, `npm run type-check`, `npm run format:check`,
  `npm run test:coverage`, `npm run build`, and `npm run test:e2e`.
- OpenAPI annotations and RBAC/scope rules are added when those features land.

`.github/CODEOWNERS` is a scaffold placeholder. Per-app GitHub owners are not
assigned yet; reviewers are requested manually until that file is filled.

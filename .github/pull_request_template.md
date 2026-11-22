Summary
This PR implements the Phase 1 security controls identified in the ILMDAS repository security review report. It establishes the custom `accounts.User` model and `audit.AuditRecord` prior to other domain tables, enforces named role-based access permissions (`CanUploadArchiveObject`, `CanViewObjectDetail`, `CanManageSearchIndex`), and configures password validators while removing `BasicAuthentication` and applying endpoint rate throttling. In addition, it secures staff routes via server-side session checks and edge middleware, enforces 10MB upload limits with magic byte content validation and an antivirus hook, hardens Elasticsearch TLS/cert checks, and adds automated security scanning gates (pip-audit, npm audit, detect-secrets, Ruff Bandit rules) with commit SHA pinned actions to CI.

Work Item
Phase 1 Security Controls: SEC-17, SEC-02, SEC-07, SEC-04, SEC-09, SEC-15, SEC-16

Bounded Context
Backend (Django)

[x] core: API platform, middleware, error format, storage, search, IIIF
[x] accounts: users, roles, sign-in
[ ] catalogue: bibliographic records, search
[ ] circulation: loans, renewals, reservations, fines
[ ] archive: digitised objects, OCR, fixity
[ ] publishing: journals and open access
[ ] payments: payment providers, callbacks, reconciliation
[x] audit: audit trail

Frontend (Next.js)

[x] (public): home, OPAC, about (added /sign-in)
[x] (staff): staff workspaces

Platform

[ ] Docker, Compose or infrastructure
[x] CI workflow or developer tooling

Type of Change
[x] feat: New functionality
[ ] fix: Bug fix
[ ] docs: Documentation only
[ ] refactor: Internal code improvement, no behaviour change
[ ] test: Tests only
[ ] chore: Tooling or dependency change
[ ] build: Build system or packaging change
[ ] ci: Pipeline change

Backend Checklist
[x] Models changed: migration created with makemigrations, and reviewed
[x] Migration is reversible, or the reason it is not is written in Deployment Notes
[x] Serializers validate input and return only the fields the API documents
[x] Views and services keep business logic out of request handling
[x] New or changed endpoints are reflected in docs/ or the API reference
[x] Settings changes are in the correct file (base, development, test, or production)
[x] Management commands are idempotent and log what they change
[x] Type hints added, and mypy apps config passes
[x] Ruff lint and format pass locally
[ ] Not applicable to this PR

Frontend Checklist
[x] Components are typed, and npm run type-check passes
[x] New strings are in all three language catalogues (Afaan Oromoo, English, Amharic)
[x] Layout checked at mobile and desktop widths
[ ] Not applicable to this PR

Security
[x] No secrets, tokens or credentials in code, tests, fixtures or Docker files
[x] New environment variables are listed in backend/.env.example (names only)
[x] New dependencies are pinned and have been checked for known vulnerabilities
[ ] Not applicable to this PR

Documentation & CI
[x] Documentation updated where behaviour, setup or configuration changed
[x] README.md or a file in docs/ reflects new commands or steps
[x] CI workflow still passes on this branch: backend-lint, backend-tests, frontend-lint, frontend-tests, frontend-e2e
[x] New CI steps or tools documented in docs/ILMDAS_Team_CI-CD.md
[ ] Not applicable to this PR

Testing Notes
[x] make backend-test passes, with coverage at or above 80% (Achieved 90.48%)
[x] make frontend-test passes
[x] make migrate succeeds on a clean database
[x] New tests cover the main path and at least one failure path
[x] Manual check done locally (describe the steps below)

How I tested:
- Backend Test Suite: Executed `pytest apps/ --cov=apps --cov-report=term-missing --cov-fail-under=80 -v` inside the backend container. 68 tests passed, 0 failures, achieving 90.48% coverage.
- Backend Lint & Static Security: Executed `ruff check .`, `ruff format --check .`, and `mypy apps config`. 0 linting errors, 0 format issues, 0 mypy issues across 77 source files.
- Frontend Verification: Executed `npm run check` in the frontend directory (ESLint, TypeScript `tsc --noEmit`, Prettier format check, Jest unit tests with coverage, Next.js production build, and Playwright E2E smoke tests). All passed.
- Role-Based Permissions (SEC-02): Verified members receive 403 on `/api/v1/storage/objects/`, `/api/v1/storage/objects/<id>/`, `/api/v1/search/catalogue-index/`, and `/api/v1/storage/presign/`.
- Upload Integrity & Malware (SEC-09): Tested magic byte MIME detection across permitted formats, rejection of forbidden binaries (ELF), enforcement of 10MB limit, and detection of EICAR test signatures.
- Staff Guard (SEC-04): Tested that anonymous visitors to `/staff`, `/staff/status`, and `/staff/[section]` are redirected to `/sign-in`.
- Elasticsearch & TLS (SEC-15): Tested HTTPS URL enforcement and certificate verification rejection when `ELASTICSEARCH_VERIFY_CERTS=False` in production.
- CI Workflow Gates (SEC-16): Tested presence of `pip-audit`, `npm audit`, `detect-secrets`, Ruff Bandit `S` rules, and verified all GitHub actions are pinned to 40-character commit SHAs.

Screenshots
<!-- Only for visible UI changes. Delete this section otherwise. -->

Deployment Notes
[ ] No deployment step needed
[x] Steps needed after merge (migrations, configuration, index rebuild):
- Run `python manage.py migrate` in the backend container:
  1. `accounts.0001_initial` (creates custom `accounts_user` table)
  2. `audit.0001_initial` (creates `audit_auditrecord` table)
  3. `core.0001_initial` (adds `scan_status` column to `core_objectreference`)
- Populate optional Elasticsearch secrets (`ELASTICSEARCH_API_KEY`, `ELASTICSEARCH_CA_CERTS`) in production environment if authentication is enabled on the cluster.

Reviewer Notes
- Migration Sequencing: Note that `backend/apps/core/migrations/0001_initial.py` and `backend/apps/audit/migrations/0001_initial.py` declare an explicit dependency on `("accounts", "0001_initial")` to ensure the custom user model is created before any referencing tables (SEC-17).
- Authentication Defaults: `BasicAuthentication` has been removed from `DEFAULT_AUTHENTICATION_CLASSES` in `settings/base.py`. Authentication relies on `SessionAuthentication` with CSRF protection, and sensitive actions (`storage.upload`, `search.index.*`, login/logout) log immutable records to `AuditRecord` (SEC-07, SEC-17).
- Defense in Depth: Staff routes are protected at two layers: Next.js edge middleware (`src/middleware.ts`) and server component session checks (`verifyStaffSession()` in `src/lib/auth.ts`) (SEC-04).

Pre-merge Checklist
[x] Title follows type(scope): summary, for example feat(catalogue): add language filter to OPAC search
[x] Scope is one of the bounded contexts above, or web, infra, ci
[x] Self-review done, with no debug output, commented-out code or unexplained TODOs
[x] Branch is up to date with the target branch
[x] All CI checks are green

## Summary

<!-- What does this PR change, and why? Two or three sentences. -->

## Work Item

<!-- Issue or task this PR delivers, for example #123 or ILMDAS-45. -->

## Bounded Context

<!-- Tick every context this PR touches. -->

**Backend (Django)**
- [ ] `core`: API platform, middleware, error format, storage, search, IIIF
- [ ] `accounts`: users, roles, sign-in
- [ ] `catalogue`: bibliographic records, search
- [ ] `circulation`: loans, renewals, reservations, fines
- [ ] `archive`: digitised objects, OCR, fixity
- [ ] `publishing`: journals and open access
- [ ] `payments`: payment providers, callbacks, reconciliation
- [ ] `audit`: audit trail

**Frontend (Next.js)**
- [ ] `(public)`: home, OPAC, about
- [ ] `(staff)`: staff workspaces

**Platform**
- [ ] Docker, Compose or infrastructure
- [ ] CI workflow or developer tooling

## Type of Change

<!-- Select one. The type sets the commit prefix in the title. -->

- [ ] `feat`: New functionality
- [ ] `fix`: Bug fix
- [ ] `docs`: Documentation only
- [ ] `refactor`: Internal code improvement, no behaviour change
- [ ] `test`: Tests only
- [ ] `chore`: Tooling or dependency change
- [ ] `build`: Build system or packaging change
- [ ] `ci`: Pipeline change

## Backend Checklist

- [ ] Models changed: migration created with `makemigrations`, and reviewed
- [ ] Migration is reversible, or the reason it is not is written in Deployment Notes
- [ ] Serializers validate input and return only the fields the API documents
- [ ] Views and services keep business logic out of request handling
- [ ] New or changed endpoints are reflected in `docs/` or the API reference
- [ ] Settings changes are in the correct file (`base`, `development`, `test`, or `production`)
- [ ] Management commands are idempotent and log what they change
- [ ] Type hints added, and `mypy apps config` passes
- [ ] Ruff lint and format pass locally
- [ ] Not applicable to this PR

## Frontend Checklist

- [ ] Components are typed, and `npm run type-check` passes
- [ ] New strings are in all three language catalogues (Afaan Oromoo, English, Amharic)
- [ ] Layout checked at mobile and desktop widths
- [ ] Not applicable to this PR

## Security

- [ ] No secrets, tokens or credentials in code, tests, fixtures or Docker files
- [ ] New environment variables are listed in `backend/.env.example` (names only)
- [ ] New dependencies are pinned and have been checked for known vulnerabilities
- [ ] Not applicable to this PR

## Documentation & CI

- [ ] Documentation updated where behaviour, setup or configuration changed
- [ ] `README.md` or a file in `docs/` reflects new commands or steps
- [ ] CI workflow still passes on this branch: `backend-lint`, `backend-tests`, `frontend-lint`, `frontend-tests`, `frontend-e2e`
- [ ] New CI steps or tools documented in `docs/ILMDAS_Team_CI-CD.md`
- [ ] Not applicable to this PR

## Testing Notes

<!-- Describe how you tested. Paste the command you ran and its result. -->

- [ ] `make backend-test` passes, with coverage at or above 80%
- [ ] `make frontend-test` passes
- [ ] `make migrate` succeeds on a clean database
- [ ] New tests cover the main path and at least one failure path
- [ ] Manual check done locally (describe the steps below)

**How I tested:**

<!-- Steps, data used, and anything not covered. -->

## Screenshots

<!-- Only for visible UI changes. Delete this section otherwise. -->

## Deployment Notes

- [ ] No deployment step needed
- [ ] Steps needed after merge (migrations, configuration, index rebuild):

<!-- For example: run migrate, rebuild the catalogue index, set a new variable. -->

## Reviewer Notes

<!-- Where should the reviewer focus first? What are you unsure about? Any decision that needs a second opinion? -->

## Pre-merge Checklist

- [ ] Title follows `type(scope): summary`, for example `feat(catalogue): add language filter to OPAC search`
- [ ] Scope is one of the bounded contexts above, or `web`, `infra`, `ci`
- [ ] Self-review done, with no debug output, commented-out code or unexplained TODOs
- [ ] Branch is up to date with the target branch
- [ ] All CI checks are green

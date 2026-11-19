# ILMDAS — End-to-end setup verification

This is the tech lead checklist to prove the local stack and quality gates work
before the team starts. Work the phases in order. Each step lists the command,
the expected result, and a pass / fail signal.

Conventions: run commands from the `ilmdas/` repository root unless noted.
`DC` below means `docker compose -f docker-compose.dev.yml`.

Deployment to the OSTA data center, PostGIS, Celery, and Nginx are **not** part
of this guide. See [ILMDAS_Tech_Lead_Env_Setup.md](ILMDAS_Tech_Lead_Env_Setup.md)
for what will be needed later.

---

## Phase 0 — Prerequisites and branches

**0.1 Tools present**

```powershell
git --version
node --version
npm --version
docker compose version
```

Pass: Git, Node 20+, and Compose v2 all print versions.
Fail: install the missing tool. Host Python is optional for the Docker path.

**0.2 Branches and remote**

```powershell
git branch -a
git remote -v
```

Pass: `main` and `develop` exist (locally or on origin). Fail: create/push the
missing branch before inviting the team.

---

## Phase A — Local development stack

Django runs in Docker. Next.js runs natively. Ports stay clear of other local projects.

**A.1 Build and start the stack**

```powershell
DC up -d --build
DC ps
```

Pass: `backend`, `postgres`, `elasticsearch`, and `minio` are Up. Fail:
`DC logs <service>`.

**A.2 Elasticsearch**

```powershell
curl http://localhost:9200
```

Pass: JSON body with a cluster name. Fail: Docker not running or port 9200 taken.

**A.3 Private MinIO bucket**

1. Open http://localhost:9011
2. Sign in with user `ilmdas` and password `ilmdas-local-only`
3. Create bucket `ilmdas-digital-objects`
4. Leave anonymous/public access off

Pass: bucket exists and is private. Fail: create the bucket before health will pass.

**A.4 Migrate and health**

```powershell
DC exec backend python manage.py migrate
curl http://localhost:8010/api/v1/health/
```

Pass: HTTP 200 and `"status": "ok"`. Fail: HTTP 503 / `"status": "failed"` —
fix the matching container or create the bucket.

**A.5 Frontend**

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3010/ and http://localhost:3010/staff.
Open http://localhost:3010/staff/status — with empty `IIIF_ENDPOINT` it must say
the endpoint is not configured, not that viewing succeeded.

Pass: public and staff shells render; public header has no Administration or
`/staff` link. Fail: see [ILMDAS_Dev_Local_Setup.md](ILMDAS_Dev_Local_Setup.md).

> Phase A passes when the stack is up, health is `ok`, and both web shells render.

---

## Phase B — Quality gates (CI parity)

These match [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).

**B.1 Pre-commit**

Install hooks once (host or documented Docker path), then:

```powershell
pre-commit run --all-files
```

Pass: Ruff, ESLint, Prettier, detect-secrets, and hygiene hooks pass.
Fail: fix the reported file; hooks do not run mypy, pytest, or `tsc`.

**B.2 Backend lint + coverage gate**

```powershell
DC exec backend ruff check .
DC exec backend ruff format --check .
DC exec backend mypy apps config
DC exec backend python -m pytest apps/ --cov=apps --cov-report=term-missing --cov-fail-under=80 -v
```

Pass: lint clean; coverage ≥ 80%. Fail: add tests or fix coverage omit only for
empty stub modules, never by lowering the gate.

**B.3 Frontend lint, coverage, production build**

```powershell
cd frontend
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
```

Pass: all five succeed. Fail: fix lint/format or failing tests before merging.

**B.4 Playwright smoke**

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

Pass: Chromium smoke opens public and staff pages. Fail: install Chromium or fix
the failing spec.

> Phase B passes when every command above is green — that is a green CI run, locally.

---

## Phase D — GitHub CI

There is no deploy job and no Docker image publish in this workflow.

**D.1 Codecov token**

Optional until Codecov is wired: without `CODECOV_TOKEN`, coverage upload steps
are skipped. Add the secret when you want uploads; then upload failures fail CI
(`fail_ci_if_error: true`).

**D.2 Open a trivial pull request into `develop`**

Expect these jobs green:

1. Backend lint
2. Backend tests (pytest + `--cov-fail-under=80` + optional Codecov)
3. Frontend lint
4. Frontend tests (`test:coverage`, `next build`, optional Codecov)
5. Frontend smoke (Playwright Chromium)

Pass: all five green. Fail: reproduce with the matching local command from Phase B
or [ILMDAS_Team_CI-CD.md](ILMDAS_Team_CI-CD.md).

> Phase D passes when a PR shows the five jobs green. Image build and staging /
> production deploy phases are deferred until those land in CI.

---

## Troubleshooting

| What you see | What to do |
|---|---|
| Backend container restarting | `DC logs backend` |
| Coverage below 80% | Read the missing lines report; add tests for `apps.core` before omitting stubs |
| Codecov upload skipped | Expected until `CODECOV_TOKEN` is set |
| Codecov upload fails with token set | Check token and `codecov.yml` |
| `next build` fails | Run `npm run build` locally; fix type or import errors |
| Health failed / 503 | Confirm Postgres, ES, MinIO, and private bucket |
| Port clash | Adjust host ports in `docker-compose.dev.yml` |

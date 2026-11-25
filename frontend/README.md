# ILMDAS web app

Next.js application for the public site and the staff shell.

Setup, environment variables, and the local Docker stack are in the repository root [README](../README.md) and in [docs/ILMDAS_Dev_Local_Setup.md](../docs/ILMDAS_Dev_Local_Setup.md).

The API runs in Docker on http://localhost:8010. This app runs natively:

```powershell
npm ci
npm run dev
npm run lint
npm run type-check
npm run format:check
npm run test:coverage
npm run build
npm run test:e2e
```

`npm run test:coverage` runs Jest with coverage. `npm run build` is the production build CI also runs (`output: "standalone"` for `docker/frontend/Dockerfile`). `npm run test:e2e` is local Playwright smoke (not run in CI); use `make frontend-e2e` from the repo root.

The dev server listens on http://localhost:3010. It calls the Django API at `NEXT_PUBLIC_API_URL`, which defaults to http://localhost:8010.

Server-rendered staff pages that forward the session cookie use `ILMDAS_API_URL` first, then `NEXT_PUBLIC_API_URL`, then the same local default. `ILMDAS_API_URL` is server-only: set it to the trusted internal API URL in deployed environments. Pointing it at an untrusted host would expose staff session cookies.

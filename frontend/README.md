# ILMDAS web app

Next.js application for the public site and the staff shell.

Setup, environment variables, and the local Docker stack are in the repository root [README](../README.md) and in [docs/ILMDAS_Dev_Local_Setup.md](../docs/ILMDAS_Dev_Local_Setup.md).

```powershell
npm ci
npm run dev
npm run lint
npm run type-check
npm test
npm run test:e2e
```

`npm test` runs Jest. `npm run test:e2e` opens Chromium on port 3010.

The dev server listens on http://localhost:3010. It calls the Django API at `NEXT_PUBLIC_API_URL`, which defaults to http://localhost:8010.

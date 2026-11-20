# Fridgely

A responsive kitchen application with a React client, a FastAPI host and durable
PostgreSQL/SQLite storage. Accounts, saved preferences, fridge entries, recipe
generation, shopping, favorites and viewed history share the same verified JWT
identity and owner-qualified database.

## Run the integrated application

Use Python 3.12, Node 24 and pnpm 11.25.0. In a virtual environment:

```bash
python -m pip install -r backend/requirements-app.lock
python -m pip install --no-deps -e backend
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
```

Set `DATABASE_URL` and a random `JWT_SECRET` of at least 32 bytes in the process
environment, using [.env.example](.env.example) as the variable reference. For
local development `DATABASE_URL=sqlite:///./fridgely.db` is supported. The app does
not automatically load `.env`. Then migrate and start the host:

```bash
python -m fridgely_app migrate
python -m uvicorn fridgely_app.host:create_app --factory --port 8000
```

Open `http://127.0.0.1:8000`. Provide `OPENAI_API_KEY` for live recipe generation;
without it the app returns an explicit retryable provider error. Personal lists
continue to work. Do not copy the old ZIP database or execute its reset schema.

## Verify

```bash
python -m pytest backend/tests
FRIDGELY_PYTHON=python node --test tests/functional/requirements.test.mjs
```

See [backend setup](backend/README-host.md), [database/account design](backend/README-accounts.md)
and [web/browser tests](frontend/README.md). Tests use the real application and
SQL persistence with a controlled external recipe provider. The production host
contains no demo-account or mock-provider mode.

The integrated CI workflow exercises real PostgreSQL persistence, all acceptance
cases, HTTP security, browser/accessibility checks, measured coverage, the
five-minute load scenario, dependency audits and an ephemeral SonarQube server.
Workflow completion and artifact contents are the evidence, not the mere presence
of a workflow file.

## Review structure

Work is proposed through separate dependent branches: accounts/database, feature
composition, web integration, CI verification and the test report. Existing
backend module history is preserved. No automatic main-branch merge or production
deployment is configured by these changes.


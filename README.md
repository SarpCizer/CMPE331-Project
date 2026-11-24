# Fridgely

A responsive kitchen application with a React client, a FastAPI host and durable
PostgreSQL/SQLite storage. Accounts, saved preferences, fridge entries, recipe
generation, shopping, favorites and viewed history share the same verified JWT
identity and owner-qualified database.

The initial release uses manually entered ingredient names and addition dates.
Receipt OCR, expiry alerts, quantity arithmetic, automatic inventory deduction and
native mobile applications are outside this reviewed scope.

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

Open `http://127.0.0.1:8000`. Configure a server-side recipe provider for live
generation. The setup supports [Cloudflare Workers AI Free or OpenAI](docs/cloud-deployment.md#recipe-provider-settings).
Personal lists continue to work when recipe generation is unavailable.

## Verify

```bash
python -m pytest backend/tests
FRIDGELY_PYTHON=python node --test tests/functional/requirements.test.mjs
API_BASE_URL=http://127.0.0.1:8000 node --test tests/fullstack/accounts-isolation.http.test.mjs
pnpm --dir frontend test:e2e
node tests/security/penetration.mjs
```

See the [interactive API contract](docs/api.md), [cloud deployment](docs/cloud-deployment.md),
[backend setup](backend/README-host.md), [database/account design](backend/README-accounts.md)
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
deployment from main is configured. The separate cloud feature branch configures
the Render teaching deployment; see its reviewable Blueprint and deployment record.

The team's Render deployment status and source revision are tracked in
[#40](https://github.com/SarpCizer/CMPE331-Project/issues/40). Live recipe generation
requires the selected provider's server-side credentials.

## Documentation and team

- [Branching, independent review and Semantic Versioning](docs/CONTRIBUTING.md)
- [Approved stories, API contract and quality requirements](docs/requirements/README.md)
- [Implemented database and transaction boundaries](docs/database.md)
- [Recorded implementation decisions for team review](docs/requirements/decisions.md)
- [Milestone status and final-delivery checklist](docs/milestone-handoff.md)
- [Existing requirements report and WBS/PERT/Gantt plans](docs/requirements-specification.md)
- [Analysis review PR #5](https://github.com/SarpCizer/CMPE331-Project/pull/5)
  and [design review PR #6](https://github.com/SarpCizer/CMPE331-Project/pull/6)
- [Instructor review and current issues](https://github.com/SarpCizer/CMPE331-Project/issues/16)
- [AI tooling and runtime recipe pipeline](docs/ai-pipeline.md),
  [contribution log](docs/ai-usage-log.md), [observed incidents](docs/ai-mistakes.md)
  and [demo/presentation runbook](docs/demo-runbook.md)
- [Source-only ZIP and final account/owner actions](docs/submission.md)
- [Executed test report, PDF and evidence index](docs/tests/README.md)

Charter roles: Berfin Gökgöz (full-stack/database), İrem Demircan (product owner and
fridge backend), Sarp Çizer (shopping/favorites/history), Ayşe Döne (recipe AI),
Mustafa Safa Bayrak (frontend), Kerem Sönmez (DevOps/QA). Current integration retains
Sarp's and Ayşe's module histories; Berfin's PRs also supply the connected React UI
and integrated checks. The team must confirm its contact, obtain independent reviews
and ensure each member makes their own real contribution. No contribution or
approval is fabricated for another member.


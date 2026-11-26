# Fridgely

A responsive kitchen application with a React client, a FastAPI host and durable
PostgreSQL/SQLite storage. Accounts, saved preferences, fridge entries, recipe
generation, shopping, favorites, weekly plans and viewed history share the same verified JWT
identity and owner-qualified database.

The fridge supports manually entered ingredient names, quantities, units and addition dates.
Confirmed cooking deducts reviewed quantities; confirmed shopping purchases refill the fridge.
Receipt OCR, expiry alerts and native mobile applications are outside this reviewed scope.

## Weekly meal planner

Open **Weekly meal planner** in the kitchen menu. Each day starts with one optional
field. Choose a saved recipe or type a dish (for example, tomato sauce pasta), set
its portions, then select **Create recipe & plan**. Use **+ Add dish** to add another
dish such as brownie to the same day. There are no fixed breakfast/lunch/dinner
categories. Each dish independently supports 1–20 portions, with up to 20 dishes
per day. Expand **Ingredients & preparation** for scaled amounts and ordered steps.
A saved dish can be reused and rescaled without another provider request.

**Generate weekly shopping list** scales and totals every planned dish, subtracts
current fridge quantities once, and adds the missing amounts to the existing list.
For example, two required bananas minus one in the fridge adds one banana. It
preserves larger quantities already on the shopping list and does not reserve or
deduct stock. Whole items are rounded up only after aggregation; unknown or
incompatible measurements are explicitly flagged for review. Planning does not
automatically remove prior shopping entries when a meal is changed or removed.
New dish creation uses the existing configured server-side AI provider; provider
outages or quota exhaustion preserve the saved plan and allow saved-recipe reuse.

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
```

For HTTP and browser verification, build the frontend and run the disposable
test host in a separate terminal:

```bash
FRIDGELY_TEST_PORT=8091 PYTHONPATH=backend/src python backend/tests/serve_web_test.py
```

With that host running:

```bash
API_BASE_URL=http://127.0.0.1:8091 node --test tests/fullstack/accounts-isolation.http.test.mjs
pnpm --dir frontend exec playwright install chromium
WEB_BASE_URL=http://127.0.0.1:8091 pnpm --dir frontend test:e2e
```

See the [interactive API contract](docs/api.md), [cloud deployment](docs/cloud-deployment.md),
[backend setup](backend/README-host.md), [database/account design](backend/README-accounts.md)
and [web/browser tests](frontend/README.md#browser-tests). Start the disposable
test host described there before running the HTTP or browser suites. Tests use
the real application and SQL persistence with a controlled external recipe
provider. The production host contains no demo-account or mock-provider mode.

The integrated CI workflow exercises real PostgreSQL persistence, all acceptance
cases, HTTP security, browser/accessibility checks, measured coverage, the
five-minute load scenario, dependency audits and an ephemeral SonarQube server.
Workflow completion and artifact contents are the evidence, not the mere presence
of a workflow file.

## Review structure

The integrated application and Cloudflare provider have been merged into `main`.
Follow-up work uses focused branches and independent PR review. Existing backend
module history and the approved submission source/report pair remain traceable.

The existing [Render application](https://fridgely-web.onrender.com) is configured
to follow `main` after successful CI checks, as recorded in
[#40](https://github.com/SarpCizer/CMPE331-Project/issues/40). Check that issue and
the Render deploy record for the actual deployed commit. The original service,
committed YAML and existing Blueprint all select `main`. The
[Blueprint verification](https://github.com/SarpCizer/CMPE331-Project/issues/40#issuecomment-7152962475)
recorded auto-sync paused and a plan with no changes.

Cloudflare Workers Free recipe generation was verified on deployed `ec9142e`
on 25 November 2026: 25 live HTTP/behavior checks passed, missing ingredients
reached shopping without duplicates, and the fridge remained unchanged. See the
[source-pinned live result and sanitized evidence](docs/cloud-deployment.md#verified-live-result-25-november-2026).
Provider setup and future changes follow the [activation checks](docs/cloud-deployment.md#activate-and-verify-cloudflare).

## Documentation and team

- [Branching, independent review and Semantic Versioning](docs/CONTRIBUTING.md)
- [Approved stories, API contract and quality requirements](docs/requirements/README.md)
- [Implemented database and transaction boundaries](docs/database.md)
- [Design package and source-pinned implementation alignment](docs/design/README.md)
- [Recorded implementation decisions for team review](docs/requirements/decisions.md)
- [Milestone status and final-delivery checklist](docs/milestone-handoff.md)
- [Existing requirements report and WBS/PERT/Gantt plans](docs/requirements-specification.md)
- [Analysis review PR #5](https://github.com/SarpCizer/CMPE331-Project/pull/5)
  and [design review PR #6](https://github.com/SarpCizer/CMPE331-Project/pull/6)
- [Instructor review and current issues](https://github.com/SarpCizer/CMPE331-Project/issues/16)
- [AI tooling and runtime recipe pipeline](docs/ai-pipeline.md),
  [contribution log](docs/ai-usage-log.md), [observed incidents](docs/ai-mistakes.md)
  and [demo/presentation runbook](docs/demo-runbook.md)
- [Approved course ZIP, matching report and live demo source](docs/submission.md)
- [Executed test report, PDF and evidence index](docs/tests/README.md)

Charter roles: Berfin Gökgöz (full-stack/database), İrem Demircan (product owner and
fridge backend), Sarp Çizer (shopping/favorites/history), Ayşe Döne (recipe AI),
Mustafa Safa Bayrak (frontend), Kerem Sönmez (DevOps/QA). Current integration retains
Sarp's and Ayşe's module histories; Berfin's PRs also supply the connected React UI
and integrated checks. The six members' authored commits and independent reviews
are linked from the [instructor checklist](https://github.com/SarpCizer/CMPE331-Project/issues/16).

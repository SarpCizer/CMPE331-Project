# Integrated FastAPI application - Berfin

`fridgely_app.host:create_app` composes Berfin's real accounts/preferences/inventory,
Sarp's `fridgely_collections` and Ayse's `fridgely_recipes`. All feature routers use
the same verified JWT principal, SQLAlchemy session factory and durable database.
Recipes read the authenticated account's latest committed inventory/preferences;
collections read the persisted owned recipe aggregate. No test account, local
owner header, ZIP model, model pickle or browser-local inventory is used.

The recipe files are preserved from PR #7 at
`e5391fee8f7f3e4ba3dff28709bcdeebae55758f`; collections are preserved from
`backend_work` at `862005feb03906f1d4f7b19c84b8a339b74dc52c`.

## Start locally

```bash
python -m pip install -r backend/requirements-app.lock
python -m pip install --no-deps -e backend
# Set DATABASE_URL and a random JWT_SECRET in your process environment.
python -m fridgely_app migrate
python -m uvicorn fridgely_app.host:create_app --factory --port 8000
```

`.env.example` documents names; the application reads process environment and does
not automatically load `.env`. Keep real values outside source control. SQLite
is supported for local development; PostgreSQL is the shared deployment target.
Migration is an explicit prior step, so startup cannot reset an existing database.

Set the [recipe provider and its server-side credentials](../docs/cloud-deployment.md#recipe-provider-settings)
to enable live generation. Missing provider credentials produce a sanitized,
retryable 503 for recipe generation. Account, inventory and collections remain
available. The test suites use controlled providers.

Both root-contract paths and `/api` paths reach the same application. The React
client uses `/api` on the same origin. When `frontend/dist/index.html` exists (or
`FRONTEND_DIST` is set), the host serves the build, its assets and supported SPA
routes. Personal responses are not cached; nosniff, CSP and referrer headers are
set by the outer host. No cross-origin credential policy is required.

## Tests

```bash
python -m pytest backend/tests
FRIDGELY_PYTHON=python node --test tests/functional/requirements.test.mjs
```

The old 501 placeholder is replaced by a JSON-lines adapter launching the actual
Python host and actual migrated SQLite database per acceptance context. Only the
external recipe provider and server clock are injected by the existing Node
fixtures. Account registration, Argon2, signed JWT verification, routing, SQL
queries, transactions and the existing feature services execute for real.

Two timestamp cases now explicitly sign in again after advancing the clock by
one or more hours. Their original assertions remain intact; the real one-hour
JWT policy is preserved. The separate authentic-expired-token case still asserts
401 after the issued token's expiry. Tests do not disable expiration or substitute
an application to make the assertions pass.

The host integration test creates two real accounts, records preferences and
inventory, generates/opens/favorites a recipe, adds missing shopping items,
checks foreign access and sanitized failure, then reopens a fresh host against
the same database and verifies all five personal collections.

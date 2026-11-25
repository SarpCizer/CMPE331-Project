# Fridgely web application

The React client uses the integrated FastAPI host through same-origin `/api`.
All personal lists are read/written in the server database. No demonstration
inventory, silent mock recipe fallback or shared localStorage list is present.

Features: registration/sign-in, fridge names/addition dates, saved dietary/allergen
preferences, generated recipe details with estimate labels, missing-ingredient
shopping lists, favorites and viewed history. Recipe viewing/favoriting never
deducts inventory. Error, empty and loading states are explicit.

The JWT and account email live in tab-scoped sessionStorage, allowing a reload
without saving a password. Logout clears session and all in-memory personal
collections, closes recipe details and cancels requests from the previous session.
Invalid sessions return to sign-in. The API client never trusts browser owner IDs.

Field errors are associated with their inputs, focus the first invalid input and
prevent invalid writes. Each server collection loads independently. An unavailable
collection shows its own retry control instead of a fabricated empty list; other
screens remain usable. A completed mutation is acknowledged separately from its
subsequent refresh. Recipe actions show pending/error/success feedback inside the
modal, prevent duplicate submissions and link to the resulting shopping list.

## Team handoff: use the integrated branch

Refs #16, #35, #36, #37, #38, #39. Start from reviewed `main` for the
current application. [PR #56](https://github.com/SarpCizer/CMPE331-Project/pull/56)
records the initial integration. See the [delivery guide](../docs/submission.md)
for the approved course archive and the separate live demo revision.

From the repository root, using Python 3.12, Node 24 and pnpm 11.25.0:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-app.lock
python -m pip install --no-deps -e backend
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
export DATABASE_URL=sqlite:///./fridgely.db
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m fridgely_app migrate
python -m uvicorn fridgely_app.host:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and create an account. Keep this terminal running.
The database persists across restarts. The command above creates a new local
signing key each time; existing browser sessions then need to sign in again.
For durable deployments, store a stable key in the server environment. The app
does not automatically load `.env`. Never commit a local environment file or DB.

For frontend editing, keep that backend running and use a second terminal:

```bash
pnpm --dir frontend dev
```

Open the Vite URL printed in that terminal (normally `http://127.0.0.1:5173`). Its
`/api` proxy points to backend port 8000. The built app on port 8000 needs a rebuild
after source edits; Vite reflects edits during development. A connection refusal
means the backend terminal stopped or port 8000 is occupied: check that terminal
and `http://127.0.0.1:8000/api/health`. Use the health endpoint, not a successful
Vite page alone, to verify backend connectivity.

| Screen / interaction | Real API under `/api` |
| --- | --- |
| Register / sign in | `POST /accounts`, `POST /sessions` |
| Preferences | `GET`, `PUT /profile/preferences` |
| My fridge | `GET`, `POST /inventory`; `DELETE /inventory/{id}` |
| Generate / details | `POST /recipes/generate`; `GET /recipes/{id}` (records view) |
| Missing ingredients | `POST /recipes/{id}/shopping-items` |
| Shopping list | `GET`, `POST /shopping-items`; `DELETE /shopping-items/{id}` |
| Favorites | `GET`, `POST /favorites`; `DELETE /favorites/{recipeId}` |
| Recently viewed | `GET /history` |

The interactive schema is `http://127.0.0.1:8000/api/docs`. Sign in through
`POST /sessions`, then use the returned bearer value with Swagger's Authorize
control. All protected endpoints derive the account from the signed session.

Without a configured server-side recipe provider, generation returns a visible
retryable 503. Accounts, inventory and personal lists still work. The separate
test host below supplies controlled recipes. See [provider setup and live
evidence](../docs/cloud-deployment.md) for the integrated Cloudflare and OpenAI
options and the public Render deployment.

## Build and run

Use Node 24 and pnpm 11.25.0; the committed lockfile pins resolved dependencies.

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm build
```

Start the backend using [the host instructions](../backend/README-host.md). Its
production build handler serves `frontend/dist`, so opening `http://127.0.0.1:8000`
loads both the UI and API. Hash navigation avoids collisions with the approved
root API routes, including `/favorites` and `/history`. During frontend
development, `pnpm dev` proxies `/api` to port 8000.

## Browser tests

Start the real integrated application with the controlled external provider and a
disposable SQL database:

```bash
FRIDGELY_TEST_PORT=8091 PYTHONPATH=backend/src python backend/tests/serve_web_test.py
```

Then run `pnpm exec playwright install chromium` and
`WEB_BASE_URL=http://127.0.0.1:8091 pnpm test:e2e` from this directory. Build first.
Port 8091 keeps these fixture-backed tests separate from the production preview.
On a machine with a supported installed Chrome, set
`PLAYWRIGHT_CHANNEL=chrome` to use an isolated browser profile. The production
application has no fixture-provider or demo-account mode. Browser fixtures live
only under backend tests. `TEST_DATABASE_URL` can select a dedicated PostgreSQL
test database; never use a shared live database for these tests.

`kitchen.spec.js` covers complete account/list/recipe flows, ownership switching,
three viewport widths and keyboard-only use. `completion.spec.js` adds associated
validation, slow/failed collection isolation, expired sessions during outages,
committed-write/failed-refresh handling, modal feedback, safe provider errors and
three-width accessibility checks. HTTP fault interception is limited to the
specific outage being tested; successful requests use the real application/SQL.

## Exact preference values

`src/preferences.js` keeps persisted dietary/allergen entries reversible in the
editable fields: commas separate entries, double quotes group a name containing
commas or surrounding whitespace, and doubled quotes represent a literal quote.
The multiline fields also preserve line breaks in an already saved quoted name.
Unquoted simple names retain the existing trimming behavior. Exact saved values,
order and repeated entries survive reload/save; clearing a field sends an empty
array. Invalid quoting is associated with its field and sends no write.

`preferences-fidelity.spec.js` checks this boundary through real authenticated
API requests and browser saves, including editing one list without changing the
other. Retain the helper and these regressions when extracting pages/components
or changing the HTTP/style/router libraries. The API and database schema are
unchanged. Refs #16, #20, #35, #62.

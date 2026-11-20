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
PYTHONPATH=backend/src python backend/tests/serve_web_test.py
```

Then run `pnpm exec playwright install chromium` and `pnpm test:e2e` from this
directory. On a machine with a supported installed Chrome, set
`PLAYWRIGHT_CHANNEL=chrome` to use an isolated browser profile. The production
application has no fixture-provider or demo-account mode. Browser fixtures live
only under backend tests. `TEST_DATABASE_URL` can select a dedicated PostgreSQL
test database; never use a shared live database for these tests.

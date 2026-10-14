# Fridgely requirements tests

Run with Node 20 or newer: `npm test`, or `node --test tests/functional/requirements.test.mjs`. No package installation or live AI credentials are required. There are 27 test cases covering all 15 stories. An exit code of 1 is expected while the features are unimplemented.

`src/acceptance-app.mjs` exports `createAcceptanceApp({ recipeProvider, clock })`. It currently returns HTTP-style 501 responses for all requests. Tests assert concrete success, validation, isolation and state-transition behavior, so failures expose missing functionality instead of being hard-coded failure assertions. Setup-dependent cases will first fail at registration; they reach their feature-specific assertions as prerequisites are implemented.

The boundary is an in-process acceptance adapter, not a running web server or browser. The future adapter should send requests through the real application's routing/business layer (or an HTTP client for a separately started backend) and translate HTTP responses into `{ status, body }`. It must not implement a second application inside the tests. Inject the clock and provider fixture into the application during tests. FastAPI can be supported by a launcher/client adapter; Node is test tooling, not an approved production stack.

Fixtures are deterministic recipe outputs with example calorie/time values, not verified nutritional data. Data is fresh for each `createAcceptanceApp` instance. A real adapter must isolate its database for each test. Tokens from sign-in must carry the authenticated account identity. Never expose provider configuration or a reset/seed endpoint in production.

Quality cases are also provided in [tests/non-functional/cases.md](non-functional/cases.md). Browser rendering, JWT signature verification, password hashing, real provider timeouts, storage restarts, deployment and load require additional integration checks; this suite alone cannot prove them.


## Review revisions on 11 October

All fixture setup writes and state reads assert the expected status before their results are used. Detached snapshots prevent later in-memory mutations from making before/after comparisons pass incorrectly. Recipe tests use IDs returned by the application rather than requiring provider fixture IDs. Invalid recipe candidates now violate one rule per case. US-15-T03 uses a real issued token and advances the injected clock past its `exp` claim; a malformed or unsigned example is not considered an expiry test. The application adapter must use the injected clock for token validation as well as timestamps.

These are acceptance tests against the still-unimplemented boundary. They do not prove JWT signature verification, actual persistence or timeout behavior. NFR checks remain required. Rejected generation is checked through error responses and unchanged inventory/history; database-level verification that no recipe candidates were persisted is still pending the database implementation.

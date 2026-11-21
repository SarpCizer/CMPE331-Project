# Unit and integration module mapping

| Executed module | Requirements / purpose |
| --- | --- |
| `backend/tests/test_accounts_database.py` | US-01/02/03/04/05/06/15; hashes, JWT claims, ownership, atomicity and constraints |
| `backend/tests/test_relational_preferences.py` | US-01/03/15; legacy upgrade, ordered repeats, relational keys, clearing/isolation and concurrent normalization |
| `backend/tests/test_collections_api.py` | US-08/10/11/12/13/14/15; shopping, owned recipe details, favorites/history and validation |
| `backend/tests/test_transactions_and_integration.py` | Collection transactions, idempotence, ownership and no hidden inventory changes |
| `backend/tests/test_recipe_integration.py` | US-07/08/09/15; provider inputs, full-batch validation, declared exclusions and rollback |
| `backend/tests/test_host_integration.py` | Actual account/inventory/preferences composition with recipes/collections; persistence and sanitized failures |
| `backend/tests/test_default_timeout.py` | US-09 / NFR-04; actual 28-second budget, cancellation and unchanged state |
| `backend/tests/test_process_persistence.py` | NFR-07 / US-15; two separate processes, both supported engines and two users/five collections |
| `backend/tests/test_api_documentation.py` | Real OpenAPI paths/models, bearer authorization, local documentation assets and CSP |
| `tests/functional/requirements.test.mjs` | 27 executable cases with criterion-level mapping in traceability.csv |
| `tests/fullstack/accounts-isolation.http.test.mjs` | 12 real HTTP authentication/authorization cases |
| `frontend/tests/kitchen.spec.js` | Eight production-build browser, layout, accessibility and keyboard cases |
| `tests/security/penetration.mjs` | Four scoped attack probes, including actual-browser stored XSS |

Read raw JUnit and source-coverage denominators with this table. Some module tests use isolated service ports; combined host/HTTP/browser cases establish the actual integration. Controlled provider fixtures do not establish live provider availability or hidden-allergen safety.

# Sarp's backend handoff: issues #30-#34 and #16

This guide describes the personal-collections module on `backend_work`. It does not merge or replace teammates' branches. The account, inventory, recipe and React implementations are exercised from the separately pinned team checkout.

The accidental full-application snapshot was reverted to the collections-only
`a38b8b4` tree. PR #9's account/database code and #10's host composition were read
to verify the existing `AccountPrincipal`, `CoreCallbacks`, session and DTO
interfaces; those implementations are not copied into this branch. They remain
separate team PRs for review and merge. The standalone CI now names only the three
collections test files, so a future merge of #9 does not make that minimal-dependency
job collect the other contributor's account tests. Full-host verification remains
isolated in the compatibility checkout.

## 1. Responsibility and issue map

| Issue | Implemented behavior | Main tests |
|---|---|---|
| [#31](https://github.com/SarpCizer/CMPE331-Project/issues/31), US-11 | List/add/delete owned shopping items; validate names; preserve ID on normalized duplicates; never restock inventory | `tests/test_collections_api.py`: `test_us11_*`, `test_concurrent_duplicate_shopping_inserts_preserve_one_id` |
| [#32](https://github.com/SarpCizer/CMPE331-Project/issues/32), US-10 | Owned recipe minus owned inventory names; normalized distinct missing names; atomic upserts; existing IDs retained; no inventory writes | `test_us10_add_missing_deduplicates_and_preserves_stock`, concurrent add-missing test, partial-write rollback test |
| [#33](https://github.com/SarpCizer/CMPE331-Project/issues/33), US-12/13 | Idempotent favorite save, full recipes, owner check on body recipe ID, independent favorite deletion | `test_us12_*`, `test_us13_*`, cross-account URL/body tests |
| [#34](https://github.com/SarpCizer/CMPE331-Project/issues/34), US-14 | One most-recent view per account/recipe; UTC and stable ordering; details commit the view before success; failures preserve state | `test_us14_*`, `test_failed_history_commit_never_returns_success`, `test_history_dependency_failures.py` |
| [#30](https://github.com/SarpCizer/CMPE331-Project/issues/30), shared with Ayşe/Mustafa | Complete, owner-scoped detail DTO; existing root API and frontend `/api` prefix use the same JSON fields | `integration_tests/test_sarp_collections_contract.py` |

Issue descriptions and the approved API remain the behavior baseline. Tests do not constitute independent teammate/course approval. The issue checkboxes remain for actual review and evidence acceptance.

## 2. Where to change a behavior

| File | Purpose | Example change |
|---|---|---|
| `src/fridgely_collections/api.py` | HTTP paths, body mapping, status codes, authentication dependency and public error envelope | Add/change a route, keeping the API contract and frontend in agreement |
| `schemas.py` | Request/response fields and name/identifier validation | Change a field only after coordinating it with recipe/UI owners |
| `service.py` | Business rules, owner checks, operation-level transactions and view clock | Change missing-name rules or when a view is recorded; write the failure test first |
| `repository.py` | SQL operations, upsert keys, stable IDs, monotonic latest-view updates | Change persistence behavior while retaining uniqueness/ownership and commit-before-success |
| `models.py` | Sarp's three table mappings | Coordinate schema changes with Berfin's shared Alembic migrations |
| `ports.py` | `AccountPrincipal`, `OwnedRecipe`, `CoreCallbacks` integration contracts | Keep these contracts compatible with the shared host |
| `adapters.py` | Uploaded-backend inventory reader and explicit legacy-recipe DTO conversion | Map data formats without guessing ownership, nutrition or ingredient quantities |

All database writes by this module target shopping, favorite or view records. It never changes inventory, preferences or accepted recipes. An object's absence and another account's object both return 404. Caller-supplied owner IDs are never trusted.

## 3. Shared auth, recipe and frontend contract

The current teammate candidate is `feature/berfin-cloud-candidate`, pinned for compatibility at `929776ccc51d914084ebb49d5997942c51c64b58`. Its `fridgely_app.host.create_app` already composes these unchanged ports:

```python
collections = build_collections(
    session_factory=api.state.sessions,
    require_account=api.state.authentication.require_account,
    core=CoreCallbacks(recipes.store.find_owned, inventory_names),
    clock=clock,
)
```

Berfin's dependency verifies the JWT and supplies `AccountPrincipal`; Ayşe's store supplies an accepted `OwnedRecipe`; the inventory reader returns the verified account's names. These read ports share the service transaction and must not commit or mutate other data. Shared FK and migration enforcement remains in the team's database layer.

`GET /recipes/{id}` returns `{id,title,ingredients,steps,cookingMinutes,caloriesPerServing,servings}`. History returns `[{recipe,lastViewedAt}]`; shopping returns `[{id,name}]`. Arrays, field names and no-wrapper responses are unchanged. The shared host exposes them at both the approved root routes and `/api` for the React client.

If another host already has a detail route, set `include_recipe_details=False` and have its authenticated detail handler use `collections.service.open_recipe`. Do not mount two competing detail handlers. A successful detail response must follow the committed history write.

## 4. This revision's history fix and TDD boundary

Before this fix, `open_recipe` called the clock before reading the owner-qualified recipe. A broken clock masked the required missing/foreign 404 with 500 or 503. A thrown clock exception for an owned recipe also became a generic 500.

The service now checks the owned recipe first. Only an accepted detail lookup requests a timestamp. Clock faults return a sanitized 503 and roll back; no success, new history, inventory change or raw diagnostic is emitted.

The five regressions were committed first at `fc2a560`; all five failed against the unchanged `862005f` implementation. The service fix at `63dcd7a` made them pass. This is real RED/GREEN evidence for this revision. The original 19 November implementation was not retroactively relabelled as tests-first.

The actual AI contribution and observed mistake are recorded in [ai-traceability.md](ai-traceability.md) for shared issue #46.

## 5. Reproduce the checks

Standalone, from the repo root with the package's locked test dependencies:

```sh
python -m pytest backend/tests -q
```

For compatibility, prepare a **new, clean, detached, disposable checkout** outside this development repository:

```sh
git worktree add --detach ../sarp-team-test 929776ccc51d914084ebb49d5997942c51c64b58
python -m pip install -r ../sarp-team-test/backend/requirements-app.lock
python -m pip install --no-deps -e ../sarp-team-test/backend
python backend/scripts/verify_team_compatibility.py --team-root ../sarp-team-test --output-dir ../sarp-test-evidence
```

Use an isolated virtual environment. `--node` selects Node explicitly if it is not on PATH; `GIT_BINARY` similarly selects Git. The verifier overlays only this branch's collection module and two named test files in the temporary checkout. It refuses an active branch, dirty checkout, unexpected revision or output directory inside a source tree. It never fetches, commits or pushes a teammate branch.

The verifier runs the complete team Python suite plus the new Sarp contract/regression cases, then the team's 27 real-host acceptance cases. It saves JUnit, logs, the pinned team revision and normalized source hashes. It checks that every tracked teammate input outside the overlaid collection module retained its original hash. An isolated `TEST_DATABASE_URL` plus `--require-postgres` is required to claim PostgreSQL verification; the CI job supplies PostgreSQL 17. No live provider credential is forwarded.

`.github/workflows/sarp-collections.yml` runs standalone checks and this pinned compatibility test on changes to `backend_work`. PR checks upload their actual evidence; inspect the run before claiming success. A new teammate revision must be reviewed and pinned explicitly before changing the compatibility baseline. Passing fixture-backed API tests does not prove cloud deployment or live-provider behavior.

Local results on 23 November: **64 standalone tests passed**, **126 shared-host Python tests passed with one PostgreSQL test skipped**, and **27 real-host acceptance tests passed**. The verifier confirmed all tracked teammate inputs outside the intentional collection overlay retained their hashes. Local PostgreSQL was unavailable; these results do not claim a local PostgreSQL pass. The machine-readable record is [verification.json](verification.json); GitHub CI separately requires that PostgreSQL test to run without skips.

## 6. Review and owner actions

The focused PR references #31, #32, #33, #34, shared #30 and review #16. Ask Berfin to inspect the auth/database boundary and Ayşe to inspect recipe/detail integration. Their actual approvals remain human actions; the assistant does not supply them or close the issues on their behalf.

[#22](https://github.com/SarpCizer/CMPE331-Project/issues/22) asks the repository owner to protect `main`. This is a GitHub repository setting, not a change that can stay in `backend_work`. Under the user's branch-only restriction, no main protection, merge, release or other branch update is applied here. The prepared owner checklist is [main-protection.md](main-protection.md).

# Decisions for requirements review

The charter establishes the feature scope. The following details make it testable and are proposed for approval; they are not claims that the charter already specifies them.

| ID | Proposed decision | Why it matters |
|---|---|---|
| D-01 | Use user stories; test backend behavior through a neutral HTTP acceptance contract | Gives every story stable tests without selecting the production backend |
| D-02 | Password minimum eight characters; case-insensitive email uniqueness; no email verification | Registration rules require an explicit agreed policy |
| D-03 | Store server UTC ISO 8601 timestamps and display local dates; ingredient names trim whitespace and compare case-insensitively | Makes addition dates and missing-ingredient comparison repeatable |
| D-04 | Inventory stores ingredient names; no quantity/unit reconciliation or expiry fields in this baseline | Charter defines manual names and dates but not quantity arithmetic |
| D-05 | Empty fridge blocks generation; malformed responses and declared allergen conflicts are rejected; provider failure is retryable | Defines AI edge cases without expanding core features |
| D-06 | Cooking time is total minutes; calories are estimated per serving, accompanied by a serving count | Charter does not specify calorie units or serving basis |
| D-07 | Missing ingredients are determined by normalized names; repeated shopping/favorite actions are idempotent | Prevents avoidable duplicate items |
| D-08 | Shopping management includes manual add/list/delete; deleting an item does not update the fridge | Keeps inventory additions manual |
| D-09 | Recipe history records detail views, one entry per recipe, newest first | Defines what “previously viewed” means |
| D-10 | Proposed numeric quality targets are in non-functional.md | Charter gives no performance/recovery targets |
| D-11 | Backend, database, frontend framework, AI provider, hosting and exact allergen/diet taxonomy remain undecided | Charter lists alternatives; requirements tests do not choose them |
| D-12 | Team designates a project manager/contact; internal estimates are confirmed by the team | Charter lists development roles without naming a project manager |

The test scaffold uses Node's standard test runner only as development tooling. A production implementation may be Express or FastAPI if it implements the reviewed contract through the test adapter. User-facing recipe estimates must not imply measured nutrition values or guaranteed allergen safety. Validation can reject declared ingredients; hidden ingredients and cross-contamination are outside what the app can verify.

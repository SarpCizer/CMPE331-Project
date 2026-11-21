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

## Implemented choices submitted for team review (21 November 2026)

Refs #16, #21. The rows below record actual implementation choices; team confirmation is still required in the PR and is not inferred from implementation.

| Choice | Responsible role | Decision and rationale |
| --- | --- | --- |
| Backend / database | Full-stack/database | FastAPI + SQLAlchemy + Alembic, PostgreSQL 17; retain the actual implemented teammate modules instead of replacing them with the earlier proposed Express implementation. |
| Browser | Full-stack/frontend | React 19/Vite, native fetch and repository CSS tokens; preserve the tested UI without introducing Axios/Tailwind solely to match a superseded design library list. Their functional roles are implemented by the existing client/styles. |
| JWT | Full-stack/auth | HS256, persistent >=32-byte server secret, issuer/audience/account validation, one-hour expiry; checks use the same injected server clock. |
| AI / hosting | AI and DevOps, integrated by full-stack | OpenAI Responses provider behind an injected port; Render Docker web service + managed PostgreSQL. Actual cloud activation and provider credential remain separately verified release steps. |
| A-01 | Full-stack/database + AI | Implement account-owned accepted recipe snapshots; no global shared catalog. |
| A-02 | Full-stack/database | Ordered relational dietary/exclusion rows in #49, preserving exact strings, order and duplicates; derived keys are not unique. |
| A-03 | Backend collections + database | Unique owner/shopping key and owner/recipe associations with composite foreign keys. |
| A-04 | Backend collections | History ties use recipe ID ascending after timestamp descending; implemented repository ordering. |
| A-05 | Full-stack + AI | Snapshot generation input at request start; PostgreSQL reader uses REPEATABLE READ. Later requests see later committed preferences. |
| A-06 | Backend collections | Commit owned detail/history upsert before successful response. |
| Vocabulary | AI + product owner | Trim/casefold exact declared-name matching; no unreviewed synonym dictionary or allergen-safety guarantee. |
| Governance and dates | Team contact / product owner | Updated instructor email: test PR 25 November, approved PDF 29 November; review #16 lists artifacts for 29 November. Internal target remains earlier. Team must identify/confirm the contact and retain actual independent reviews. |


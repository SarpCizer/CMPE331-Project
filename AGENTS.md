# Fridgely coding-assistant instructions

Read the approved stories under docs/requirements and the current issue before changing behavior. Work on one English-named feature/fix/test/docs branch and a focused PR. Reference the task issue and #16. Never push or merge to main on an assistant's initiative.

Preserve teammates' recipe and collection ports. Identity comes from verified JWT subjects. Inventory changes only through explicit user actions: manual add/edit/delete, confirmed cooking (#81), or an explicitly confirmed shopping purchase (#85). Generating/viewing/favoriting recipes never deducts stock. Cooking must use reviewed quantities, atomic owner-scoped updates and durable retry protection. Keep provider credentials server-side; never commit, log or ask for secrets in chat. Production must not use fixture providers.

For a behavior change, write a meaningful failing test first, record the failure against the preceding source, implement the fix, and retain both commits. Do not invent TDD history for older work. Run the relevant tests, build and integrated checks. Distinguish fixture-backed provider tests, PostgreSQL/container checks and actual cloud/live-provider results.

Before a PR, review input validation, ownership, commit-before-success transactions, cancellation/error states and migrations on existing data. Report actual test counts, source revisions and limitations. No fabricated coverage, reviewer approval, teammate authorship or course-platform submission.

Use prompts/implement-feature.md and prompts/review-change.md as repeatable starting points. The developer remains responsible for reviewing generated work.

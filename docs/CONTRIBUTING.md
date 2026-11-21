# Branching, reviews and versioning

Refs #16, #22, #24. Use small English branches: `feature/<owner>-<purpose>`, `fix/<owner>-<defect>`, `test/<owner>-<scope>`, `docs/<owner>-<scope>` or `ci/<owner>-<scope>`. Keep one review purpose per PR. Link the task issue, #16, exact tests/evidence, AI assistance and dependent PRs. Never commit credentials, local databases or installed libraries.

Stacked PRs target the preceding feature branch to keep diffs focused. Current integration order is #9 -> #10 -> #11 -> #12 -> #13 -> #14 -> #15 -> #49, followed by workflow/docs and final evidence PRs. #10 preserves the exact recipe and collections module commits, including Ayse's #7; #8 is Kerem's independent CI/report draft and must be reviewed with him before deciding how to reconcile its overlap. Preserve #6's design review separately. Do not merge or close another teammate's work without the team's decision. When reviewed parents are merged, the team contact retargets/rebases dependent PRs under a checked plan. This work performs no main merge.

At least one teammate other than the author must approve a merge. Yeşim is also requested for course deliverables. Address review findings with linked commits; do not equate a request, a bot check or an author review with independent approval.

## Version policy

The initial candidate is `0.1.0`, matching backend/frontend metadata. Use Semantic Versioning: PATCH for compatible fixes, MINOR for compatible features and MAJOR for incompatible public contracts after 1.0. Before 1.0, explicitly document every contract-breaking change and increment MINOR. Database revisions are separate, ordered Alembic IDs; do not use application version numbers as migration identifiers.

Create an annotated `v0.1.0` tag only on the approved integrated commit after the authorized team merge and successful CI. Release notes record the commit, migrations, API changes, executed tests, deployment and rollback constraints. No release tag is created on an unreviewed main branch. Later changes follow the same reviewed-commit rule; never move a published version tag.

## Repository-owner settings still required

SarpCizer must enable main protection: pull requests required, at least one approving review, stale approvals dismissed after new code, required successful integrated checks and no direct pushes. Restrict bypass rights deliberately. Verify these settings with a test PR; writing this policy does not enable protection. Berfin's current repository permission is push, not admin, so the assistant cannot truthfully mark that setting applied.

Use the team's GitHub Project to track issues #17-#48 with assignee, milestone, status, linked PR and evidence. Issue creation alone is not proof of GitHub Projects usage. The team contact maintains #16, checks only verified items, and keeps review/cloud/submission actions pending until observed.

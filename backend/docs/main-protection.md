# Owner checklist for issue #22

This is a concrete proposal for Sarp as repository owner. It is **not an applied setting**. It is stored on `backend_work` because the user explicitly limited this task to that branch. Kerem owns the broader workflow issue; coordinate the setting and its test PR with him.

In GitHub repository **Settings > Rules > Rulesets**, prepare a branch ruleset targeting exactly `main`:

1. Require a pull request before changes reach `main`.
2. Require at least **one approving review from someone other than the author**. Dismiss stale approvals when reviewed code changes.
3. Require conversations to be resolved and successful status checks before merging. Prefer the branch to be up to date before its final checks.
4. Block force pushes and deletion of `main`; do not configure an ordinary direct-push/admin bypass of these requirements.
5. Select only stable check names that the team's final workflow reports for every PR. The current candidate exposes:
   - `Repository secret scan`
   - `Cloud image and PostgreSQL smoke test`
   - `Verify tested source identity`
   - `API, PostgreSQL, browser and load tests`
   - `Enforce source coverage policy`
   - `SonarQube analysis and evidence`

The team's workflow must be reviewed/available on the intended integration revision first. Do **not** make a path-filtered Sarp-only workflow a mandatory check for unrelated documentation PRs: a check that never starts can block them indefinitely.

Before activation, review owner/admin access, required check availability and the team's agreed merge order. After the authorized setting is applied, use a harmless test PR to verify that missing approval or a failed required check blocks merge, and that a reviewed green PR can merge. Record the real ruleset and test-PR links in #22 and #16. Do not tick those issue boxes based on this document alone.

No protection setting, branch deletion, teammate approval, main merge, release tag, deployment or course-platform upload has been performed by this revision.

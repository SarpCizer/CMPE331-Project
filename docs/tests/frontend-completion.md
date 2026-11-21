# Frontend completion and team handoff

Refs #16, #35, #36, #37, #38, #39. This work updates existing PR #56 and its
`feature/berfin-cloud-candidate` branch. It does not open another branch or merge
main. The runnable setup and API mapping are in [the frontend handoff](../../frontend/README.md).

## Observed gaps and changes

- Account and preference forms now display errors associated with the relevant
  input, focus the first invalid field, and avoid invalid HTTP writes. Whitespace
  ingredient/shopping names receive the same treatment. Preferences use the
  backend's 100-entry / 128-character limits.
- Each collection loads and retries independently. Failed or slow favorites do
  not block the fridge, discard loaded data or fail unrelated committed writes.
  A 401 from any collection ends the session even when another request fails first.
- Mutation success and refresh success are separate outcomes. A committed write
  with an unavailable refresh is acknowledged; Retry reads the list without
  repeating the write.
- Recipe modal errors and success messages are visible inside the modal; pending
  actions disable duplicate submissions. Adding missing ingredients provides a
  direct link to the resulting shopping list. Provider 422/502 diagnostics are
  replaced with safe messages and previous generated cards survive failure.
- The sign-in introduction now has a named landmark. New accessibility checks
  include validation and unavailable states at 360, 768 and 1440 pixels, together
  with the existing keyboard and complete flow checks.

## Test-first evidence

Production baseline: `a7c7456fd5eac0f6911b0c72d3fc0b3c0d1a1018`.
Failing-test commit: `2b2797fb14f3353eb4f50ca3e8f66c77e008d710`.
All nine initial `completion.spec.js` regressions failed against that unchanged
built frontend before production edits. The tenth regression (committed write /
failed refresh) was added during implementation review; no earlier test-first
history is claimed for that additional assertion. The old eight browser tests
are retained. Both commits remain in the PR history.

The isolated browser host runs the real FastAPI app, real SQL and signed sessions
on port 8091 with a controlled external recipe provider. Outage tests intercept
only specified HTTP failures. This is not a cloud or live-provider test.

Local verification: **18/18 browser tests passed** in 23.4 seconds. V8 mapped
coverage: lines 100%, branches 92.18%, functions 92.45%. Mapped line coverage is
not a claim that every possible behavior is tested. [RED JUnit](evidence/frontend-completion/red-junit.xml),
[GREEN JUnit](evidence/frontend-completion/local-green-junit.xml),
[GREEN log](evidence/frontend-completion/local-green.log),
[coverage](evidence/frontend-completion/local-coverage.json) and the
[exact source hashes](evidence/frontend-completion/source-manifest.json) are retained.
GitHub Actions runs the complete PostgreSQL, image, security and Sonar checks
for the new source; its final result is recorded after completion. Historical coverage/load/Sonar results
in the main report remain attributed to their original revision; they are not
silently relabelled as results for these new frontend changes.

## Review and release boundaries

Frontend peer review by Mustafa Safa and QA review are still required. Team
members can run this complete candidate immediately using the handoff guide.
Render repository access, a public HTTPS deployment, a real provider credential,
independent approvals and course-platform uploads remain separate observed
release steps. They cannot be completed by checking a documentation box.

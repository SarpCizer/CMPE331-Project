# Frontend completion and team handoff

Refs #16, #35, #36, #37, #38, #39. This work updates existing PR #56 and its
`feature/berfin-cloud-candidate` branch. It does not open another branch or merge
main. The runnable setup and API mapping are in [the frontend handoff](https://github.com/SarpCizer/CMPE331-Project/blob/feature/berfin-cloud-candidate/frontend/README.md).

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

Local verification: **18/18 browser tests passed** in 24.6 seconds. V8 mapped
coverage: lines 100%, branches 92.24%, functions 92.45%. Mapped line coverage is
not a claim that every possible behavior is tested. [RED JUnit](evidence/frontend-completion/red-junit.xml),
[GREEN JUnit](evidence/frontend-completion/local-green-junit.xml),
[GREEN log](evidence/frontend-completion/local-green.log),
[coverage](evidence/frontend-completion/local-coverage.json) and the
[exact source hashes](evidence/frontend-completion/source-manifest.json) are retained.
GitHub Actions [run 44943105424](https://github.com/SarpCizer/CMPE331-Project/actions/runs/44943105424)
executes source `522e0db8e2a9c6d9c3e22b5b8a71e9de05ffc82a`. Its application job
passes **106 Python, 27 acceptance, 12 HTTP, 18 browser and four penetration cases**.
The production image passes PostgreSQL restart/isolation checks. Five-minute
PostgreSQL load: **50,068 requests, p95 172.64 ms, zero errors**. CI mapped frontend
coverage: lines 96.39%, branches 92.24%, functions 92.45%; backend statement/branch
coverage: 91.44%/72.83%. The actual coverage policy and its negative canary pass.
The raw logs/JUnit are under `evidence/ci-frontend`, coverage under `coverage`, and
non-functional results under `non-func-tests`. That scan reports one MAJOR `javascript:S9383` finding, with zero critical/blocker
findings or security hotspots. The selected original finding fields and artifact
identity are retained in `quality/frontend-522-findings.json`. Follow-up
`25c111aa5a8d678b60c17745289675821b62f91d` explicitly marks the handled background
load with `void`; all 18 local browser cases pass again. Its complete CI and
follow-up Sonar analysis are verified separately before final publication. Historical coverage/load/Sonar results
in the main report remain attributed to their original revision; they are not
silently relabelled as results for these new frontend changes.

Supplementary browser walkthroughs also verify clearing saved preferences, fridge
search recovery, removing a favorite while retaining history, and idempotent
shopping additions/removal without inventory changes. The four results are in
[evidence/frontend-completion/secondary-flows.json](evidence/frontend-completion/secondary-flows.json);
they are separate from the 18-case suite.

## Review and release boundaries

Frontend peer review by Mustafa Safa and QA review are still required. Team
members can run this complete candidate immediately using the handoff guide.
Render repository access, a public HTTPS deployment, a real provider credential,
independent approvals and course-platform uploads remain separate observed
release steps. They cannot be completed by checking a documentation box.

## Final-source verification

Source `25c111aa5a8d678b60c17745289675821b62f91d`,
[run 44944497368](https://github.com/SarpCizer/CMPE331-Project/actions/runs/44944497368):
106 Python, 27 acceptance, 12 HTTP, 18 browser and four penetration scenarios pass.
The production image/PostgreSQL restart and actual coverage/secret policies pass.
CI frontend coverage is 96.39% lines, 92.18% branches and 92.45% functions.
The repeated five-minute measurement records 40,336 requests, p95 371.47 ms and
one connection-level failure (0.00248%). It satisfies p95 <=500 ms and errors <1%;
the non-success observation is preserved, not silently removed. The preceding
50,068-request result above belongs to source 522e0db. Runner variability is not
interpreted as a deployment SLA or an application regression.

Follow-up SonarQube reports **zero issues, bugs, vulnerabilities, smells and
security hotspots** for exact source 25c111a. All six workflow jobs pass. The gate
export is OK with an empty conditions array; explicit counts and the separate
coverage/secret policies are retained rather than treating OK as a custom gate.

# Final release verification

Refs #16, #40, #67. Continue from reviewed main
`abdca3f5b2e58d7842dacbe83a4c5d2722c13d3a` and retain its source-qualified
results; do not relabel earlier provider failures as successful final tests.

## Public source identity

Render supplies `RENDER_GIT_COMMIT` at runtime, documented in its
[default environment variables](https://render.com/docs/environment-variables).
The host exposes that value as `X-Fridgely-Revision` only when it is exactly a
40-character lowercase hexadecimal Git revision. It never accepts this value
from request headers and does not export other environment variables. The
existing API response bodies, authentication and cache/security headers remain.

This permits exact-source HTTPS verification without creating Render OAuth
grants, reading credentials or changing the existing free service configuration.
The header's contract uses synthetic metadata in isolated unit tests; only an
actual public observation after deployment establishes the live source.

Test-first evidence: before implementation at `c3558ba`, the source-identity
regressions reported **1 failed / 1 passed in 0.84s**. Red commit `601ade9`
retains the tests. After implementation, identity, API documentation and
security-header regressions reported **18 passed in 4.36s**. These are local
contract checks, not a deployment claim.

## Completion conditions

The final report must identify the exact measured source, actual successful CI
run, preserved raw artifacts, branch/review provenance and actual public release
identity. Verify the approved main source over HTTPS after all required checks
pass. Use disposable synthetic accounts for bounded functional checks and a
small number of real-provider requests; never run load or active attack scans
against production. Verify account return/password rotation, inventory,
generation/detail, shopping/purchase, favorites/history, cooking, planner and
wheel behavior with unchanged-stock checks where appropriate.

Preserve previous live failures and the failed Windows benchmark. Controlled
provider throughput is not real model throughput. An uploaded course report,
team rehearsal or instructor acceptance requires its own observed evidence.

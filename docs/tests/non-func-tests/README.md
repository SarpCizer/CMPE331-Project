# Non-functional evidence and interpretation

`local-load.json` and the PostgreSQL measurements use 50 signed-in users, exactly
100 inventory entries per user, and a 300-second measured phase after setup. Each
user reads inventory, preferences, shopping and favorites, then pauses one second.
Shopping/favorites are initially empty and AI calls are excluded from the measured
loop. Overall and per-route p95 must be <= 500 ms and error rate < 1%.

The local result identifies macOS ARM64/SQLite/one application worker. The CI result
identifies the actual Ubuntu runner CPU count/Python version and PostgreSQL 17.
These are measurements of those environments, not a production SLA or proof about
the team's eventual agreed staging host. Keep the baseline with its connection
failure/outlier; do not silently discard non-success observations.

`provider-timeout.json` is produced by the real host's default 28-second timeout
test. It records actual elapsed time, provider cancellation and unchanged state
for all five personal collections. Other provider-boundary fixtures test malformed
output, declared allergen conflicts and rollback of the full recipe batch.

Persistence tests launch two separate Python processes against the same database,
sign in again, and compare two accounts' inventory/preferences/shopping/favorites/
history. Real PostgreSQL is required for the PostgreSQL case; SQLite results do
not substitute for it. Browser evidence covers core flows, three viewport widths,
automatic WCAG A/AA checks, contrast corrections and keyboard-only actions.

The remaining release evidence is HTTPS staging, a live-provider smoke check with
server-only credentials, and deployment-specific reproduction/performance. These
are stated separately from the completed local/CI checks.

# Instructor review: security and load profile

Related: [review of #67](https://github.com/SarpCizer/CMPE331-Project/pull/67#issuecomment-7198211995), #16 and #94.

## Sign-in guessing

The login route reserves a slot before password hashing, including concurrent
requests. Five failed attempts for one account and transport client within
60 seconds cause HTTP 429 with `Retry-After`. A successful login clears that
account/client bucket. A separate ceiling of 200 attempts per transport client
per minute bounds rotating account names; successful logins still count there.
Known and unknown accounts use the same limits and fixed public error.
Untrusted forwarded headers are not parsed by this component.

State is process-local, capped at 10,000 buckets, expires after the window,
and fails closed when full. It matches the current single-worker deployment.
A restart resets counters. Before multiple workers/replicas, replace it with
shared atomic storage and explicitly configure trusted proxies. This bounded
application control does not claim complete protection against distributed abuse.

Regression evidence covers known/unknown accounts, expiry and valid retry,
other-account use, forwarded-header spoofing, successful reset, simultaneous
reservations, rotating accounts and bounded-memory expiry. The earlier test-first
commit failed with missing 429 behavior; both red and implementation commits remain.

## Standard scanner and targeted probes

CI runs [OWASP ZAP's API scan](https://www.zaproxy.org/docs/docker/api-scan/)
with its pinned 2.17.0 image against the real API on loopback and a disposable
database. A controlled provider supplies recipes. No production scan or external
model call occurs. ZAP receives only a synthetic user's bearer token through
the [official authentication-header mechanism](https://www.zaproxy.org/docs/getting-further/authentication/handling-auth-yourself/).
It does not mount the repository or receive GitHub credentials.

A test-only instrumented host records protected successful HTTP requests during
the scan. A clean-looking report with no such authenticated request fails the
job. The active phase has a four-minute budget. High/medium alerts require
triage; low/informational alerts are retained. Failed setup attempts are retained
and are not counted as successful assessments. Reports and logs redact the
synthetic token/password before upload. Actual image digest, request counts,
source SHA, rules and severities are exported. This bounded OpenAPI scan cannot
prove that every business workflow or authorization state is secure; the existing
four probes and parameterized ownership matrix remain complementary evidence.

## Recipe generation under concurrency

`recipe_generation.py` launches the real HTTP host with a controlled 200ms
provider, ten signed-in users, one-second think time and a 60-second measured
phase. Its explicit experimental gate is p95 <= 2,000ms and errors < 1%; this
is separate from NFR-03's non-AI 500ms gate. All accepted recipes must persist
and stock snapshots must remain unchanged.

A second phase sends five simultaneous requests to a stalled provider. Each
must return retryable 503 within 30 seconds, cancel inference at the production
28-second deadline, leave stock unchanged, and create no partial recipe row.
This measures HTTP/application/database scheduling and cancellation under controlled
inference; it does not benchmark live AI latency, cost or provider quotas.

The existing five-minute NFR-03 experiment retains 50 users, 100 inventory rows
per user and four non-AI GET routes. Both experiments require the full current
Git SHA and clean application/test sources. Environment/database and source
identities must accompany comparisons; local SQLite and CI PostgreSQL results
remain separate even when their source revision matches.

## Evaluated Sonar conditions

The ephemeral Sonar server receives a selected project quality gate with five
overall-code conditions: zero bugs, vulnerabilities, BLOCKER and CRITICAL
violations; aggregate coverage at least 90%. An independent export policy also
requires zero security hotspots: the server's [condition validator](https://github.com/SonarSource/sonarqube/blob/master/server/sonar-webserver-webapi/src/main/java/org/sonar/server/qualitygate/QualityGateConditionsUpdater.java)
explicitly disallows `security_hotspots` as a gate condition. Export fails if any
required condition is missing, empty, unevaluated, altered or failing. The raw
server conditions and observed values are retained beside the actual dashboard
capture. Separate per-language line/branch policy checks remain active.

The historical empty-condition `OK` is preserved as historical evidence, not
reinterpreted as a real threshold decision. The twelve historical S2970 alerts
were false positives from confusing a custom Node assertion helper with Jest;
their helper rename did not repair twelve application vulnerabilities.

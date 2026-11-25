# Kerem's QA handoff — 25 November 2026

Refs #16, #22, #23, #41, #42, #43, #44. Codex assisted Kerem's assigned QA work.
This update is based on main `ebd8a5a9e2d9012f09582a4e6f9500072a60d094`.

## Assignment status and next actions

| Issue | Verified work | Remaining acceptance |
| --- | --- | --- |
| #22 branching/versioning/protection | CONTRIBUTING and the PR template are in main. Main's branch API still reports `protected:false`; the connected account has push access, not administration. | Sarp enables required PR/review/check protection and verifies it with a test PR. The team selects an approved green source before its first annotated version tag. |
| #23 CI | Seven-job integrated workflow, enforced language coverage, full-history secret scanning and negative canaries are merged. This QA change fixes the Sonar exporter accepting a failed gate. | Independent review and merge of this QA change; require the actual stable job names in owner settings. |
| #41 48 acceptance criteria / coverage | 15 stories, 48 criterion mappings; 28 acceptance cases pass locally. Source-matched CI coverage and genuine regression-first evidence are in the report. | No retroactive TDD claim: older work without a recorded RED run remains outside that claim. Later source results retain their own CI identity. |
| #42 security / penetration / Sonar | Existing HTTP and four scoped penetration checks are retained. This change adds the complete invalid-token method matrix, foreign URL/body references, seeded-secret inspection and enforced Sonar security metrics. | Independent review, exact-head integrated CI and merge. A scoped assessment is not an independent exhaustive penetration audit. |
| #43 performance | The recorded five-minute run at `a59556e` exercised 50 signed-in users with 100 inventory entries each: 47,400 requests, p95 204.06 ms, zero errors. Controlled timeout observed 28.03 seconds with cancellation and unchanged collections. | The named environment is GitHub Actions/PostgreSQL 17, not Render. Confirm that environment for the agreed criterion or plan a separate authorized deployment measurement. Do not load-test shared production data. |
| #44 report | [PR #67](https://github.com/SarpCizer/CMPE331-Project/pull/67) merged into main at `da81cc3c30cd781e48f15f6941173bd16aaf8631`. İrem and Sarp independently approved exact head `2d53035`. All report/evidence blobs checked against that head are unchanged. | The report's merge criterion is met. The PDF/ZIP pair remains the approved `a59556e` snapshot; a newer course source needs matched regenerated artifacts and PO selection under #48. |

The report PDF SHA-256 is
`d31e5df0e3dd2d2f446ec37762ef5e6a29b27faf9da0358d75bbad5e6cbf205f`.
Final combined main `682eea6` passed all seven jobs in
[CI 45582073405](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45582073405).
The approved report's application measurements remain pinned to `a59556e` and
[CI 45474025963](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45474025963).

## New authorization and credential checks

`backend/tests/test_security_matrix.py` runs against the real migrated host with
a controlled external provider. For each database (SQLite and disposable
PostgreSQL in CI), it contains 165 cases:

- 150 invalid-token cases: all 15 protected methods, both root and `/api`, each
  with missing, malformed, forged, correctly signed expired and unsigned tokens.
- 12 foreign-reference cases: all six URL/body resource references on both
  prefixes, using actual objects belonging to another signed-in account.
- Two credential/log cases: distinct Argon2 salts, verified hashes, sign-in,
  seeded JWT/signing/password/provider-diagnostic markers, and provider failure.
- One OpenAPI comparison that fails if the protected method inventory changes
  without updating the matrix.

Denied requests must return 401 (or 403/404 for foreign objects), leave every
database table unchanged and avoid provider calls. The inspection searches
database contents, captured application logs and error bodies; it does not
search a shared deployment or retain actual credentials. A successful sign-in's
intentional token response is not treated as an error leak.

Local verification: **294 backend tests passed, 177 explicitly skipped** without
PostgreSQL; **28 acceptance cases passed**. The final matrix alone passed
**165 cases**, with **165 PostgreSQL cases skipped**. Those skips require the
exact-head CI database run before claiming PostgreSQL success.

## Sonar policy and tests-first evidence

The previous helper printed a failed server gate and still returned success.
The new exporter rejects a non-OK server gate, failed/ignored conditions, and
missing/invalid/nonzero `bugs`, `vulnerabilities` or `security_hotspots` metrics.
It retains diagnostics and emits `quality-policy.json` before rejection.
An empty server gate is disclosed; three independent metric decisions still
run. Zero hotspot metrics do not imply completed manual hotspot review.

The published RED commit is `2f634a9e30b2ca48a057b1b2758a6e450a737437`.
Its exact regression file was executed before implementation as local commit
`860082b`: rejection assertions failed because no RuntimeError was raised;
two new policy-output checks also failed because no policy artifact existed.
An initial test revision tried to read that absent artifact too early; the
corrected RED test returns first so it exposes the gate acceptance itself.
After implementation, all **nine export-boundary regressions pass**. Logs are
retained in `evidence/kerem-qa/`; the Sonar CI job runs the same regressions.

No application behavior, migration, paid resource, live account, secret setting
or approved course artifact is changed by this QA work. The local provider is
controlled. Existing cloud completion belongs to #40; Learn upload and team
rehearsal remain #48. An independent teammate must review this QA PR before the
authorized merge process.

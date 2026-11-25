# Enforced verification and deployment checks

Refs #16, #23, #40, #41, #42. The integrated workflow runs on PRs, pushes to main and manual dispatch. It checks the actual PR head, pins dependencies, and exports evidence tied to that SHA. PostgreSQL process persistence, the production Docker image, API/acceptance/browser/penetration suites, five-minute non-AI load, dependency audits and SonarQube each retain their own measured result.

## Coverage and secret failure gates

`scripts/ci/check_coverage.py` reads actual coverage.py and mapped frontend summaries. Minimum percentages: backend statements 90, backend branches 70, frontend lines 90, frontend branches 85 and frontend functions 85. Missing or invalid reports fail the check. Statement/line coverage is not substituted with coverage.py's combined branch percentage. A synthetic zero-coverage input is executed as a negative canary and must be rejected.

Gitleaks 8.30.1 scans full reachable Git history with redacted logs and reports. Any finding fails the job. An isolated, randomly generated credential-shaped canary must also make the scanner fail; it is not a real provider token and is never committed. The canary result records only a detection count. No broad test-directory or source-directory secret allowlist is introduced.

The initial enforced scan stopped for two historical matches. Exact source review showed backend testing prose and a deliberately invalid unsigned JWT used to assert HTTP 401. Quoting the prose during triage produced two additional copies of that false-positive pattern. `.gitleaksignore` contains only the four exact historical commit/file/rule/line fingerprints, with explanations; the triggering quotation is removed from current triage text. New matches in these files remain subject to scanning. No actual credential is exempted and history is not rewritten. Both redacted finding exports are retained with the quality evidence.

Committing the original Sonar issue export also triggered 15 generic-key matches on Sonar-generated issue identifiers. Each flagged line was checked against an issue object's `key` in the exported schema. Only those 15 exact export-commit/file/rule/line fingerprints are additionally scoped; no Sonar report directory or other fields are excluded. Future API credentials in reports still fail scanning. The original exported issues and redacted scan findings remain available for review.

These jobs make a failing test, insufficient measured coverage or detected secret fail the PR check. Repository-owner branch protection must require successful checks; a workflow file alone cannot prevent a permitted direct push.

## SonarQube failure policy

The exporter must finish with an `OK` server gate and no failed or ignored
conditions. ERROR, NONE and unknown gate states fail the job after retaining the
raw exports. An empty server `conditions` array is recorded explicitly and is
not counted as a server threshold evaluation.

The exporter also enforces three concrete source-metric checks: `bugs`,
`vulnerabilities` and `security_hotspots` must each be present, numeric and zero.
Missing or invalid measurements fail. `quality-policy.json` records each check,
the server gate, whether server conditions were evaluated and the final result.
This conservative policy blocks reported hotspots; zero reported hotspots does
not certify a manual hotspot review or replace the scoped penetration tests.
The separate per-language coverage thresholds above still apply.

Nine export-boundary regressions exercise failure and success, including an
empty server gate with a nonzero security metric. They run in the Sonar job and
retain `gate-regressions.log`. The test-first sequence and security matrix are
linked from [Kerem's QA handoff](tests/kerem-qa-handoff.md).

## Reuse and release limits

Expensive test artifacts are reused only after `git diff` verifies the covered production, dependency, test and image inputs exactly match a named successful source revision. The recorded source/test/analysis revisions and immutable artifact identify this reuse. Changed covered inputs run the full suite again. Documentation-only changes do not become evidence of new application behavior.

The original Render service and Blueprint now select main. The verified automatic
deployment and bounded live Cloudflare results are recorded in
[the deployment guide](cloud-deployment.md) and closed issue #40. CI load tests
remain isolated PostgreSQL measurements, distinct from those live smoke results.
See [#22](https://github.com/SarpCizer/CMPE331-Project/issues/22) for the verified
branch protection and annotated release tag, and
[#48](https://github.com/SarpCizer/CMPE331-Project/issues/48) for the approved
course files and submission status.

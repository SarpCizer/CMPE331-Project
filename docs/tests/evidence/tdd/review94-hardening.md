# Instructor-review correction evidence

Task: review of #67 and #16. Sarp Çizer with Codex assistance; no teammate or
instructor approval is asserted.

## Report tooling

The absent-directory fix already exists on the main baseline through #66.
This correction preserves it and adds default/missing-parent, UTF-8, immutable
browser inventory, version-qualified performance and Windows raw-byte regressions.
The initial test commit is `f12f1eb`; implementation is `2fb0306`.
The real Windows checkout initially failed SHA-256 evidence validation because
line-ending conversion altered retained JSON/XML bytes. Attributes now preserve
those exact bytes. No historical measurement was rewritten or relabelled.

`completion.spec.js` exists at both reviewed report head
`2d53035de40caf4ae472ce033a5f9977295e0d19` and tested application source
`a59556e366ffd65adf799bb8aa9bc47e95dea16e`, with the same Git blob.
The report retains immutable file links and recorded JUnit suite counts.

## Login windows and meaningful Sonar conditions

RED `1f4984c` adds five sign-in cases and empty/incomplete/unevaluated Sonar-gate
regressions before changing the implementation. The login cases returned 401 or
200 where the new test expected 429; empty conditions were previously accepted.
GREEN `93a28c9` implements reservation before password work and rejects absent
or unevaluated gate conditions. The original 26 account/login cases and eleven
quality-gate regressions passed locally. Two later tests additionally check
parallel reservations and rotating-account/memory-cap expiry; all seven login
tests pass. No retrospective TDD claim is made for older teammate code.

The first real follow-up CI run
[45892798683](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45892798683)
at `45a6b0d8481b8524e3d61add59647aaaef483e6f` passed backend/browser/load,
archive, container, coverage and secret checks, but failed the newly introduced
ZAP setup and Sonar configuration. It is **not** a passing overall run.
The retained `review94-initial-zap` evidence shows that scanning did not start
before its output directory was created inside the disposable container.

Sonar returned HTTP 400 while creating conditions. Its official condition
validator excludes the direct `security_hotspots` metric. The corrected policy
uses five real server conditions and separately enforces the unchanged zero
hotspot requirement from the exported metric. It does not weaken security policy
or reinterpret the historical empty-condition `OK` as a threshold evaluation.

Later measured evidence retains its own full source SHA and run ID. Report
guard fixtures are explicitly synthetic temporary unit-test data, not measured
CI, security, dashboard or performance results.

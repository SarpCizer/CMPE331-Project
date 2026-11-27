# Final recipe generation verification

Refs #16, #40, #67, #94. Prepared with Codex assistance for Berfin's explicit
request on 27 November 2026. Independent review, green CI and observed deployment
are release conditions; this document does not itself assert they occurred.

## Behavior and correctness

The existing Cloudflare 70B model, JSON schema, ingredient measurement rules,
whole-batch validation, owner-scoped transaction and 28-second deadline remain.
For a normal request with at least six fridge entries, two complementary groups
of three run concurrently. **The target remains six complete suggestions**, not
three. Both calls receive every ingredient, known quantity, dietary preference,
allergen exclusion and selected mood. Alternating priorities encourage different
main ingredients, including recently added food. They are JSON food data, never
system instructions. Restrictions take priority over ingredient coverage.
Small pantries still request six through one call; a requested weekly dish still
uses one call with its exact requested portion count. OpenAI's existing port is
unchanged. Exact duplicate recipe content is removed; different preparations
with the same title are retained. AI may return fewer distinct valid dishes than
requested; the application never pads the list with invented or incomplete food.

A failed request cancels its sibling. The service deadline cancels both. An
invalid group, excluded allergen or invalid measurement rejects the complete
request before any recipe insertion. Generation never changes fridge stock.
This preserves validation; it is not a guarantee that AI food advice, calories,
allergen safety or every cooking instruction is independently verified. The UI
continues to label time/calories as estimates and cooking quantities are reviewed
before stock deduction.

Two calls repeat input tokens and consume more of the existing free AI allowance.
No model downgrade, paid plan, billing change or automatic paid fallback is used.
The 28-second limit is not increased. Real speed depends on provider load and
must be measured after the approved source is deployed. Mock concurrency alone
is not evidence of a live speed improvement.

## Test-first evidence and final checks

The first two new tests failed against main
`6bb06ba441aeed1e27a2a421e09756507ca8598f`: **2 failed in 0.75 seconds**.
The overlap barrier timed out with serial generation; complementary group data
was absent. The red commit is `27d330d2b6471b362b8ab55c2bd549b7184a39cf`.
Implementation is retained separately as `f96863ce5ae4d79c202487ac6af4e4377a1f7708`. The following local application/test sources are byte-identical to that commit.

Local execution on the implementation working tree: **600 backend tests passed,
393 PostgreSQL variants skipped** because no TEST_DATABASE_URL was supplied.
The CI job executes those variants against PostgreSQL 17; local skips are not
counted as passes. White-box coverage from that local run: **93.60% statements,
84.21% branches** (1712/1829 statements; 352/418 branches). Provider: 94.01%
statements / 87.50% branches; login throttle: 100% / 100%. The report explains
remaining branch gaps below; there is no claim of complete path coverage.

The targeted seeded mutation experiment has a passing **77-test baseline** and
**14/14 killed mutants**, zero survivors, invalid mutants or timeouts. Changes
include disabled parallelism, lost group diversity/deduplication, wrong units,
ignored quantities, acceptance of zero amounts, empty-fridge/provider calls,
ignored allergen/time limits and weakened login limits/expiry/reset. Mutants run
in isolated temporary source copies; an import-origin check prevents accidentally
testing the original checkout. This **100% score applies only to these 14 seeded
faults**, not the whole project or all possible mutations. It uses controlled
providers, never production credentials or real AI calls.

Reproduce the source-pinned campaign:

```sh
python scripts/quality/mutation.py --revision "$(git rev-parse HEAD)" --output test-results/mutation.json
```

The integrated workflow uploads `mutation-evidence-<source SHA>` alongside its
existing coverage, PostgreSQL/container, HTTP acceptance, browser, load, ZAP,
SonarQube, secret and dependency scan artifacts. Final immutable run IDs, measured
live latency, recipe counts and deployment source must be recorded on the PR and
#40 after execution. Historical measurements must not be relabelled as this run.
**32 functional acceptance, 12 real HTTP isolation, 51 browser and 20 report/export/traceability regression tests passed locally**, and the production frontend build passed. The browser run used an isolated SQLite host with a controlled provider. Black-box validation covers observable HTTP/user behavior; provider mocks are
identified separately from the bounded actual-cloud verification.

## Yeşim's #67 feedback: item-by-item reconciliation

1. **Review provenance:** #67's earlier unreviewed merge remains a historical
   fact. #94 was independently reviewed before merge. This follow-up also needs
   an independent teammate's approval on its final head; passing tests alone do
   not supply approval.
2. **Rebuild, file inventory, source identity:** the missing-output-directory fix
   and clean-export regression remain in `scripts/tests/export_report.py` and
   `scripts/tests/test_export_report.py`. Immutable inventories retained by #94
   establish the referenced `completion.spec.js` exists at the cited sources.
   `review-follow-up.json` identifies the follow-up measured source, local/CI
   revisions and evidence index. Neither an older local run nor the course ZIP
   is silently presented as final-source testing.
3. **Interpret performance and coverage:** the historical report explains
   371.47/44.35 = 8.38x, 128.53 ms headroom to 500 ms, and the confounded source,
   OS, CPU and database differences. It does not invent one causal explanation.
   It retains the later Windows non-AI failure (1772.75 ms) alongside the CI pass
   (144.05 ms). Line execution does not imply both outcomes of a branch were
   tested: provider error/configuration alternatives and database-specific paths
   account for remaining gaps; current local PostgreSQL skips are explicit.
   The final CI coverage JSON identifies each missing line/branch so the final
   source can be assessed separately from the older 92%/73% figures.
4. **Detailed traceability:** 48 AC rows and nine NFR rows have immutable
   assertion references in `docs/tests/coverage/traceability.*`; duplicate test
   identifiers are distinguished from 32 executions of 28 physical acceptance
   IDs. `criterion_assertions.py` and regression tests verify references.
5. **Security and generation load:** the workflow retains authenticated standard
   OWASP ZAP testing, the four custom probes, concurrent login brute-force tests,
   the 10-user controlled generation load and five simultaneous 28-second
   deadline cases. These run on disposable hosts, not live customer data.
   Controlled provider timing is not a real AI capacity measurement.
6. **Real Sonar gate / false positives:** `scripts/quality/sonarqube.py` configures
   and exports five server conditions (zero bugs, vulnerabilities, BLOCKER and
   CRITICAL findings; coverage >=90%) and a separate zero-hotspot policy. The
   twelve historical helper-related S2970 BLOCKERs are explicitly labelled false
   positives, not twelve security fixes. The retained MAJOR S8786 bounded-regex
   finding is not relabelled as a false positive.
7. **Results figures:** the rebuilt 14-page report contains the actual Sonar
   dashboard and coverage/non-AI/generation performance figures, linked to the
   immutable evidence bundle `docs/tests/evidence/review94-fafd3fd`. New CI again
   captures its actual source-pinned Sonar dashboard and raw results. Older
   figures remain labelled with their measured source.

Remaining historical limitations are explicit: two low/five total ZAP alerts
(no high/medium), one investigated-but-not-isolated preferences 503 in that scan,
one bounded-regex MAJOR Sonar finding, and the process-local login throttle's
single-worker scope. The final CI may change these findings; use its actual
exports rather than assuming zero findings. The frozen course package is not
replaced and no course-platform submission or instructor acceptance is claimed.

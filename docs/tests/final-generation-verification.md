# Final recipe generation verification

Refs #16, #40, #67, #94. Prepared with Codex assistance for Berfin's explicit
request on 27 November 2026. Independent review, green CI and observed deployment
are release conditions; this document does not itself assert they occurred.

## Behavior and correctness

The existing Cloudflare 70B model, JSON schema, ingredient measurement rules,
whole-batch validation, owner-scoped transaction and 28-second deadline remain.
Normal generation has **no numeric recipe target or recipe-count cap**. It asks
for as many useful, complete, distinct dishes as the available variety supports.
It never pads the list with unsuitable suggestions. For a pantry of at least six
entries, complementary requests run concurrently; one group per roughly four
pantry entries, up to four concurrent provider calls. This bounds request
fan-out, not the number of returned recipes. Both older and newly added items
receive priority attention. All calls receive the full pantry, known amounts,
dietary preferences, allergens and selected mood as JSON data. Restrictions take
priority over ingredient coverage. Small pantries use one call without a numeric
recipe target. A requested weekly dish still uses one call with its exact portion
count. OpenAI's existing port retains its contract and now also receives the
count-free variety instructions. Exact duplicate content is removed; different
preparations with the same title remain. Every returned valid recipe is retained,
including batches larger than six. AI responses and free-tier token/time limits
are finite; this is not a promise to enumerate every theoretically possible dish.

A failed request cancels sibling requests. The service deadline cancels all requests. An
invalid group, excluded allergen or invalid measurement rejects the complete
request before any recipe insertion. Generation never changes fridge stock.
This preserves validation; it is not a guarantee that AI food advice, calories,
allergen safety or every cooking instruction is independently verified. The UI
continues to label time/calories as estimates and cooking quantities are reviewed
before stock deduction.

Concurrent calls repeat input tokens and consume more of the existing free AI allowance.
No model downgrade, paid plan, billing change or automatic paid fallback is used.
The 28-second limit is not increased. Real speed depends on provider load and
must be measured after the approved source is deployed. Mock concurrency alone
is not evidence of a live speed improvement.

## Test-first evidence and final checks

The first two new tests failed against main
`6bb06ba441aeed1e27a2a421e09756507ca8598f`: **2 failed in 0.75 seconds**.
The overlap barrier timed out with serial generation; complementary group data
was absent. The red commit is `27d330d2b6471b362b8ab55c2bd549b7184a39cf`.
The user subsequently requested removal of the numeric target. A new test failed
against `9cb54bc88130f5454af48c5e53ca535da037d4cd` (1 failed in 0.18 seconds),
retained in `5bcfdbbd41d960c786cff721c916b74cf9778347`. It requires pantry-driven
fan-out, count-free instructions and retention of 16 distinct returned recipes.
The earlier implementation was `f96863ce5ae4d79c202487ac6af4e4377a1f7708`;
its results are a preceding checkpoint, not final-source measurements.

At that preceding checkpoint: 600 local backend passes, 393 PostgreSQL variants
skipped; 93.60% statement / 84.21% branch coverage; 32 acceptance, 12 HTTP,
51 browser and 20 report regressions passed, and frontend build passed. No UI,
HTTP contract, database schema or report-export code changed after these checks.
Final-head PostgreSQL, application coverage, acceptance/browser, security/load and
mutation results are published by CI on the PR. Local PostgreSQL skips are not
counted as passes. Controlled provider results are distinct from actual cloud
checks. There is no claim of complete path coverage.

The targeted seeded mutation campaign uses a passing baseline and 14 isolated
source faults: disabled parallelism, lost group diversity/deduplication, wrong
units, ignored quantities, acceptance of zero amounts, empty-fridge calls,
ignored allergen/time limits and weakened login limits/expiry/reset. Each mutant
runs in a temporary source copy with an import-origin check. Its score applies
only to these selected faults, not all project code or every possible mutation.
No production credentials or real provider calls are used in this campaign.

```sh
python scripts/quality/mutation.py --revision "$(git rev-parse HEAD)" --output test-results/mutation.json
```

The integrated workflow uploads `mutation-evidence-<source SHA>` alongside
coverage, PostgreSQL/container, HTTP acceptance, browser, load, ZAP, SonarQube,
secret and dependency artifacts. Final immutable run IDs, current coverage,
mutation counts, measured live latency, recipe counts and exact deployment source
are recorded on the PR and #40 after execution. Historical measurements must not
be relabelled as final-source testing. Mock concurrency alone is not evidence of
a live speed improvement.

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

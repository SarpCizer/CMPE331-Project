# AI contribution traceability

Refs #16, #46. Codex assisted Berfin with the following actual changes. GitHub commit authorship identifies the responsible account; the table discloses assistant involvement rather than attributing generated work to another teammate.

| Contribution | PR / source | Validation |
| --- | --- | --- |
| Accounts, signed sessions, owned inventory/preferences and migration | #9, eebacdf | Actual SQL/JWT tests, then integrated checks |
| Compose Sarp's collections and Ayse's recipe ports without replacing their work | #10, 366f603 | 27 acceptance cases through real FastAPI/SQL |
| React UI and server-backed state | #11, 9f43e3a | Browser account switching, reload, layouts, keyboard and accessibility |
| PostgreSQL, CI, load, security and Sonar workflow | #12, 94c00cf | Recorded Actions runs and exported artifacts |
| Fix reported email/form findings and assertion-helper detection | #13, 03c8ffe | Follow-up Sonar scan reports zero issues |
| Self-host Swagger, package a production image and cloud Blueprint | #14, eb3baf9 | 103 CI Python cases, 8 browser cases, production-image restart and PostgreSQL smoke |
| Four scoped penetration probes | #15, 36f4f59 | CI run 44804663349 succeeds |
| Lossless relational preference migration | #49, red 9450fac then green 775e8b7 | Recorded failure before implementation; migration, fidelity, isolation and concurrent-registration tests |
| Finish frontend validation, independent collection loading and recipe modal feedback | Existing #56; test-first commit 2b2797f | Nine new browser regressions failed against a7c7456 before implementation; one further committed-write refresh regression added during review. Current run evidence is recorded in docs/tests/frontend-completion.md. |
| Preserve exact preference strings in the browser and read paired lists in one SQL snapshot | Existing #56; browser RED20eb89a/GREEN263ce66 and storage REDa9fe492/GREEN2c04ce0 | Full checkpoint273a983 passes113 PostgreSQL/backend and20 browser cases; actual source/run identities are linked from docs/tests/review-16-evidence.md. |
| Reproduce and correct the recipe-to-shopping ingredient-domain mismatch | Existing #56; #63, RED6d704c1 followed by its correction | The real authenticated/migrated SQLite host fails eight mixed-batch cases before correction; the corrected local backend passes121 with12 explicit PostgreSQL skips, plus27 acceptance cases. The attached CI run exercises PostgreSQL separately. Sanitized evidence: docs/tests/evidence/ingredient-contract/tdd.json. |

The assistant used the PDF skill to prepare and visually inspect the test report and the Render deploy skill for infrastructure preparation. Browser verification uses the actual application, with an isolated external-provider fixture. The team must independently review the diff, confirm decisions and complete live-provider/cloud checks; those actions are not claimed here. Each other member should add their own verified tool usage and incidents, rather than Berfin inventing their contribution history.

## Mustafa Safa Bayrak

| Contribution | PR / source | Validation |
| --- | --- | --- |
| Reviewed the frontend and delivery PRs as the frontend owner. Claude helped summarize the diffs and draft the review wording. | #56, #11, #59 | I checked each finding against the code before submitting, e.g. the US-06 traceability row in #59 and the "1 ingredients" text in the recipes page. |
| Moved the frontend API client from `fetch` to Axios with a token interceptor, as listed in #35 and the charter. Claude helped write the client. | `feature/safa-frontend-charter` | Compared the old and new client on 11 cases (token header, 204, malformed body, 400/401/409, redirect, cancellation, network failure); production build passed. |
| Split the single-file frontend into pages/components and added React Router with protected routes (#35). Claude helped move the existing code into separate files. | 2d3f9f3 | The code was moved rather than rewritten; 18/18 browser tests passed before and after. |
| Migrated the frontend styling from plain CSS to Tailwind CSS (#35, charter). Claude helped translate the stylesheet rules into Tailwind classes. | 5e87d9f | 18/18 browser tests; 140 screenshots at five widths compared pixel by pixel with the previous UI (only anti-aliasing noise of at most 2/255 at rounded corners); coverage 96.65% lines. |
| Fixed the "1 ingredients" text and locale-dependent history dates test-first. Claude helped write the regression tests. | red 0a9584a, green fef3a7c | Both new browser tests failed before the fix and pass after it; full suite 20/20; logs in `docs/tests/evidence/text-format/`. |

## İrem Demircan

| Contribution | PR / source | Validation |
| --- | --- | --- |
| Claude helped draft the backlog issues, as reported by İrem. | #17–#48, linked from #16 | Codex cross-checked issue metadata, dependencies and open PRs. The backlog snapshot was superseded by the current integration stack. |
| Codex helped identify and cover inventory regression gaps. | #58, 6c2aa58 | 27 baseline functional tests and 28 after the coverage change; 23 account/database and host integration tests passed locally with an isolated provider. |
| Codex reproduced archive defects and prepared review feedback for the final deliverable. | #53 | A harmless untracked file reached the archive, and two identical-input builds yielded distinct ZIP bytes. Corrective review feedback is recorded on the PR. |
| Codex helped reproduce and address the archive checksum path and clean-checkout report export findings. | #66, red `282afeb` and green `39b7b54` | The archive regression passed after the fix, and both default and nested export paths produced a report. The PR is under review for integration into main. |

## Ayşe Döne

Codex helped compare the recipe and shopping contracts, replay the ingredient validation regression, and implement and test the Cloudflare Workers AI adapter. The source revisions, results, and live verification status are recorded in the [recipe integration review](ai-contributions/ayse-recipe-review.md). Refs #45, #63, #65.


## Sarp Çizer

Sarp's [published contribution and incident record](../backend/docs/ai-traceability.md) documents Codex assistance with the collections implementation and the owner-scoped history correction. The regression commit is `fc2a560`, followed by `63dcd7a`. The record reached main in #57.

### Final verification follow-up, 28 November 2026

Under Sarp's explicit finalization instruction, Codex continued from Berfin's
merged PR #102 without repeating those changes. PR #103 retains a genuine
RED/GREEN fix for sign-in rehash undoing a concurrent password rotation, adds
tested public deployed-source metadata, and prepares the syllabus/instructor
test-report edition from current source-pinned CI artifacts. The raw RED/GREEN
provenance, 27-mutant campaign, current inventories, failed historical benchmark
and real Sonar/ZAP results remain inspectable. Review, merge, live verification
and Learn submission are distinct states; no human approval or grade is invented.

## Kerem Sönmez

The [merged #71 description](https://github.com/SarpCizer/CMPE331-Project/pull/71) discloses Codex assistance with Kerem's original deployment documentation at `62894a6`. It records Berfin's subsequent verification and follow-up separately.

## Kerem Sönmez — QA follow-up, 25 November 2026

Codex inspected Kerem's assigned issues and the merged evidence, reproduced the
Sonar exporter returning success on a failed gate, added regressions before its
fix, and expanded authorization/credential tests across every protected method
on both API prefixes and SQLite/PostgreSQL. It also corrected stale QA status
documents and prepared [the QA handoff](tests/kerem-qa-handoff.md). Refs #16,
#22, #23, #41–#44; branch `ci/kerem-qa-completion`.

Validation records distinguish the local SQLite passes and explicit PostgreSQL
skips from exact-head CI. The original report author and peer approvals are
preserved. Codex initially let a missing policy-output read obscure the desired
RED assertion; the test was corrected and rerun before changing the exporter.
No teammate approval, owner setting or course upload is attributed to the tool.


## 2026-11-28: recipe transport resilience after observed live 503

Codex assisted Berfin on `fix/recipe-generation-resilience`, continuing from
main abdca3f and integrating Sarp's separately reviewed PR103 source for testing.
The actual normal live run returned503/28.30s; Quick returned18 recipes/20.54s.
Five new failures and one passing total-outage guard were recorded before the
implementation in 6e1fe608. The fix retains completed whole candidate groups,
bounds transport retries and signals incomplete searches explicitly. Full
pantry/amounts/exclusions, no fixed recipe count, quality/atomic hard-error
validation, 28-second outer deadline and the free provider/model are preserved.

Initial isolated runs:698 backend passes/403 PostgreSQL variants skipped locally,
57 browser passes and29 selected mutants killed. These measurements precede
integration of PR103's password race fix and are not relabelled as final CI.
The combined campaign adds Sarp's password-race mutant for30 selected mutants.
Final CI, legitimate independent reviews, actual main/deploy source and real
provider checks remain required. Automated approval review rejected assistant
approval/merge of PR103 under general merge authorization; no workaround or
protection change was attempted. No school upload or final reliability is claimed.

After Berfin explicitly requested the assistant review and approval on her behalf,
the transparent Codex-assisted review6099376504 was accepted for Sarp's unchanged
be5dd3b PR103. Normal expected-head merge produced f3a6246; no protection setting
changed. The combined working source then passed702 backend cases locally, with
405 PostgreSQL variants explicitly skipped, and all30 targeted mutants were killed
(zero survivor/invalid/timeout). This does not substitute for final-source CI or
actual provider measurements.

Final UI review found incomplete-search metadata survived in shared results while
its duplicate page-local notice state reset after navigation. Both viewport cases
failed against37055e4, retained in red847faa6b. Deriving the notice from shared
results fixes the mismatch without changing provider budgets/counts. Final44
focused backend cases and both browser cases passed; full CI is rerun for this
new exact source, rather than relabelling earlier runs.

A final provider-envelope sweep reproduced200/success:false erasing a healthy
group in red8ee70dd7 against90ee26b. A typed upstream-unavailable result now
marks only that group unavailable without retrying opaque upstream errors or
exposing their private message. All45 focused backend regressions pass. This
checkpoint is separately source-qualified; final CI/review/live gates remain.

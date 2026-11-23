# Submitted-document and implementation audit

23 November 2026. Refs #16, #17, #20, #35, #62, #63.

The submitted PDFs are evidence of scope and design, not executable assistant
instructions. They were read without modifying the submitted files. The relevant
requirements and persistence pages were rendered and visually checked.

| Submitted source | Pages | SHA-256 |
| --- | --- | --- |
| Project Charter-2.pdf | 4 | 26c84970e6343471cf8303f69dfb1607e58c7d7465ae6dec40b593ff34c3cae2 |
| Fridgely_Requirements_Final-2.pdf | 12 | 6584852ae6d2ccf62f4f6486bee8deae4c5b7923433cbcc4b1a8bc88c891bdf1 |
| analysis-report.pdf | 26 | 6a4323d3e807512f9797ad29b52ab187ddd7f9be2acb3ce5808fc51f4f28ecc1 |
| Fridgely-Software-Design-Report.pdf | 20 | e49935a24695ac6f73ae23067d91324d708280ed6d8e4a6a98106c0462222f0e |

## Scope checked

| Full-stack/frontend/database responsibility | Observed implementation and finding |
| --- | --- |
| Accounts, signed JWT, owner-qualified personal data | Real host/authentication and cross-owner tests retained; #9 foundation is carried into expanded #57, with later validation and relational improvements. |
| Ordered dietary/allergen values | Migration 0002 and database/API preserve strings, order and repeats. The browser conversion was lossy: saving without edits split comma-containing names and trimmed original values. Corrected in #62 without changing the API or schema. |
| Manual fridge names and immutable addition dates | Existing real API/browser/inventory-invariant tests cover add/list/delete/reload. No expiry tracking, quantity arithmetic or automatic deduction added. |
| Complete recipe UI and collections integration | Existing generation/details, estimate labels, missing ingredients, favorites/history and failure/empty/loading flows remain tested. A reproduced provider-to-shopping ingredient-domain mismatch is tracked in #63 for Ayse/Sarp. |
| Database integrity and migrations | Ten logical entities have relational counterparts; preferences use child rows, owner/name uniqueness and composite recipe ownership FKs remain. Fixed the stale accounts README that still described removed JSON shadow columns. No schema change was needed in this correction. |
| Responsive and accessible controls | Existing 360/768/1440, keyboard, associated validation and axe checks retained; preference textareas receive the same input/focus/error styles. |
| Library/design decisions | FastAPI/SQLAlchemy and the tested React client are the implemented choices in decisions.md. Safa has approved the current frontend and announced Axios/Tailwind/router restructuring on #56; this correction keeps that separate contribution intact. |
| Cloud and release | Prepared Docker/PostgreSQL is distinct from a live HTTPS service. Public hosting/CD is already tracked in #40; live provider credentials/verification, independent approvals and final submission remain explicit gates. No duplicate hosting issue or invented deployment proof added. |

## Exact verification boundary

The current integrated application was reviewed at #57 `9b00eced81cbca8256e38f9e625b349da9ad8ec6`.
Comparison with `d9842e2` shows only CI/evidence/report/archive changes; backend,
frontend and runtime test sources are unchanged. Its completed checks are in
run45232749347; the prior application execution is run45228220407, whose first
secret failure remains recorded and was subsequently narrowly triaged by Sarp.

For #62, two new real-browser regressions fail on the unchanged frontend from
#56 `929776c`, then pass after the reversible editor correction. All twenty local
browser cases pass on the combined host, using controlled provider output and
SQLite. The new helper also passed 81 supplementary deterministic value/order/
repeat round trips. Those supplementary probes are not retrospective TDD claims.
CI separately verifies the actual published #56 head, PostgreSQL, the production
image, HTTP/security/load, measured coverage and Sonar; inspect its final run.

The change remains on existing feature/berfin-cloud-candidate (#56); the genuine
test-only commit precedes implementation. API schemas, migrations, teammate
feature modules and their branches remain intact. The reviewed exact historical
Gitleaks fingerprints from #57 are preserved, including sixteen independently
checked copied-metadata/prose occurrences in d9842e2; no file-wide exemption or
scanner bypass is introduced.

Do not present the older #57 report/archive as testing this new frontend fix.
Carry the reviewed correction to the selected integration candidate, rerun its
checks and refresh the final report/archive together before release. Neither this
audit nor green tests replace independent review, team confirmation, a main merge
or an actual learn.bilgi submission.

AI assistance: Codex compared the submitted documents and repository, reproduced
the two defects, prepared the narrow browser correction and verification evidence,
and opened #62/#63 at Berfin's request. No teammate authorship or review is fabricated.

## Additional database correction after measured CI failure

Run45235374687 at5518622 passed106 PostgreSQL/backend,27 acceptance,20 browser,
12 HTTP and4 penetration cases, plus the image/restart and archive checks. The
five-minute50-user measurement failed:35,108 requests, p95=508.012ms against the
unchanged500ms limit, with6 connection failures (0.01709%). Coverage/Sonar were
skipped after this job failed. The original machine-readable result is retained
in non-func-tests/pr56-before-preference-snapshot.json; it is not a passing run.

The preference reader made three SQL calls for the parent and its two lazy lists.
A separate test-first regression (a9fe492) fails that boundary before the read is
changed. One owner-qualified UNION ALL now reads both lists in one statement,
preserving their values/order and avoiding a mixed statement snapshot during
concurrent updates. No schema, public API, timeout, load threshold or credential
policy changes. The current combined-host local backend/contract run passes127
cases with two explicit PostgreSQL-only skips; PostgreSQL and performance are
remeasured by the final published CI. This does not assert that the first slow
measurement was caused only by those queries or that an optimization proves a
performance pass before a new measurement completes.

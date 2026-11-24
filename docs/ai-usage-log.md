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

The assistant used the PDF skill to prepare and visually inspect the test report and the Render deploy skill for infrastructure preparation. Browser verification uses the actual application, with an isolated external-provider fixture. The team must independently review the diff, confirm decisions and complete live-provider/cloud checks; those actions are not claimed here. Each other member should add their own verified tool usage and incidents, rather than Berfin inventing their contribution history.

## Mustafa Safa Bayrak

| Contribution | PR / source | Validation |
| --- | --- | --- |
| Reviewed the frontend and delivery PRs as the frontend owner. Claude helped summarize the diffs and draft the review wording. | #56, #11, #59 | I checked each finding against the code before submitting, e.g. the US-06 traceability row in #59 and the "1 ingredients" text in the recipes page. |
| Moved the frontend API client from `fetch` to Axios with a token interceptor, as listed in #35 and the charter. Claude helped write the client. | `feature/safa-frontend-charter` | Compared the old and new client on 11 cases (token header, 204, malformed body, 400/401/409, redirect, cancellation, network failure); production build passed. |
| Split the single-file frontend into pages/components and added React Router with protected routes (#35). Claude helped move the existing code into separate files. | 2d3f9f3 | The code was moved rather than rewritten; 18/18 browser tests passed before and after. |
| Migrated the frontend styling from plain CSS to Tailwind CSS (#35, charter). Claude helped translate the stylesheet rules into Tailwind classes. | 5e87d9f | 18/18 browser tests; 140 screenshots at five widths compared pixel by pixel with the previous UI (only anti-aliasing noise of at most 2/255 at rounded corners); coverage 96.65% lines. |
| Fixed the "1 ingredients" text and locale-dependent history dates test-first. Claude helped write the regression tests. | red 0a9584a, green fef3a7c | Both new browser tests failed before the fix and pass after it; full suite 20/20; logs in `docs/tests/evidence/text-format/`. |

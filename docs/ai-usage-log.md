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

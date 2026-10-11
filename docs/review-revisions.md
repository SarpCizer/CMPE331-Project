# Requirements review revisions

Revision date: 11 October 2026. This note records implementation of the requested changes; it does not assert reviewer approval.

| Review point | Revision | Verification |
|---|---|---|
| [PERT network](https://github.com/SarpCizer/CMPE331-Project/pull/4#discussion_r4237695216) | Separate parallel WBS 3.2-3.6 features, shared TDD activities Q0/Q1/J, design-report finalization K and review L; compute ES/EF/LS/LF/slack | Shared activity data and forward/backward pass; 54-day critical path and positive slack; matching WBS/Gantt/report figures |
| [Acceptance criteria](https://github.com/SarpCizer/CMPE331-Project/pull/4#discussion_r4237697259) | Every one of the 48 functional criteria uses explicit Given/When/Then | Dedicated story criteria and report criteria match exactly |
| [Use-case diagram](https://github.com/SarpCizer/CMPE331-Project/pull/4#discussion_r4237698099) | Add system boundary, visitor, signed-in user, AI supporting actor, generation-failure extension and US-15 access constraint | PlantUML source and equivalent locally rendered PNG embedded in report/PDF |
| [Minor test issues](https://github.com/SarpCizer/CMPE331-Project/pull/4#pullrequestreview-5479029713) | Assert setup/read status; detach snapshots; use returned recipe IDs; isolate invalid fields; replace fake expiry with a real issued-token expiry scenario | 27 executable acceptance cases, all still intentionally failing against 501 scaffold; no skipped cases |

The reviewer did not identify individual test defects; the listed test changes are issues found during the follow-up audit. Database atomicity, cryptographic signature verification, browser checks and non-functional results remain pending implementation. Reviewer confirmation and approval are still required before final PDF submission.

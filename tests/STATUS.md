# Requirements test status

Updated 25 November 2026. All **28 functional acceptance cases pass** locally
through the real FastAPI/SQL host and a controlled recipe provider, on the QA
branch based on main `ebd8a5a`. The 15 stories and 48 criteria are mapped in
[the criterion CSV](../docs/tests/coverage/traceability.csv).

The original 11 October result (27 failures from the 501 application boundary)
is historical RED evidence. It is not the current application status and does
not establish tests-first development for every later feature.

[The source-matched report](../docs/tests/software-test-report.md) records
application `a59556e`, CI 45474025963, its measured coverage, browser/security/load
results and genuine TDD sequences. Report PR #67 was independently approved and
merged into main on 25 November at `da81cc3`; its approved PDF bytes are preserved.

[Kerem's QA handoff](../docs/tests/kerem-qa-handoff.md) separates the new security
and Sonar gate checks, historical source evidence, live deployment, remaining
owner settings and course submission. Local PostgreSQL skips are not passes.

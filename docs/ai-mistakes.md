# Observed AI-assisted implementation incidents

Refs #16, #46. These are observed defects or workflow failures, with bounded impact and evidence. They are not invented production incidents or claims of independent human review.

| Incident | Detection / impact | Correction and evidence |
| --- | --- | --- |
| Generated email validation used a potentially expensive regex | Sonar `python:S8786`, medium reliability concern. This was an avoidable validation design issue; no successful real-world exploit is claimed. | Replace with email-validator and regression inputs in #13; `03c8ffe` scan has zero issues. Initial findings and follow-up are preserved in docs/tests/quality. |
| Scanner work directory assumed writable container defaults | CI scan failed before analysis; this would have made a quality claim unsupported. | Set a writable project-local scanner directory in 62576a5; later export fix 94c00cf; preserve failure history separately from actual findings. |
| Broad provider tests alone could be misread as live AI evidence | Test fixtures validate boundary behavior but do not prove provider credentials, current live outputs or cloud availability. | Production contains no fixture mode; reports identify the provider boundary, exact environment and remaining live checks. |
| Coverage could be mislabeled by using combined line/branch percentage | coverage.py's combined percentage differs from statement/line coverage; treating them as identical would misstate results. | Export separate statements and branches plus raw denominators in the report and coverage notes. |
| The earlier integrated UI coupled all five reads and mutation acknowledgement | Nine browser regressions at 2b2797f exposed missing field associations, modal feedback and collection isolation. A favorites outage could hide successfully read inventory or make a committed write appear to fail; a fast outage could mask a later 401. | #56 separates collection state and mutation/refresh outcomes, clears any expired session, sanitizes provider errors and places feedback inside the modal. Eighteen browser cases plus four supplementary walkthroughs pass; RED/GREEN evidence is in docs/tests/frontend-completion.md. |

Four implicit form-submit types were also corrected by #13. Twelve blocker-level Sonar findings were caused by Jest detection of a custom helper named `expect`; the helper already asserted correctly. Rename it `assertResponse`, retain all assertions and execute the suite. This was a tool classification issue and is not presented as twelve application vulnerabilities.

Human team members should add any serious mistakes they personally caught, with the faulty revision, reproduction, impact and verified fix. No unobserved human-caught severe defect or peer approval is claimed by this log.

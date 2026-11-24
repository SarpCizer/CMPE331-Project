# Integrated test plan and exit criteria

Refs #16, #39, #41-#44. Test the actual FastAPI/SQLAlchemy application and built React client against the 15 approved user stories, 48 acceptance criteria and nine NFRs. PostgreSQL is the integration target; SQLite is an additional isolated local environment. Provider outputs and clocks are controlled only where the scenario requires them. Public-cloud and live-provider checks remain distinct release activities.

| Layer / responsibility | Cases and exit criterion | Evidence |
| --- | --- | --- |
| Full-stack/database | Registration, salted hashes, token claims/expiry, owned inventory/preferences, constraints and old-data migration; no failures in the recorded run | Python JUnit, coverage, TDD sequence |
| Recipe/collections integration | Real account/fridge/preferences passed through teammate ports; whole batches and committed history; no mutation on failure | Backend integration and 27 acceptance cases |
| HTTP security | Every protected method without/malformed credentials, forged tokens and foreign IDs; denied requests preserve state | 12 HTTP cases and JWT unit cases |
| Frontend | Registration/sign-in/preferences; exact preference strings/order/repeats; inventory, recipe details, shopping, favorites/history, reload and account switching | 20 actual-browser cases at verified checkpoint273a983, screenshots; see current PR run for later sources |
| Accessibility/responsiveness | 360/768/1440 px, no horizontal overflow; labelled controls, WCAG A/AA automation, keyboard core flows | Browser results and embedded figures |
| Penetration | SQL payload stays literal, owner mass assignment rejected, file disclosure denied, stored XSS inert | Four scoped probes and limitations |
| Persistence | Two processes and two users/five collections; production container restart retains SQL data and signed sessions | SQLite/PostgreSQL process cases and container JSON |
| Performance | 50 signed-in users, 100 inventory entries each, 300 measured seconds, one-second think time, four non-AI read routes; p95 <=500 ms and errors <1% overall and per route | Raw local/CI measurements; never a production SLA |
| Provider deadline | Real host's default 28-second timeout returns within 30 seconds, cancels stalled fixture and preserves five collections | Observed elapsed-time JSON |
| Quality / CI | No unreviewed high-impact Sonar findings; explicit coverage floors; audits, full-history secret scan and failure canaries | JSON exports, mitigation register and actual job status |

Use disposable accounts/databases and never run load or attack probes against the team's shared production data. The full command list is in README.md and docs/tests/README.md. Preserve raw failed runs and classify causes before rerunning; do not replace a failed measurement with a planned result.

Exit from technical verification requires successful relevant tests, traceability for every criterion, measured code coverage, reviewed findings and a reproducible source revision. Release additionally requires independent PR approval, owner settings, actual HTTPS deployment/database smoke, live-provider validation and agreed deployment performance. Course submission and each member's contribution/rehearsal are observed human actions, not outcomes inferred from CI.

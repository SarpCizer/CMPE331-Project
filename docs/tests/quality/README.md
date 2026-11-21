# Quality evidence and mitigation register

The JSON files are exports from an actual SonarQube server executed in GitHub Actions, not an unexecuted configuration or estimated findings. The CI server is ephemeral and loopback-only. `before-fixes/` records revision `94c00cf`; `after-fixes/` records revision `03c8ffe` from [PR #13](https://github.com/SarpCizer/CMPE331-Project/pull/13), [run 44798645271](https://github.com/SarpCizer/CMPE331-Project/actions/runs/44798645271).

| Rule | Initial count / severity | Mitigation | Verification |
| --- | --- | --- | --- |
| `python:S8786` | 1 MAJOR / medium reliability | Replace the email regex with the maintained email-validator parser; pin its dependencies and cover invalid local-part/domain forms. | 21 account/database regression cases pass; rule absent in completed follow-up scan. |
| `javascript:S9011` | 4 MAJOR / medium reliability | Set `type="submit"` explicitly on all four form submission buttons. | Browser account, inventory, shopping and preferences flows pass; rule absent in follow-up scan. |
| `javascript:S2970` | 12 BLOCKER / high maintainability | The custom HTTP helper named `expect` already called `assert.equal`. Rename it `assertResponse` to avoid incorrect Jest detection; retain and execute all actual assertions. No rule suppression or test exclusion. | All 12 HTTP tests pass; all twelve blocker findings absent in follow-up scan. |

The completed follow-up reports **0 issues, 0 bugs, 0 code smells, 0 vulnerabilities and 0 security hotspots**, with measured aggregate coverage 92.3%. Its quality gate is `OK`, but the export has an empty `conditions` array for the initial project analysis: `OK` is not proof that a bespoke set of release thresholds was evaluated. The explicit issue totals, impact/severity export and measured tests are therefore preserved alongside the gate.

The earlier CI failures are infrastructure history: the first scanner workspace was not writable, and the next analysis completed but the export request used an unsupported optional metric. The corrected job uses a writable project-local scanner directory and supported metrics. Initial findings are retained rather than erased. `analysis-history.json` links the exact runs and changes.

`current/` records the final relational-database application revision 775e8b7 from
run 44932416317: zero issues/bugs/smells/vulnerabilities/hotspots, aggregate Sonar
coverage 92.1%, and the explicit initial-project gate caveat above. The separate
policy run 44933945505 passes coverage floors and the full-history Gitleaks scan.
Its exports include successful negative coverage and synthetic-secret canaries.
Initial and triage scan matches are retained as redacted JSON; only four exact
historical fingerprints for two verified false-positive patterns/copies are
scoped in .gitleaksignore. No broad source/test directory is excluded.

Dependency audits cover the locked Python packages and pnpm graph. “No known vulnerabilities” is time-bound and does not establish absence of application flaws. `secret-canary-scan.json` checks named synthetic diagnostic strings in the exported successful logs; it is not a generic secret-scanning guarantee. No real passwords, JWTs, database URLs or provider credentials belong in this folder.

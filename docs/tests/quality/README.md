# Quality evidence and mitigation register

## Instructor-review follow-up

The historical zero-issue scans below retain their original revisions. The
follow-up uses evaluated server conditions and a separate zero-hotspot policy;
it does not describe every finding as fixed. The completed source `fafd3fd` analysis and dashboard capture passed in
[run 45899635960](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45899635960).
Its five evaluated server conditions report 96.0% aggregate coverage and zero
bugs, vulnerabilities, BLOCKER and CRITICAL issues; security hotspots are zero.
Earlier dashboard-capture failures remain retained as failed attempts.

That analysis retains one **open MAJOR python:S8786** finding in
`backend/src/fridgely_app/availability.py:16`: the amount regex may backtrack
super-linearly. Public `IngredientAmount` DTO input is capped at 64 characters
in `fridgely_collections/schemas.py`; this bounds normal exposure but does not
make the pattern linear. A linear parser remains follow-up work. This is not
one of the twelve historical S2970 false positives and is not silently suppressed.
Use the final source-qualified evidence bundle for the corrected capture and scan.

## Historical scans

The JSON files are exports from an actual SonarQube server executed in GitHub Actions, not an unexecuted configuration or estimated findings. The CI server is ephemeral and loopback-only. `before-fixes/` records revision `94c00cf`; `after-fixes/` records revision `03c8ffe` from [PR #13](https://github.com/SarpCizer/CMPE331-Project/pull/13), [run 44798645271](https://github.com/SarpCizer/CMPE331-Project/actions/runs/44798645271).

| Rule | Initial count / severity | Mitigation | Verification |
| --- | --- | --- | --- |
| `python:S8786` | 1 MAJOR / medium reliability | Replace the email regex with the maintained email-validator parser; pin its dependencies and cover invalid local-part/domain forms. | 21 account/database regression cases pass; rule absent in completed follow-up scan. |
| `javascript:S9011` | 4 MAJOR / medium reliability | Set `type="submit"` explicitly on all four form submission buttons. | Browser account, inventory, shopping and preferences flows pass; rule absent in follow-up scan. |
| `javascript:S2970` | 12 BLOCKER / high maintainability — **false positives** | The custom HTTP helper named `expect` already called Node's `assert.equal`; the analyzer incorrectly treated it as Jest's matcher API. Renaming it `assertResponse` corrects framework detection while retaining every assertion. This did not fix twelve security defects or add twelve missing assertions. No rule suppression or test exclusion. | All 12 HTTP tests pass; all twelve false-positive findings are absent in the follow-up scan. |
| `javascript:S9383` | 1 MAJOR in frontend-completion revision 522e0db | Mark the internally handled background collection load with explicit `void` in 25c111a. Preserve independent loading and its internal error handling. No runtime rejection incident is inferred from the static finding. | All 18 local browser cases pass after the change; run 44944497368 reports zero issues/bugs/hotspots on exact source 25c111a. Original selected fields and artifact digest: frontend-522-findings.json. |

The completed follow-up reports **0 issues, 0 bugs, 0 code smells, 0 vulnerabilities and 0 security hotspots**, with measured aggregate coverage 92.3%. Its quality gate is `OK`, but the export has an empty `conditions` array for the initial project analysis: `OK` is not proof that a bespoke set of release thresholds was evaluated. The explicit issue totals, impact/severity export and measured tests are therefore preserved alongside the gate.

The earlier CI failures are infrastructure history: the first scanner workspace was not writable, and the next analysis completed but the export request used an unsupported optional metric. The corrected job uses a writable project-local scanner directory and supported metrics. Initial findings are retained rather than erased. `analysis-history.json` links the exact runs and changes.

`current/` records frontend-completion revision 25c111a from
run 44944497368: zero issues/bugs/smells/vulnerabilities/hotspots, aggregate Sonar
coverage 92.5%, and the explicit initial-project gate caveat above. The separate
policy run 44933945505 passes coverage floors and the full-history Gitleaks scan.
Its exports include successful negative coverage and synthetic-secret canaries.
Initial and triage scan matches are retained as redacted JSON; only four exact
historical fingerprints for two verified false-positive patterns/copies are
scoped in .gitleaksignore. The report commit's scanner additionally matched 15
Sonar-generated issue IDs in the original issue export. Every flagged line was
validated against the exported issue-key set; only those exact historical
fingerprints are scoped. No broad source/test/report directory is excluded.

Dependency audits cover the locked Python packages and pnpm graph. “No known vulnerabilities” is time-bound and does not establish absence of application flaws. `secret-canary-scan.json` checks named synthetic diagnostic strings in the exported successful logs; it is not a generic secret-scanning guarantee. No real passwords, JWTs, database URLs or provider credentials belong in this folder.

## Evidence-identifier secret-scan triage

The full-history Gitleaks 8.30.1 scan flagged thirteen identifiers introduced by
the immutable evidence commit `e0f74ca469231b3a98320967ccc0daab79af25bc`:
twelve actual Git blob object IDs and one Sonar-assigned issue UUID. Each Git ID
was verified with `git rev-parse` and `git cat-file -t` at both measured
revisions; the UUID matches the hash-verified CI issue export. They are
identifiers, not authentication credentials.

[The triage attestation](../evidence/review94-secret-triage.json) records each
exact commit/path/rule/line fingerprint and source-line hash. Only those
fingerprints are appended to `.gitleaksignore`; no rule or directory is
excluded. Raw evidence bytes are preserved, including original scanner HTML
and log whitespace. Default detectors and the synthetic-credential negative
canary remain enabled.

# Review #16: implementation and remaining review actions

This index links concrete feature-branch evidence. It does not tick instructor boxes, close issues or claim independent approval before the team contact verifies them. Existing main remains unchanged by this work.

## Verification checkpoint — 24 November 2026

The last complete integrated run is [45241264964](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45241264964), source `273a9830764b3a81b19702fc5e8d8dc6df9d5028`: all seven jobs pass, with 113 PostgreSQL/backend, 27 acceptance, 20 browser/accessibility/keyboard, 12 HTTP and four scoped penetration cases. Production-image/PostgreSQL restart, seven immutable archive cases, coverage/secret policies and Sonar (zero issues) pass. The load measurement is 42,336 requests, p95 336.34 ms and two connection failures (0.004724%). Earlier failed and intermediate measurements remain separate.

PR #56 now additionally proposes the #63 recipe-to-shopping domain correction. Its actual test-first sequence is recorded in [ingredient-contract evidence](evidence/ingredient-contract/tdd.json); the CI run attached to that new commit must be assessed separately. The previous checkpoint is not relabelled as testing the new code. The existing report/PDF still describes its stated `25c111a` baseline; it must be regenerated for the team's selected final revision.

| Issue | Implementation / evidence | Remaining action |
| --- | --- | --- |
| #17 | #9 plus lossless relational migration #49; constraints, repeated upgrade and existing-data tests | Independent DB review and authorized merge |
| #18 | #9 and concurrent case-variant registration in #49 | Independent auth review |
| #19 | #9/#10; real signed JWT/expiry and owner-qualified feature ports | Independent review |
| #20 | #9/#10/#49; atomic ordered preferences and latest provider input | Independent review |
| #21 | #50 records actual stack, A-01..A-06 and matching limits | Team confirms choices |
| #22 | #50 policies/template and #52 failure gates | Owner enables/verifies protection; tag only after reviewed integration |
| #23 | #12/#52 actual CI, coverage floors, Sonar, secret scan and negative canaries | Check final gate run and require checks through owner settings |
| #24 | #50 gives a dependent review plan; original #6/#7/#8 preserved | Teammates perform real reviews; team decides merge order; no assistant main merge |
| #25/#26 | #9/#10 real owned inventory; 27 acceptance cases and no-deduction assertions | Fridge owner reviews shared implementation |
| #27/#28/#29 | Ayse's #7 code composed in #10; input snapshot, whole-batch validation and measured 28-second timeout. #56's focused #63 follow-up reuses shopping's ingredient domain before any recipe insert | Ayse/Sarp review the shared boundary; real provider credential and live smoke |
| #30 | Sarp's owned detail/history port composed with accepted recipe storage in #10 | Backend/AI/UI cross-review |
| #31/#32/#33/#34 | Sarp's shopping/favorite/history ports retained and connected; reviewed #57 history-clock correction copied into #56; HTTP/browser tests; #63 ingredient boundary regression | Review the current integrated revision; current module-only #57 does not supersede #9 |
| #35/#36/#37/#38/#39 | #56 supplies every connected screen, validation, independent loading/retry, modal feedback and exact preference round trips (#62); 20 browser cases at checkpoint273a983 include three widths, keyboard and accessibility | Fresh review after follow-ups. Safa approved the preceding implementation and announced separate Axios/Tailwind/router restructuring; that restructuring has not been delivered in an open PR at this check |
| #40 | Production image, managed-PostgreSQL contract and restart smoke pass; existing free PostgreSQL retained | User explicitly put deployment on hold pending Sarp's Render access grant for the original team repository. Do not deploy from the personal fork; no live HTTPS/CD is claimed |
| #41 | 48/48 criteria mapped; 27 real-host acceptance cases; unit-module map and actual #49 red/green history | Reviewer assesses scope; no invented earlier TDD |
| #42 | #13 zero-issue follow-up; #15 four probes; JWT/HTTP suite and #52 redacted secret gate | Review evidence and any explicitly scoped false positives |
| #43 | Checkpoint273a983: 42,336 requests / p95 336.34 ms / two connection failures (0.004724%); both unchanged limits pass; first508ms failure preserved | Assess the new commit's own CI; repeat agreed deployment measurement after cloud access |
| #44 | Test report, PDF with embedded figures and dedicated coverage/non-functional/quality evidence in test_work | Yeşim approval, then course PDF upload by authorized account |
| #45/#46 | #51 instructions, prompts, pipeline, commit-linked contribution and observed incident logs | Each member adds their own verified experiences; human review is not fabricated |
| #47 | #50 README, #53 source archive and #54 generic-placeholder cleanup | Team integrates approved docs and verifies final archive; no stale PR deletion here |
| #48 | #51 presentation runbook and prepared source ZIP | Team walkthrough/rehearsal and actual learn.bilgi submission |

The six-member contribution requirement, GitHub Projects usage, independent approvals, main protection, live hosting/provider results and learn.bilgi upload cannot be established by writing a checklist. They remain pending until the appropriate account/team action is observed. The project contact maintains the instructor issue using this evidence.

## Instructor checklist disposition

| Instructor section | Evidence available in the proposed branches | Still required |
| --- | --- | --- |
| A: charter and six contributors | Submitted charter and disclosed commit/PR authorship | Each teammate makes their own actual contribution; team contact verifies all six |
| B: frontend/backend, API, database, auth, secrets | Connected React/FastAPI, OpenAPI/Swagger, relational migrations, owner-scoped JWT/SQL and redacted scan | Independent review, #63 integration; actual cloud hosting and live provider smoke |
| C: branching, versioning and README | docs/CONTRIBUTING.md, PR template, aligned0.1.0 package versions, setup/test documentation and source-only archive builder | Owner protection/settings, reviewed integration, selected release/tag, working cloud/CD URL and final cleanup/README update |
| D: functional/unit, coverage, load, security, Sonar and penetration | Requirement matrix48/48, executed checkpoint above, raw artifacts, failure history and genuine RED/GREEN evidence | Review the new CI results; final report/PDF and archive must match the team-selected source; cloud measurements remain separate |
| E: AI tooling and traceability | AGENTS.md, prompts/, docs/ai-pipeline.md, docs/ai-usage-log.md and docs/ai-mistakes.md | Teammates add their own verified usage/incidents; do not invent human review or live AI results |
| F: diagram/report format and traceability | Submitted PlantUML/Mermaid sources, Markdown reports and requirement/test mappings | Preserve the final source/artifact identities during integration |
| G and presentation | Reproducible source ZIP builder and demo/presentation runbook | Team selects and reviews final commit, refreshes matching PDF/ZIP, rehearses and performs authorized learn.bilgi upload |

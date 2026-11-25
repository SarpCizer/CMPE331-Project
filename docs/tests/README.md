# Fridgely software testing submission

This folder contains the requirement traceability, executed results, non-functional
measurements, code-quality evidence and review report for the integrated application.
Read `software-test-report.md` or its PDF first. Screenshots are embedded in the PDF.

For current assignment and integration status, read
[Kerem's QA handoff](kerem-qa-handoff.md). The independently approved report #67
is merged; its unchanged PDF/Markdown retain the tested `a59556e` application
snapshot. Later source, live Cloudflare and new security-gate checks keep their
own evidence identities. The checkpoints below are historical records.

## Evidence layout

- `coverage/`: the 48-criterion CSV and story summary, Python coverage and mapped
  frontend V8/LCOV summaries. Requirement mapping and source coverage are separate.
- `non-func-tests/`: local SQLite and CI PostgreSQL five-minute load measurements,
  the default-provider timeout measurement, environment and interpretation notes.
- `quality/`: dependency audits, actual SonarQube exports, analysis history and
  rule-specific mitigation/review strategies. An infrastructure failure is retained
  separately from completed analysis findings.
- `evidence/local/`: local JUnit and execution logs.
- `evidence/ci-baseline/`: the first successful integrated full-stack job, preserved
  even though its separate initial Sonar job failed before completing analysis.
- `evidence/screenshots/`: synthetic-account browser evidence at 360/768/1440 px.
- `evidence/source-manifest.json`: hashes of production backend/frontend sources.

## Reproduce the results

Use an isolated database. Install the repository lockfiles as documented in the
root README, explicitly migrate, build the frontend, and run:

```bash
python -m pytest backend/tests --cov=backend/src --cov-branch --cov-report=xml:test-results/coverage.xml
FRIDGELY_PYTHON=python node --test tests/functional/requirements.test.mjs
```

For real PostgreSQL restart verification, set `TEST_DATABASE_URL` to a disposable
PostgreSQL database. Local runs without it explicitly skip that one case; this
skip is not treated as a PostgreSQL pass.

Start the isolated host with `python backend/tests/serve_web_test.py` after building
the frontend. This invokes the real application and SQL database with a controlled
external provider, not a replacement application. Then:

```bash
API_BASE_URL=http://127.0.0.1:8000 node --test tests/fullstack/accounts-isolation.http.test.mjs
pnpm --dir frontend test:e2e
python tests/performance/non_ai_http.py --revision YOUR_REVIEWED_SHA --environment YOUR_TEST_ENVIRONMENT --output test-results/load.json
python scripts/tests/build_traceability.py
```

Install the matching Playwright browser as described in the frontend README. Load
tests create 50 accounts and 5,000 inventory entries; do not run them against a
shared live database. Tokens/passwords are not exported in the results.

The GitHub Actions workflow supplies real PostgreSQL, collects runner artifacts
and executes SonarQube on an ephemeral loopback-only server. Its exported JSON is
the durable analysis evidence. The temporary server URL is not a persistent
dashboard and no analysis credential is committed.

## Review and submission history

At the earlier checkpoint, features were in separate dependent PRs and the report branch was `test_work`.
Yeşim's verified reviewer handle is `yesimyigitbasi`. The user's supplied updated
email sets the PR deadline to 25 November 2026 and approved PDF submission to
29 November; the internal preparation target is 22 November. PR approval and
course-platform submission are not inferred from test execution. Current main
integration and remaining owner actions are recorded in the QA handoff above.

## Historical verification checkpoints

The last complete integrated checkpoint is source273a983, [run45241264964](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45241264964):113 PostgreSQL/backend,27 acceptance,20 browser,12 HTTP and4 penetration cases; all seven jobs pass, including image/restart, archive, coverage, secret scan and Sonar (zero issues). The 50-user/5-minute run records42,336 requests, p95336.34ms and2 connection failures (0.004724%); both unchanged thresholds pass. This is a CI environment result, not a public-cloud measurement.

The #63 recipe-to-shopping follow-up in current #56 adds real-auth/SQL regressions for invalid mixed batches and valid name boundaries. Its source and test-first evidence are recorded in [ingredient-contract/tdd.json](evidence/ingredient-contract/tdd.json); check its own CI run on #56 before using later-source results. [The review checklist](review-16-evidence.md) distinguishes implemented work, review gates and remaining owner/team actions. Cloud deployment is explicitly on hold until Sarp grants Render access to the original repository; the personal fork must not be deployed.

The following report/PDF baseline remains historical. Regenerate the final report and ZIP from the team-selected source after review; do not relabel its old measurements as testing newer code.

## Report baseline evidence (25c111a)

Refs #16, #39, #41-#44. Start with [the test plan](test-plan.md),
[review checklist evidence](review-16-evidence.md), [unit-module mapping](coverage/unit-modules.md)
and [the frontend completion](frontend-completion.md). Candidate #56 source
25c111a is verified in run 44944497368: 106 Python, 27 acceptance, 12 HTTP,
18 browser and four penetration cases pass; the production-image/PostgreSQL
restart check passes. CI coverage and secret policies include passing negative
canaries. Current raw application results are in evidence/ci-frontend.

The initial frontend-completion scan at 522e0db reported one MAJOR S9383 finding;
25c111a marks the internally handled background promise explicitly. Selected
finding fields, artifact identity and mitigation are retained. Final follow-up
analysis is recorded in quality/current and quality/analysis-history.json.
Historical database and policy runs retain their own source/run identities;
old evidence is not relabelled as a new source measurement.

The actual relational preference red/green sequence is in evidence/tdd and PR #49.
The report PDF embeds all six screenshot figures. To regenerate from a full
checkout containing the committed evidence:

```sh
python -m pip install -r scripts/tests/requirements-report.txt
python scripts/tests/export_report.py
```

The default output is build/reports. Set FRIDGELY_REPORT_OUTPUT to another output
directory when needed. Arial or DejaVu Sans fonts are required. The course's
source-only ZIP deliberately omits binary evidence; obtain the full reviewed
repository/evidence to regenerate the PDF.

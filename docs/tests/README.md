# Fridgely software testing submission

This folder contains the requirement traceability, executed results, non-functional
measurements, code-quality evidence and review report for the integrated application.
Read `software-test-report.md` or its PDF first. Screenshots are embedded in the PDF.

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

## Review and submission

Features remain in their separate dependent PRs. The report branch is `test_work`.
Yeşim's verified reviewer handle is `yesimyigitbasi`. The user's supplied updated
email sets the PR deadline to 25 November 2026 and approved PDF submission to
29 November; the internal preparation target is 22 November. PR approval and
course-platform submission are not inferred from test execution. Main is unchanged.

## Current review evidence

Refs #16, #39, #41-#44. Start with [the test plan](test-plan.md),
[review checklist evidence](review-16-evidence.md), [unit-module mapping](coverage/unit-modules.md)
and the criterion CSV. Current application run 44932416317 tests revision 775e8b7:
106 Python, 27 acceptance, 12 HTTP, 8 browser and 4 penetration scenarios pass;
production-image/PostgreSQL restart checks pass; Sonar reports zero issues.
The policy-only run 44933945505 verifies identical application/test/image inputs,
reuses those immutable test artifacts and separately passes coverage/secret gates
and their negative canaries. Raw failures and narrowly reviewed false positives
remain in quality/analysis-history.json and the redacted finding exports.

The actual relational preference red/green sequence is in evidence/tdd and PR #49.
The report PDF embeds all four screenshot figures. To regenerate from a full
checkout containing the committed evidence:

```sh
python -m pip install -r scripts/tests/requirements-report.txt
python scripts/tests/export_report.py
```

The default output is build/reports. Set FRIDGELY_REPORT_OUTPUT to another output
directory when needed. Arial or DejaVu Sans fonts are required. The course's
source-only ZIP deliberately omits binary evidence; obtain the full reviewed
repository/evidence to regenerate the PDF.

# Fridgely Software Testing Report - Draft

**Project:** Fridgely, CMPE 331  
**Evidence snapshot:** 20 November 2026  
**Prepared for:** Kerem Sönmez, DevOps and QA  
**Status:** Draft - integrated staging and production evidence remain incomplete.

## Executive summary

The default branch `main` contains an unimplemented acceptance adapter that returns HTTP 501 for every request. A read-only snapshot of the 27-case functional acceptance suite was run with Node v24.22.3: **0 passed, 27 failed, 0 skipped**. All failures are consistent with the placeholder adapter; they do not indicate regressions in feature-branch code.

The collections implementation is on `backend_work`, and recipe generation is on open PR #7 (`ayse/recipe-ai`). PR #7 reports 16 recipe/integration tests and 59 collections tests passing locally with SQLite and fixtures. These results are author-reported and had no GitHub Actions run at the time of this evidence snapshot. The combined backend suite is being exercised by the CI workflow added in this branch; its result will be recorded after the run completes.

**Release assessment:** Do not report the system as fully tested or deployed. Combined CI, staging, performance, browser, accessibility, and production database evidence are required.

## 1. Scope and test environment

This report covers the acceptance tests and nine non-functional requirements (NFR-01 through NFR-09). It separates tests run against `main` from results reported for feature branches.

- Repository: `SarpCizer/CMPE331-Project`
- Default branch at review: `main`, commit `48b77e9`
- Acceptance command: `node --test tests/functional/requirements.test.mjs`
- Runtime: Node v24.22.3
- App boundary on `main`: `src/acceptance-app.mjs` returns HTTP 501 for every request
- Staging evidence: no staging URL or deployment record was available

## 2. Functional test results

| Suite | Result | Evidence and interpretation |
|---|---:|---|
| Requirements acceptance suite on `main` | 27 tests; 0 pass; 27 fail; 0 skipped | Independently run on a read-only snapshot. All failures receive HTTP 501 from the unimplemented boundary. This is a baseline, not a passing application result. |
| Collections backend on `backend_work` | 59 tests reported passing | Branch README records a 19 November Python 3.12 / SQLite test run. Not independently rerun locally. |
| Recipe integration on PR #7 | 16 tests reported passing | PR reports local SQLite/fixture tests. Test source covers malformed output, declared allergens, provider failures, timeout cancellation, and collection integration. Not independently rerun locally. |
| GitHub Actions | No run at snapshot | No Actions workflow runs were present when this review began. |

The Python results must be rerun together after integration. Feature code is not merged into `main`; the Node acceptance tests still target the 501 adapter and do not validate the Python modules.

## 3. Non-functional requirement evidence

| Requirement | Status | Current evidence / remaining check |
|---|---|---|
| NFR-01 Authorization | Partial | Feature-branch tests cover owner isolation and unauthenticated routes using test authentication. Verify real JWT signature/expiry and every protected route in the integrated host. |
| NFR-02 Credential and secret handling | Not verified | No production password-storage or captured-log inspection. Inspect password hashes, error responses, and logs using seeded secrets. |
| NFR-03 Response time | Not run | No staging load result. Test 50 concurrent signed-in users with 100 inventory entries each; record p95 and error rate over five minutes. Targets: p95 <= 500 ms and error rate < 1%. |
| NFR-04 AI timeout | Partial | PR #7 tests a stalled mocked provider, cancellation, and no partial writes with a 0.1-second test timeout. The 30-second production target has not been measured. |
| NFR-05 Responsive usability | Not run | No browser evidence at 360, 768, and 1440 px across core screens, including empty and error states. |
| NFR-06 Accessibility | Not run | No keyboard-only walkthrough or accessibility audit evidence. |
| NFR-07 Persistence | Partial | `backend_work` includes an SQLite new-application/session persistence test. Restart and user isolation against the agreed production database remain unverified. |
| NFR-08 AI output integrity | Partial | PR #7 test source contains controlled malformed-output and allergen cases. Rerun after integration and check estimate labels in the UI. No live-provider run is claimed. |
| NFR-09 Deployment and reproducibility | Not run | No staging deployment, HTTPS smoke results, or repository secret-scan evidence available. |

“Partial” means relevant test code or a branch-owner-reported run exists, but the full requirement has not been verified in the integrated deployment.

## 4. Required next steps

1. Integrate `backend_work` and PR #7 in an isolated branch. Resolve schema, session, authentication, and route conflicts before merging.
2. Run the pinned Python backend test suite in CI. Keep the 27-case Node suite visibly blocked until its adapter calls the real application.
3. Rerun the combined collections and recipe tests; preserve the command, commit SHA, environment, and output as CI evidence.
4. Connect the real account/JWT and inventory services, then run cross-user, persistence, and PostgreSQL migration checks against the integrated host.
5. Deploy a reviewed revision to staging. Capture HTTPS smoke checks, secret handling, the 30-second AI timeout, five-minute load results, responsive screenshots, and keyboard/accessibility findings.
6. Update this report with verified results and the deployment identifier before submission. Do not mark unexecuted checks as passes.

## 5. Source records

- Requirements tests and NFR definitions: `tests/README.md`, `tests/STATUS.md`, `tests/non-functional/cases.md`, and the functional suite on `main`.
- Collections tests and recorded 19 November result: `backend/README.md` and `backend/tests/` on `backend_work`.
- Recipe integration tests and reported local results: [PR #7](https://github.com/SarpCizer/CMPE331-Project/pull/7) and `backend/tests/test_recipe_integration.py` on `ayse/recipe-ai`.

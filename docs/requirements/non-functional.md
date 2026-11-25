# Non-functional requirements and test cases

This page preserves the original non-functional test plan and its pre-implementation
status. See the [reviewed test report](../tests/software-test-report.md) for
executed results on the approved course source and the [test evidence
index](../tests/README.md) for source-specific follow-up runs. [Issue #43](https://github.com/SarpCizer/CMPE331-Project/issues/43)
records the agreed isolated CI/PostgreSQL environment for the load test.

## NFR-01 Authorization

**Criterion:** All personal resource routes require a valid JWT; cross-user read/write attempts return 403 or 404 and leave data unchanged.

**Test case:** Automated US-15 cases; later expand to every method and resource.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-02 Credential and secret handling

**Criterion:** Passwords are stored as salted password hashes; tokens, passwords and provider keys are absent from client-visible errors and logs.

**Test case:** Inspect account storage and captured logs after sign-in and provider failures; search for seeded secrets.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-03 Response time

**Criterion:** For 50 concurrent signed-in users and 100 inventory entries each, non-AI API requests have p95 response time ≤ 500 ms and error rate < 1% over five minutes in the agreed deployment environment.

**Test case:** Run load scenarios for fridge, profile, shopping and favorites; record environment, p95 and error rate. Proposed target.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-04 AI timeout handling

**Criterion:** AI generation times out within 30 seconds and returns a retryable error without partial state changes.

**Test case:** Use a controllable stalled provider and measure elapsed time; verify unchanged collections. Proposed target.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-05 Responsive usability

**Criterion:** At viewport widths 360, 768 and 1440 px, all core actions remain visible and operable without horizontal page scrolling.

**Test case:** Browser checks on sign-in, fridge, recipes, shopping, favorites and history, including empty/error states.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-06 Accessible core controls

**Criterion:** Core flows work with keyboard-only input; form controls have labels, focus is visible, and validation errors are associated with fields.

**Test case:** Manual keyboard walkthrough plus an accessibility audit; preserve evidence of corrections.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-07 Persistence

**Criterion:** Committed accounts, preferences, inventory, shopping items, favorites and history survive an application restart and remain isolated by user.

**Test case:** Create data for two users, restart app against the same database, sign in again, compare all resources.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-08 AI output integrity

**Criterion:** Accepted recipes include ingredients, ordered steps, positive cooking minutes, nonnegative estimated calories per serving and a positive serving count; declared allergen conflicts are rejected.

**Test case:** Controlled fixture tests for missing fields, invalid numbers and declared excluded allergens; manual review of displayed estimate labels.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

## NFR-09 Deployment and reproducibility

**Criterion:** The web app and backend run on a cloud service; CI runs acceptance tests and later deployment checks; secrets are supplied outside source control.

**Test case:** Deploy to agreed staging service, run core smoke flows over HTTPS, inspect pipeline and repository for credentials.

**Expected result:** The stated criterion is met; otherwise record a defect and rerun after a fix.

**Owner:** Kerem Sönmez coordinates with the relevant feature owner. **Planning baseline:** Not yet executed.

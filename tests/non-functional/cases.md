# Non-functional test cases

## NFR-01 Authorization

**Precondition:** Implemented application and relevant test environment.

**Action:** Automated US-15 cases; later expand to every method and resource.

**Expected:** All personal resource routes require a valid JWT; cross-user read/write attempts return 403 or 404 and leave data unchanged.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-02 Credential and secret handling

**Precondition:** Implemented application and relevant test environment.

**Action:** Inspect account storage and captured logs after sign-in and provider failures; search for seeded secrets.

**Expected:** Passwords are stored as salted password hashes; tokens, passwords and provider keys are absent from client-visible errors and logs.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-03 Response time

**Precondition:** Implemented application and relevant test environment.

**Action:** Run load scenarios for fridge, profile, shopping and favorites; record environment, p95 and error rate. Proposed target.

**Expected:** For 50 concurrent signed-in users and 100 inventory entries each, non-AI API requests have p95 response time ≤ 500 ms and error rate < 1% over five minutes in the agreed deployment environment.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-04 AI timeout handling

**Precondition:** Implemented application and relevant test environment.

**Action:** Use a controllable stalled provider and measure elapsed time; verify unchanged collections. Proposed target.

**Expected:** AI generation times out within 30 seconds and returns a retryable error without partial state changes.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-05 Responsive usability

**Precondition:** Implemented application and relevant test environment.

**Action:** Browser checks on sign-in, fridge, recipes, shopping, favorites and history, including empty/error states.

**Expected:** At viewport widths 360, 768 and 1440 px, all core actions remain visible and operable without horizontal page scrolling.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-06 Accessible core controls

**Precondition:** Implemented application and relevant test environment.

**Action:** Manual keyboard walkthrough plus an accessibility audit; preserve evidence of corrections.

**Expected:** Core flows work with keyboard-only input; form controls have labels, focus is visible, and validation errors are associated with fields.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-07 Persistence

**Precondition:** Implemented application and relevant test environment.

**Action:** Create data for two users, restart app against the same database, sign in again, compare all resources.

**Expected:** Committed accounts, preferences, inventory, shopping items, favorites and history survive an application restart and remain isolated by user.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-08 AI output integrity

**Precondition:** Implemented application and relevant test environment.

**Action:** Controlled fixture tests for missing fields, invalid numbers and declared excluded allergens; manual review of displayed estimate labels.

**Expected:** Accepted recipes include ingredients, ordered steps, positive cooking minutes, nonnegative estimated calories per serving and a positive serving count; declared allergen conflicts are rejected.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

## NFR-09 Deployment and reproducibility

**Precondition:** Implemented application and relevant test environment.

**Action:** Deploy to agreed staging service, run core smoke flows over HTTPS, inspect pipeline and repository for credentials.

**Expected:** The web app and backend run on a cloud service; CI runs acceptance tests and later deployment checks; secrets are supplied outside source control.

**Status:** Not executed. Capture environment, steps, actual result and evidence before reporting a pass.

Definition: [requirements](../../docs/requirements/non-functional.md).

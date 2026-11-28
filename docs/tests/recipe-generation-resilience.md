# Recipe generation resilience after the live 503

Refs #16, #40, #67 and #102. This is a behavior change, not a relabelling of
previous cloud results. The actual `abdca3f` normal 14-ingredient run returned
503 after 28.30 seconds with unchanged inventory/preferences. Its Quick run
returned 18 recipes in 20.54 seconds. Main's nine successful controlled CI jobs
did not establish reliable live inference.

## Diagnosis and correction

The service has a 28-second outer deadline (NFR-04). The previous TaskGroup
cancelled every complementary request when any sibling raised a transport
exception, and waited for every sibling even if other complete responses were
already available. A slow group could therefore discard successful completed
work at the outer deadline. The normal run also logged an invalid measurement;
its exact upstream content was deliberately not retained, so that separate
schema failure is not asserted to be a timeout.

Complementary discovery requests now have a 26-second collection deadline,
leaving room inside the unchanged 28-second outer budget for cancellation,
validation and saving. Completed responses are retained in original group order
and every distinct complete recipe is considered. Transient network errors and
HTTP 5xx get at most one retry, within the same deadline, without repeating
healthy siblings. Rate limits (429) are not retried immediately. Authorization
errors and malformed completed responses remain hard failures.

All completed candidates still pass schema, explicit dose, declared exclusion,
content and mood validation before one owner-scoped insert transaction. A hard
failure prevents all writes. No ingredient quantity, missing field or JSON tail
is invented. The existing bounded token-prefix rule is unchanged. Weekly
requested dishes remain exact-one/exact-portions with strict validation.

When some groups are unavailable but other complete, validated recipes exist,
HTTP200 contains those recipes and `X-Fridgely-Generation-Incomplete: true`.
The browser displays the ready cards and the exact same wheel choices, with a
visible message that additional suggestions could not finish and generation can
be retried. This is an explicit successful-but-incomplete *search*, never a
partially saved recipe or a claim that all possible dishes were found. When no
group succeeds, the service still returns a sanitized retryable 503 and writes
nothing. Arbitrary third-party outages cannot be guaranteed away.

Caller cancellation and either deadline cancel and await outstanding tasks.
No stock, preferences, favorites, shopping or history changes occur on failed
generation. Successful generation only inserts the validated recipes; history
is added by actual detail views.

## Count, correctness and performance

There is no fixed recipe count, response slicing, reduced token budget, paid
plan/model change or fixture fallback. Every group receives the complete pantry,
known quantities and preferences/exclusions, with complementary priorities
covering every inventory entry. The 3200-token group budgets, 4800-token small
pantry budget and 2400-token requested-dish budget are preserved. The compact
prompt no longer simultaneously requests amount objects and amount strings;
it asks for one measured-string format and minified JSON. Nutrition and cooking
time remain estimates; physical quantities still require user review.

## Test-first evidence and release gates

The six initial regressions against `abdca3f` yielded five failures and one pass,
retained in test-only commit `6e1fe608a1816b0b4331a7a81057f9448cdb47d3`.
New tests exercise a stalled sibling, retry without duplicate healthy requests,
rate limiting, total outage, declared exclusions in an incomplete search,
strict malformed-response failure, unambiguous compact amounts, explicit HTTP
completion metadata, persistence/anonymous denial and unchanged stock/history.
The prior fail-fast test now specifically covers a non-retryable 403; a 429
no longer cancels a healthy sibling. The original complete-outage deadline and
hard schema/allergen atomicity tests remain required.

Two browser cases cover the completion notice, exact card/wheel correspondence,
clearing the notice after a complete retry, unchanged stock, axe accessibility
and 360/1440px layout. Three additional targeted mutations disable retry,
drop completion metadata and discard successful groups: each must be killed.
Actual integrated CI, peer review, main CI, exact-source automatic deployment
and real normal/Quick content review remain separate release gates. No live
success is claimed from these controlled tests.

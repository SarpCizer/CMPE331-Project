# Recipe response compatibility follow-up

Refs #16, #40, #67, #100. This document supplements the frozen course report;
it does not revise historical measurements or claim an instructor submission.

## Actual released baseline

SarpCizer approved PR100 head `51674a55039065f19f33be92d6910e04dd4ab91b`
in review 6097470781. Merge `8031e617b111f1dd4fe0d0b6246357914220fca4`
passed all nine jobs in Actions run 46142196700 and became LIVE on free Render
deploy `dep-dc5ca3jbc2fs73aoba1g` at 2026-11-28T12:12:54Z. Existing-account
data/session preservation, password rotation, sign-out/sign-in, the six remaining
new-entry units, and quantity-aware shopping purchase passed actual live checks.

Actual AI did **not** pass: normal generation returned HTTP502 in 19.68 seconds
at 12:14:49Z, and Quick & Easy returned HTTP502 in 23.59 seconds at 12:17:44Z,
both with zero recipes. Inventory/preferences remained unchanged. The application
logged `Cloudflare structured recipe response rejected`; the raw model response
was not recorded or inspected, so its specific malformed shape is unproven.
Passing controlled-provider tests do not override these live failures.

## Test-first change

`backend/tests/test_cloudflare_wire_variants.py` produced **16 failed / 22 passed**
against that preceding source, before production code changed. Red tests are
retained in commit `dab2188801165371197e33f510182c56d5602cc7`.

The Cloudflare adapter now accepts complete unambiguous records inside closed
JSON fences, arrays, or a single-record wrapper; resolves full/short field names;
and normalizes explicit metric/count spellings without changing a quantity or
inventing a density. Missing fields and conflicting aliases remain invalid.
Provider-supplied identity/unknown metadata never becomes a trusted recipe field.

Only when numeric finite provider usage confirms the configured output-token
limit, normal discovery may retain fully decoded recipe objects preceding an
unfinished final object. It does not repair JSON values, manufacture fields,
return an unfinished recipe, skip an invalid complete recipe, or recover after
a timeout. All completed candidates still undergo measurement, schema, content,
allergen and mood validation before one atomic save. Requested weekly dishes
retain their strict one-recipe/exact-portions contract, with no prefix recovery.
The response parser is bounded; diagnostics contain fixed reason codes and
counts only, never model text, pantry/preferences, passwords, keys or tokens.

All complementary requests still receive the full pantry, every supplied stock
amount and saved exclusions. Their priorities jointly cover the whole pantry.
The existing parallel requests, compact wire format, 28-second cancellation,
free 70B model and token budgets are preserved. There is no recipe-count target
or output slicing. Exact duplicates are removed while distinct preparations
remain. No stock is deducted by generation. A successful wire adaptation alone
does not establish culinary correctness or prove the observed live fault fixed.

## Verification and release status

The targeted mutation campaign adds token-limit-gate and alias-conflict faults
to the existing 21, for **23 selected mutants**, not whole-project mutation
coverage. CI must retain actual source-pinned baseline/kill results, PostgreSQL,
browser, authorization, ZAP, Sonar and load evidence. After independent review,
merge and automatic checks-pass deployment, actual provider output must be
checked for completeness, ingredient coverage, sensible measured quantities,
excluded allergens, preparation steps and persistence before final readiness.

The final Software Testing Report must retain the failed live measurements
above alongside the final source's actual measurements. At this writing this
follow-up has not been merged or verified on the live provider.

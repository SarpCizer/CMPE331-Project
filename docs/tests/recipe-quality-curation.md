# Usable recipe candidate curation

Refs #16, #40, #67, #101. This is a focused follow-up to the actual released
source `fd293bb3eed3d08b50a8fbe1c85621455e608653`, not a relabelling of older tests.
PR101 received SarpCizer's exact-head approval, passed all nine jobs in main run
46146845091 and became LIVE in free Render deploy `dep-dc5d5ctbedkc73ejf8k0`.

## Retained live observations

Normal discovery returned HTTP200 in **28.02s with 22 recipes**, using all 14
pantry ingredient names. Complete fields, persisted details, denied anonymous
access and unchanged inventory/preferences passed. Manual review nevertheless
found an undosed oil brushing step and optional bread/herbs/lemon outside the
listed ingredients. A Quick & Easy call with a synthetic fish exclusion returned
**HTTP502 in 19.28s**, with zero recipes and unchanged stock/preferences. Its exact
raw cause is unproven; it is not presented as a successful live release check.
Account/session/data preservation, same-credential return, password rotation,
the six remaining new-entry units and shopping purchase-to-fridge passed LIVE.
These non-AI passes do not override the recipe failures.

## Explicit candidate policy change

Discovery now keeps every usable, complete, distinct candidate after validating
the entire response's schema, measurements and declared allergens. These hard
failures still reject the whole request before any insertion; provider failures
still cancel work and deadlines do not produce partial writes.

Content candidates that fail the explicit salt, bread or known unlisted-step
ingredient review can be withheld while other validated choices are saved in
one owner-scoped transaction. This is a deliberate change from the previous
all-content-errors-reject-everything behavior. A batch with no usable choices
still fails with no writes; no invalid candidate is accepted to force HTTP200.
Requested weekly dishes and direct strict validation keep the strict contract.
The mood time limit remains a hard batch rule. Malformed measurements, missing
steps and declared excluded allergens are not silently filtered away.

Only standalone optional accompaniment/garnish instructions introducing known
unlisted extras are omitted. A required unlisted oil/ingredient step is not
repaired: its dose, replacement and recipe are not invented. The bounded English
checks target observed oil, bread, lemon and herb errors; they do not certify
arbitrary natural-language food semantics, nutrition or physical stock densities.
Generated calories/time remain estimates and cooking quantities require review.

A well-formed empty complementary group no longer discards other groups' usable
results. Invalid groups still reject the request. All groups still receive the
full pantry/amounts/preferences and jointly prioritize all ingredient entries.
There is no fixed recipe-count target, output slicing, reduced token budget,
paid plan/model change or fixture fallback. Stock changes only on explicit
user actions. Logs contain fixed quality reason codes, never recipe/user text.

## Verification

Before implementation, the new/updated focused tests produced **8 failures and
19 passes** against mainfd, retained in red commit
`a5229d7365906943d7a9fd72c64917f73f3c7f53`. The tests cover empty valid groups,
optional versus mandatory extras, all-unusable failure, >6 retained usable
choices, persisted-row counts and strict schema/measurement/allergen failures.
History is checked before details are viewed; actual views then correctly appear
in history (US14). The first green-run history assertion mistakenly expected no
history after viewing details; that test oracle was corrected without weakening
the no-view/no-write assertion.

Three new targeted source mutations check empty-group poisoning, bypassed extra
ingredient validation and disabled usable-content selection, for 26 selected
faults in total. This remains a scoped experiment, not whole-project mutation
coverage. CI, independent final-head review, exact-source automatic deployment
and actual normal/quick recipe review must pass before final readiness or the
syllabus-aligned Software Testing Report PDF is claimed.

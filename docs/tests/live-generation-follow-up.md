# Real-provider follow-up after #99

Refs #16, #40, #67, #99. Prepared with Codex assistance on 28 November 2026.
This file records a new defect; it does not relabel previous green tests as proof
that the real AI provider always works.

## Observations on deployed source 4284552

Main run [46066290240](https://github.com/SarpCizer/CMPE331-Project/actions/runs/46066290240)
passed all nine jobs, including 1,025 backend, 53 browser, 32 acceptance and
12 HTTP checks, zero Sonar issues and zero high/medium/low ZAP alerts. The free
Render deployment was observed LIVE at 2026-11-27T21:07:55Z. An account seeded
before deployment retained its valid session, original sign-in credentials,
fridge, shopping and preferences. Password rotation revoked its earlier token
and preserved those records. A separate real browser passed the same returning
sign-in and new password form, with all five moods and no Low Budget option.

Actual provider calls used a random synthetic account, the same 14 pantry
entries/amounts, the existing 70B model and no fixture provider:

| Mood | HTTP | Seconds | Recipes |
| --- | --- | --- | --- |
| Normal, first call | 503 | 28.24 | 0 |
| Quick & Easy | 200 | 24.16 | 21 |
| Normal, second call | 503 | 28.07 | 0 |

All three left inventory/preferences unchanged. The quick response covered all
14 pantry ingredient names and passed DTO/persistence/isolation checks. Manual
content review nevertheless found a packet of salt used as a cooking dose,
strawberry toast without bread in its ingredients, and poultry/fish steps using
browning without a thermometer endpoint. Therefore #99 is merged/deployed but
is **not** evidence of completed live recipe reliability or semantic correctness.

The non-AI main load run met the unchanged NFR (48,148 requests, p95 211.11ms,
error rate 0.00208% <1%). Its one status-zero client HTTPError is retained. No
application exception or 5xx marker occurred in the exported host log. The exact
client exception was not retained, so its cause is unproven, not silently fixed.

## Focused correction

Five regressions failed against 4284552 (one control passed; 0.22 seconds),
retained in `6b9de9871262ec216ac8ec5a568c4b23ee6e2e44` before implementation.
The parallel Cloudflare wire uses short field names and measured amount strings,
then expands them to the unchanged public/stored DTO. No fields, quantity data,
steps, servings, pantry entries or dietary/allergen restrictions are dropped.
There is no numeric recipe-count target/cap; the 3,200-token per-group budget,
existing model, four-call concurrency bound and 28-second cancellation remain.
Groups focus on their own complementary priorities instead of each repeating
every main protein. The full pantry still accompanies every call. Weekly dish
and OpenAI contracts retain their original full-field wire.

A serialization comparison on all 21 observed recipes, without deleting any
field or step, was 8,860 to 5,609 UTF-8 bytes (36.69% smaller). This is a wire-size
measurement, **not** a measured live latency improvement. Only a new approved
source observed LIVE and real-provider measurements can establish improvement.

A recipe sanity gate rejects unmeasured salt packages and salt amounts above a
conservative 10g per serving review boundary (a recipe sanity rule, not dietary
advice). Toast dishes must include bread/toast; merely toasting seeds is allowed.
Both providers and requested weekly dishes pass through the same gate before
atomic recipe insertion. Any rejected candidate rejects the whole batch with
no partial history/inventory writes; invalid/allergen/quantity checks remain.
Existing optional-measure legacy DTOs remain readable.

Known poultry/fish ingredient names get a thermometer endpoint before serving,
without removing the model's steps. The temperature reference is the
[FDA Safe Food Handling table](https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling).
This bounded check covers the observed English-name defects; it is not a
universal ingredient ontology, a proof of every cooking instruction or an
allergen/nutrition certification. Other semantic mistakes remain possible and
actual live output must still be inspected.

The seeded mutation campaign adds three faults for compact decoding, measured
seasoning and bypassed recipe review: 21 selected mutations in total. This is
not whole-project mutation coverage. The final Software Testing Report must
include these actual final-source outcomes and retained live failures, rather
than declaring the preceding candidate ready.

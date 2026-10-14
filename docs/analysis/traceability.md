# Requirements-to-analysis traceability

Baseline: approved requirements revision `4839cdf`. All 15 stories and 48 numbered acceptance criteria are retained. No story is omitted as obvious. The [criterion-level JSON](coverage.json) repeats each exact approved criterion and maps it to a behavior model, logical data entities and a planned frontend state. It is checked against the dedicated story definitions by the validation script.

| Story | Criteria | Behavior | Data entities | Preliminary frontend state |
|---|---:|---|---|---|
| [US-01](../requirements/US-01.md) | 3 | [Activity model](behavior/US-01.md) | ACCOUNT | Register |
| [US-02](../requirements/US-02.md) | 2 | [Activity model](behavior/US-02.md) | ACCOUNT | Sign in |
| [US-03](../requirements/US-03.md) | 3 | [Activity model](behavior/US-03.md) | DIETARY_PREFERENCE, ALLERGEN_EXCLUSION | Preferences |
| [US-04](../requirements/US-04.md) | 3 | [Activity model](behavior/US-04.md) | INVENTORY_ENTRY | Fridge / add |
| [US-05](../requirements/US-05.md) | 3 | [Activity model](behavior/US-05.md) | INVENTORY_ENTRY | Fridge / empty and populated |
| [US-06](../requirements/US-06.md) | 3 | [Activity model](behavior/US-06.md) | INVENTORY_ENTRY | Fridge / remove |
| [US-07](../requirements/US-07.md) | 4 | [Activity model](behavior/US-07.md) | INVENTORY_ENTRY, DIETARY_PREFERENCE, ALLERGEN_EXCLUSION, RECIPE, RECIPE_INGREDIENT, RECIPE_STEP | Recipes / loading and results |
| [US-08](../requirements/US-08.md) | 3 | [Activity model](behavior/US-08.md) | RECIPE, RECIPE_INGREDIENT, RECIPE_STEP, RECIPE_VIEW | Recipe details |
| [US-09](../requirements/US-09.md) | 3 | [Activity model](behavior/US-09.md) | RECIPE, INVENTORY_ENTRY, DIETARY_PREFERENCE, ALLERGEN_EXCLUSION, SHOPPING_ENTRY, FAVORITE, RECIPE_VIEW | Recipes / error and retry |
| [US-10](../requirements/US-10.md) | 4 | [Activity model](behavior/US-10.md) | RECIPE_INGREDIENT, INVENTORY_ENTRY, SHOPPING_ENTRY | Recipe details / add missing |
| [US-11](../requirements/US-11.md) | 4 | [Activity model](behavior/US-11.md) | SHOPPING_ENTRY | Shopping / add, remove and empty |
| [US-12](../requirements/US-12.md) | 3 | [Activity model](behavior/US-12.md) | FAVORITE, RECIPE | Recipe details / save |
| [US-13](../requirements/US-13.md) | 3 | [Activity model](behavior/US-13.md) | FAVORITE, RECIPE, RECIPE_VIEW | Favorites / remove and empty |
| [US-14](../requirements/US-14.md) | 4 | [Activity model](behavior/US-14.md) | RECIPE_VIEW, RECIPE | History / newest first |
| [US-15](../requirements/US-15.md) | 3 | [Activity model](behavior/US-15.md) | ACCOUNT, INVENTORY_ENTRY, DIETARY_PREFERENCE, ALLERGEN_EXCLUSION, SHOPPING_ENTRY, RECIPE, FAVORITE, RECIPE_VIEW | Sign in / expired session; access checks require backend |

Cross-cutting ownership is modeled by US-15 and applies before every US-03 to US-14 operation. The [generation](behavior/generation-sequence.md), [shopping](behavior/shopping-sequence.md) and [authorization](behavior/authorization-sequence.md) sequences expand the highest-risk interactions.

## Quality requirements

| Quality requirement | Analysis response | Verification that remains for implementation |
|---|---|---|
| NFR-01 Authorization | Owner-qualified queries and composite recipe-owner references; US-15 gate | Exercise every route/method, including child data and forged tokens |
| NFR-02 Credentials | Salted password hash only; sanitized provider errors; no secrets in models/UI | Storage/log inspection and JWT signature tests |
| NFR-03 Response time | Candidate owner lookup and uniqueness indexes in dictionary | Measure p95 under the agreed load and environment |
| NFR-04 AI timeout | Bounded provider call, 30-second limit, retryable 503 with rollback | Controlled stalled-provider timing test |
| NFR-05 Responsive UI | Mockups intended for 360, 768 and 1440 px | Browser viewport checks; live backend flows later |
| NFR-06 Accessibility | Explicit labels, keyboard-operable actions, focus and status feedback | Keyboard and accessibility audit with the implemented UI |
| NFR-07 Persistence | Stored owned entities and transaction boundaries; relational/NoSQL mapping | Restart and two-account isolation tests |
| NFR-08 AI integrity | Validate whole batch before persistence; ordered ingredients/steps and estimates | Fixture and live-provider verification; UI labels |
| NFR-09 Deployment | Framework/database choices remain open; diagram tools isolated from app | Cloud deployment, HTTPS and CI checks |

## Consistency review

The analysis preserves name-only inventory and immutable addition dates, no expiry or OCR, no automatic ingredient deduction, private recipes, all-or-nothing generation, normalized missing-name matching, idempotent shopping/favorites, detail-view-only history and authenticated ownership. Clearing preferences is represented explicitly. No purchase-completion state, shared household, quantity reconciliation, email verification, recipe deletion or automatic retry is added.

The requirements' US-07 wording withholds conflicting recipes; the approved API and tests further specify whole-batch rejection. Models follow the stricter existing contract (422 with no accepted rows), not partial filtering. Numeric estimates and display warnings preserve US-08 and NFR-08. Draft concurrency/tie-order details are identified as A-01 through A-06 in the data dictionary rather than silently changing approved requirements.

Models describe intended behavior, not completed functionality. Existing 27 acceptance tests remain intentionally failing; this analysis does not implement the application boundary. Prototype browser checks do not prove authentication, persistence, cryptographic security, real AI behavior or production accessibility.

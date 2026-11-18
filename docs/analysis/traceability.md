# Requirement-to-analysis traceability

All 15 stories and 48 exact numbered criteria from approved requirements `4839cdf` remain unchanged. The [criterion-level mapping](coverage.json) has a primary DFD and explicit supporting DFDs; a filename match alone is not semantic coverage. Each diagram's prose names constraints that data-flow arrows cannot represent.

| Story | Criteria | Primary model | Supporting model views |
|---|---:|---|---|
| [US-01](../requirements/US-01.md) | 3 | [US-01 DFD](behavior/US-01.md) | - |
| [US-02](../requirements/US-02.md) | 2 | [US-02 DFD](behavior/US-02.md) | - |
| [US-03](../requirements/US-03.md) | 3 | [US-03 DFD](behavior/US-03.md) | US-07, US-15 |
| [US-04](../requirements/US-04.md) | 3 | [US-04 DFD](behavior/US-04.md) | US-15 |
| [US-05](../requirements/US-05.md) | 3 | [US-05 DFD](behavior/US-05.md) | US-15 |
| [US-06](../requirements/US-06.md) | 3 | [US-06 DFD](behavior/US-06.md) | US-08, US-12, US-15 |
| [US-07](../requirements/US-07.md) | 4 | [US-07 DFD](behavior/US-07.md) | US-15 |
| [US-08](../requirements/US-08.md) | 3 | [US-08 DFD](behavior/US-08.md) | US-07, US-09, US-14, US-15 |
| [US-09](../requirements/US-09.md) | 3 | [US-09 DFD](behavior/US-09.md) | US-07, US-15 |
| [US-10](../requirements/US-10.md) | 4 | [US-10 DFD](behavior/US-10.md) | US-11, US-15 |
| [US-11](../requirements/US-11.md) | 4 | [US-11 DFD](behavior/US-11.md) | US-15 |
| [US-12](../requirements/US-12.md) | 3 | [US-12 DFD](behavior/US-12.md) | US-15 |
| [US-13](../requirements/US-13.md) | 3 | [US-13 DFD](behavior/US-13.md) | US-14, US-15 |
| [US-14](../requirements/US-14.md) | 4 | [US-14 DFD](behavior/US-14.md) | US-15 |
| [US-15](../requirements/US-15.md) | 3 | [US-15 DFD](behavior/US-15.md) | - |

US-03 AC-3 also maps to generation for provider inputs. US-06 AC-3 maps to details/favorites for no deduction. US-08 AC-2 maps to generation/failure handling because malformed output is rejected before details exist. US-13 AC-2 maps to history to show retention. US-15 supplements every protected story and validates referenced IDs in URL and body.

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


## Consistency corrections

- Generation returns complete recipe objects, as specified by the approved API; the old summary label has been removed.
- Preference storage preserves submitted list values, ordering and repeats through ordinal keys. Derived normalization keys are not uniqueness rules for saved preference arrays.
- Missing inventory IDs produce 404; foreign IDs produce 403/404. These are distinct outcomes in the deletion process specification.
- Authorization checks object IDs even when they are body fields on collection operations, including POST /favorites.
- Only manual inventory additions/deletions write D3. Generation, details, shopping, favorites and history cannot deduct or restock ingredients.
- Favorite removal does not delete the recipe or a view record. History is created/refreshed on detail views only.

Data normalization for missing-ingredient matching, declared-allergen filtering and account email remains as approved. Inventory dates remain addition timestamps. Whole-batch malformed/allergen rejection follows the existing API/test contract. Framework/database/provider selection and proposals A-01 through A-06 remain for review; the mockup is illustrative and does not establish production security or persistence.

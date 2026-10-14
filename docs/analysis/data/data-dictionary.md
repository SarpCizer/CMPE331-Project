# Data dictionary, integrity and storage decisions

Analysis baseline: requirements commit `4839cdfdf7f53f226373380f41c307886d08906a`, merged into `main` by `d9178ed8b4d6cf38df3ded201a3fb5cfdd9a0694`. Models interpret the approved behavior without changing it. Types and storage layout below are draft design choices; no migration or production implementation is included.

## Entities and attributes

Unless noted otherwise attributes are required and non-null. IDs are opaque application-assigned values. Display names retain user-readable text; normalized keys apply trimming and case normalization consistently on the server. A final Unicode/synonym vocabulary is unresolved (D-03/D-11); the normalization used for inventory, recipes, shopping and allergen matching must agree. Display timestamps are local; stored instants are UTC.

| Entity | Key and attributes | Integrity / lifecycle | Requirements |
|---|---|---|---|
| ACCOUNT | PK account_id; email; UK normalized_email; password_hash | Case-insensitive email uniqueness enforced atomically, including concurrent registration. Store salted hash, never plaintext; no verification flag or email workflow. Account deletion is outside scope. | US-01, US-02, US-15 |
| DIETARY_PREFERENCE | Composite PK (account_id, value_key); FK account_id; display_value | Zero rows means an empty dietary list. Replace the complete list atomically together with allergen exclusions. Duplicate normalized values need not be stored. Vocabulary remains open. | US-03, US-07 |
| ALLERGEN_EXCLUSION | Composite PK (account_id, value_key); FK account_id; display_value | Zero rows means no declared exclusions. Empty replacement clears prior values. This is a declared-ingredient filter, not a safety guarantee. | US-03, US-07 |
| INVENTORY_ENTRY | PK entry_id; FK account_id; ingredient_name; normalized_name; added_at | Nonblank trimmed name. added_at is server-generated UTC and immutable on reads. Duplicate names may exist; the approved requirements do not require inventory deduplication. Never infer quantity, freshness or expiry. | US-04, US-05, US-06 |
| RECIPE | PK recipe_id; FK account_id; title; cooking_minutes; calories_per_serving; servings | Nonblank title; cooking_minutes > 0; calories_per_serving >= 0; servings is a positive integer. Estimates per serving, not measured nutrition. Also declare UNIQUE(account_id, recipe_id) for composite owner FKs. | US-07, US-08, US-15 |
| RECIPE_INGREDIENT | Composite PK (recipe_id, position); FK recipe_id; ingredient_name; normalized_name | Positive ordinal, nonblank names, at least one row per accepted recipe. Order is preserved on API reconstruction. Ingredient text remains name-based; no quantity arithmetic is introduced. | US-07, US-08, US-10 |
| RECIPE_STEP | Composite PK (recipe_id, position); FK recipe_id; instruction | Positive ordinal, nonblank instructions, at least one step per accepted recipe. Return steps by position ascending. | US-08 |
| SHOPPING_ENTRY | PK entry_id; FK account_id; ingredient_name; normalized_name | UNIQUE(account_id, normalized_name), nonblank name. Existing row IDs remain stable on repeated add-missing actions. Manual duplicate adds may return the existing row; the acceptance contract specifies 201 only for a new item. | US-10, US-11 |
| FAVORITE | Composite PK (account_id, recipe_id); FK account_id; composite FK (account_id, recipe_id) to RECIPE | Prevent duplicate saves and foreign-account references. Removing this row does not remove RECIPE or RECIPE_VIEW. No new inventory mutation. | US-12, US-13, US-15 |
| RECIPE_VIEW | Composite PK (account_id, recipe_id); FK account_id; composite FK (account_id, recipe_id) to RECIPE; last_viewed_at | Upsert only when details are opened, using server time. List by last_viewed_at descending. Timestamp ties use recipe_id as a proposed stable secondary key. Generation and favorite actions alone do not create views. | US-08, US-14, US-15 |

## Business invariants

1. **Owner boundary:** Every protected operation authenticates a signed JWT, checks expiry against the server clock and derives account_id from its verified subject. Client owner IDs never determine ownership. Use owner-qualified object queries; validate composite recipe ownership before creating a favorite or view. Ingredient/step rows are read only through an owned recipe. Unauthorized requests do not mutate data.
2. **No hidden inventory edits:** Only manual inventory add/delete changes INVENTORY_ENTRY. Generation, opening details, shopping changes, saving/removing favorites and viewing history leave inventory unchanged.
3. **Generation atomicity:** Snapshot the current account's inventory names and both preference lists for the request. Empty inventory returns 400 without invoking AI. Validate the entire provider batch before assigning accepted internal IDs and committing RECIPE, RECIPE_INGREDIENT and RECIPE_STEP together. A declared allergen conflict rejects the whole batch with 422 under the approved contract; malformed output returns 502. Timeout/unavailability returns retryable 503 within 30 seconds. No partial results or changes to inventory/preferences/shopping/favorites/history on failure. Provider candidates are transient; do not store them as accepted recipes.
4. **Missing ingredients:** missing = unique normalized recipe ingredient names minus normalized inventory names. Insert only missing names not already in the account's shopping list, atomically; concurrent requests rely on the same uniqueness rule and upsert/retry strategy. Return the resulting list. Inventory is not decremented and shopping removal never moves food into the fridge.
5. **Stable recipe references:** Recipes remain available for the owner's favorites/history. Recipe deletion and automatic cleanup are not defined in this release, so no cascade from favorite removal or inventory deletion to recipes is permitted. Future retention rules need a reviewed change.
6. **Valid complete recipes:** Required title, ingredients and ordered steps are nonblank; ingredient and step collections are nonempty; numeric constraints above apply to every candidate. Database checks alone cannot enforce cross-row minimum collection sizes; the generation transaction must enforce them.
7. **No unbounded scope:** JWTs are issued credentials, not required persisted session rows. Provider secrets live outside user data and source control. There is no OCR entity, expiry field, quantity deduction, shopping completion checkbox or shared recipe catalog in the approved scope.

## Candidate indexes and transactions

These are logical access paths, not a final physical schema. Use unique normalized email, account inventory lookup, unique account/shopping normalized name, owned recipe lookup, favorite composite PK and history (account_id, last_viewed_at DESC, recipe_id). Sorting inventory is a UI choice; list reads must not rewrite added_at.

Transaction boundaries: registration with unique email; replace both preference lists; persist a complete validated recipe batch and children; add missing ingredients with uniqueness; save favorite idempotently; and read owned recipe plus history upsert. A failed history write must not return a successful detail-open response that falsely claims the view was recorded. Database selection must support equivalent atomicity and uniqueness semantics.

The analysis does not select transaction isolation for concurrent preference edits or concurrent fridge edits during generation. Proposed behavior is a consistent request-start snapshot; a later request sees the latest committed lists. A generation in flight may use its captured snapshot. Team agreement on this concurrency detail is required before design.

## NoSQL mapping if MongoDB is selected

Keep an accounts collection with both preference arrays embedded; replacing them in one document is atomic. Store inventory and shopping as owner-keyed collections with the same name/unique rules. Recipes may embed ordered ingredient and step arrays, while favorites and views remain owner-qualified references. A unique index on (account_id, recipe_id) preserves idempotence. MongoDB references do not enforce foreign keys: application transactions must enforce owner and existence checks. Complete multi-recipe batches must commit atomically using an appropriate transaction or a reviewed equivalent; embedding one recipe does not make a whole batch atomic. The logical E-R cardinalities and invariants still apply.

## Decisions for analysis review

| ID | Proposed detail | Existing behavior preserved |
|---|---|---|
| A-01 | Account-owned immutable accepted recipe snapshots | US-07/08/15; prevents global recipe lookup leakage |
| A-02 | Separate dietary/allergen preference rows, or embedded profile arrays | US-03 lists and clearing semantics |
| A-03 | Unique owner/name shopping key and owner/recipe association keys | US-10/12 idempotence under concurrency |
| A-04 | Stable recipe_id tie-breaker when history timestamps tie | US-14 newest-first; tie ordering was unspecified |
| A-05 | Consistent request-start inventory/preferences snapshot | US-07 latest saved input at request start; in-flight concurrency requires review |
| A-06 | Successful detail reads include a committed history upsert | US-08/14; preserve observed view semantics |

Framework, database engine, JWT algorithm/lifetime, allergen synonyms, retention, rate limiting and deployment remain software-design questions. Do not silently treat these proposals as new approved requirements.

# Criterion and assertion traceability

Assertion source: `93d60d0c425f2ba1b6e61d13b03db484982be0b5`. 48 ACs, nine NFRs, 28 unique physical acceptance IDs.
Each row names its concrete assertion and purpose. Reusing a case for several criteria is explicit; IDs are never reassigned.
Mappings are not test pass counts. Use same-source JUnit/CI evidence or a retained test-source equivalence proof.
Controlled provider tests do not certify live inference, nutrition or undeclared allergens.

| Criterion | Case / concrete verification | Assertion |
|---|---|---|
| US-01/AC-01 | `US-01-T01`: ID/public email and immediate login without email verification | [L12](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L12) |
| US-01/AC-02 | `US-01-T02`: Normalized duplicate email rejected | [L17](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L17) |
| US-01/AC-03 | `US-01-T02`: Invalid email/short password rejected; valid retry proves no email reservation | [L21](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L21) |
| US-02/AC-01 | `US-02-T01`: Correct credentials return signed three-part JWT | [L27](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L27) |
| US-02/AC-02 | `US-02-T01`: Wrong credentials return 401 without token | [L29](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L29) |
| US-03/AC-01 | `US-03-T01`: Saved preferences round-trip unchanged | [L36](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L36) |
| US-03/AC-02 | `US-03-T01`: Both lists explicitly cleared | [L39](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L39) |
| US-03/AC-03 | `US-07-T01`: Generation receives current saved preferences | [L89](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L89) |
| US-04/AC-01 | `US-04-T01`: Ingredient ID/name and clock-derived addedAt | [L45](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L45) |
| US-04/AC-02 | `US-04-T02`: Blank name rejected without inventory change | [L51](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L51) |
| US-04/AC-03 | `US-04-T01`: Timestamp equals addition clock; no expiry inference | [L45](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L45) |
| US-05/AC-01 | `real account, saved preferences`: Ingredient name and actual saved addition date rendered | [L74](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/frontend/tests/kitchen.spec.js#L74) |
| US-05/AC-02 | `register(page, address`: Explicit empty fridge state after registration; US-05-T01 checks empty API list | [L20](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/frontend/tests/kitchen.spec.js#L20) |
| US-05/AC-03 | `US-05-T01`: Original addition timestamp survives advanced-clock read | [L60](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L60) |
| US-06/AC-01 | `US-06-T01`: Deleting rice leaves unselected tomato | [L78](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L78) |
| US-06/AC-02 | `US-06-T01`: Missing deletion returns 404; subsequent snapshot still tomato | [L79](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L79) |
| US-06/AC-03 | `US-12-T01`: Generation and repeated favorite saves do not deduct stock; US-14-T01 covers views | [L209](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L209) |
| US-07/AC-01 | `US-07-T01`: Provider receives owned ingredients/current dietary and allergen lists | [L89](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L89) |
| US-07/AC-02 | `US-07-T02`: Allergen-conflicting batch rejected with 422 and no saved results | [L126](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L126) |
| US-07/AC-03 | `US-07-T03`: Empty fridge validation prevents provider calls | [L132](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L132) |
| US-07/AC-04 | `US-07-T01`: Generation leaves stock snapshot unchanged | [L90](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L90) |
| US-08/AC-01 | `US-08-T01`: Full details exactly match ingredients/ordered steps/time/calories/servings | [L139](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L139) |
| US-08/AC-02 | `US-08-T02`: Six distinct malformed cases reject whole result with 502; history/stock unchanged | [L156](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L156) |
| US-08/AC-03 | `real account, saved preferences`: Estimate label plus dialog minutes/calories/servings and ingredient/step assertions | [L92](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/frontend/tests/kitchen.spec.js#L92) |
| US-09/AC-01 | `US-09-T01`: Retryable 503 after provider error and unchanged saved collections | [L172](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L172) |
| US-09/AC-02 | `US-09-T01`: All five named collection snapshots unchanged | [L174](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L174) |
| US-09/AC-03 | `test_invalid_provider_response_is_sanitized`: Malformed/incomplete/refused output exposes no provider diagnostics | [L181](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_recipe_integration.py#L181) |
| US-10/AC-01 | `US-10-T01`: Missing onion/tomato added; stocked rice excluded | [L186](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L186) |
| US-10/AC-02 | `US-10-T01`: Case/whitespace normalization avoids existing tomato duplication | [L186](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L186) |
| US-10/AC-03 | `US-10-T01`: Repeat action preserves same shopping IDs | [L187](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L187) |
| US-10/AC-04 | `US-10-T01`: Add missing ingredients leaves fridge unchanged | [L188](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L188) |
| US-11/AC-01 | `US-11-T01`: Created item appears in owned shopping list | [L195](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L195) |
| US-11/AC-02 | `US-11-T01`: Normal removal empties list | [L198](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L198) |
| US-11/AC-03 | `US-11-T01`: Blank name rejected; subsequent empty-list assertion | [L200](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L200) |
| US-11/AC-04 | `US-11-T01`: Normal removal preserves pre-existing stock; does not purchase | [L198](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L198) |
| US-12/AC-01 | `US-12-T01`: Favorite list contains full recipe details | [L208](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L208) |
| US-12/AC-02 | `US-12-T01`: Two saves yield exactly one favorite | [L208](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L208) |
| US-12/AC-03 | `US-12-T01`: Saving favorites preserves stock | [L209](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L209) |
| US-13/AC-01 | `US-12-T01`: Listing returns saved full recipe | [L208](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L208) |
| US-13/AC-02 | `US-13-T01`: Favorite removal empties favorites but retains previously viewed history | [L223](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L223) |
| US-13/AC-03 | `US-13-T01`: Before saving, favorites is empty | [L215](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L215) |
| US-14/AC-01 | `US-14-T01`: Viewed recipe has injected last-viewed timestamp | [L235](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L235) |
| US-14/AC-02 | `US-14-T01`: Generated but unopened recipes absent from history | [L229](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L229) |
| US-14/AC-03 | `US-14-T01`: Exactly two unique IDs, newest first after reopen; updated timestamp | [L234](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L234) |
| US-14/AC-04 | `US-14-T01`: Viewing/reopening never deducts stock | [L236](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L236) |
| US-15/AC-01 | `US-15-T03`: Authentic expired JWT rejected; T01 covers missing/malformed | [L277](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L277) |
| US-15/AC-02 | `US-15-T02`: Foreign read/write operations denied and owner snapshots unchanged | [L262](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/functional/requirements.test.mjs#L262) |
| US-15/AC-03 | `test_unknown_owner_and_empty_fridge_stop_before_provider`: Supplied owner rejected before provider/storage access | [L140](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_recipe_integration.py#L140) |
| NFR-01/Criterion | `test_every_protected_method_rejects_invalid_tokens_without_writes`: Every personal method, both prefixes, invalid JWT variants: denied/no writes/no provider call | [L140](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_security_matrix.py#L140) |
| NFR-02/Criterion | `test_seeded_credentials_absent_from_storage_errors_and_captured_logs`: Salted Argon2id verified; seeded password/JWT/signing/provider markers absent from responses/logs | [L179](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_security_matrix.py#L179) |
| NFR-03/Criterion | `<module>`: 50 users/100 inventory rows each/four GET routes/300 seconds; per-route and aggregate p95<=500ms, errors<1% | [L82](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/performance/non_ai_http.py#L82) |
| NFR-04/Criterion | `test_production_timeout_cancels_stalled_provider_within_thirty_seconds`: 28-second default deadline: cancelled provider, retryable503, five unchanged collections | [L37](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_default_timeout.py#L37) |
| NFR-05/Criterion | `core screens fit ${width}px`: 360/768/1440px: six core pages/headings visible without horizontal overflow | [L203](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/frontend/tests/kitchen.spec.js#L203) |
| NFR-06/Criterion | `core kitchen actions work with keyboard-only input`: Tab/Enter/type-only registration, fridge, preferences, recipes, favorites and shopping | [L237](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/frontend/tests/kitchen.spec.js#L237) |
| NFR-07/Criterion | `test_two_process_restart_preserves_two_users_and_five_collections`: Different write/read processes preserve two accounts and all five collections | [L26](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_process_persistence.py#L26) |
| NFR-08/Criterion | `test_invalid_recipe_rejects_whole_batch`: Single-field invalid numbers/ingredients/steps and declared allergen conflict reject whole batch without partial rows | [L163](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/backend/tests/test_recipe_integration.py#L163) |
| NFR-09/Criterion | `<module>`: Production container/PostgreSQL restart preserves committed resources; actual CI builds/tests it | [L75](https://github.com/SarpCizer/CMPE331-Project/blob/93d60d0c425f2ba1b6e61d13b03db484982be0b5/tests/cloud/smoke.py#L75) |

## Non-functional scope

- **NFR-01:** OpenAPI matrix completeness and foreign-ID parameterized cases are separate tests in the same file.
- **NFR-02:** Seeded-marker inspection and repository secret scan do not certify external platform logs.
- **NFR-03:** Evaluate actual named environment only. Older local/CI numbers have distinct source SHAs.
- **NFR-04:** Additional generation load checks five concurrent deadlines/no partial persisted recipes; not live inference.
- **NFR-05:** Completion browser cases separately cover validation and unavailable states at all three widths.
- **NFR-06:** Axe labels/error associations and explicit focus tests supplement automated walkthrough; no human usability audit claimed.
- **NFR-07:** SQLite and PostgreSQL parameters; PostgreSQL requires TEST_DATABASE_URL and any skipped variant must be disclosed.
- **NFR-08:** Browser US-08 mappings verify estimate labels/list review; nutrition truth and undeclared allergens outside fixture evidence.
- **NFR-09:** Historical HTTPS smoke is source a59556e. This fix branch is not claimed deployed; no production scan/load.

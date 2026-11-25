# Requirement traceability

Denominator: 15 stories and 48 acceptance criteria in the repository requirements. 
All 48 criteria have assertion mappings; the detailed CSV preserves each criterion. 
Passing claims refer to the recorded runs and their controlled-provider/SQL/browser scope. 
This is separate from code coverage and does not establish live AI, staging or hidden-allergen safety.

| Story | Criteria | Assertion mapping |
|---|---:|---|
| US-01 | 3 | US-01-T01; US-01-T02 |
| US-02 | 2 | US-02-T01; B-AUTH-05; US-02-T01; B-AUTH-04 |
| US-03 | 3 | US-03-T01; B-PREF-01; US-07-T01; test_real_accounts_supply_owned_inventory_and_latest_preferences |
| US-04 | 3 | US-04-T01; US-04-T02; US-04-T01; test_inventory_isolation_and_immutable_addition_time |
| US-05 | 3 | US-05-T01; browser real-account flow; US-05-T01; browser empty-fridge flow; US-05-T01 |
| US-06 | 3 | US-06-T01; US-12-T01; US-14-T01 |
| US-07 | 4 | US-07-T01; US-07-T02; US-07-T03; browser empty-fridge flow |
| US-08 | 3 | US-08-T01; browser real-account flow; US-08-T02..T07; browser real-account flow (estimate label and displayed ingredients) |
| US-09 | 3 | US-09-T01; test_production_timeout_cancels_stalled_provider_within_thirty_seconds; browser provider-failure flow; US-09-T01; test_real_accounts_supply_owned_inventory_and_latest_preferences; test_invalid_provider_response_is_sanitized; US-09-T01 |
| US-10 | 4 | US-10-T01 |
| US-11 | 4 | US-11-T01 |
| US-12 | 3 | US-12-T01 |
| US-13 | 3 | US-13-T01 |
| US-14 | 4 | US-14-T01 |
| US-15 | 3 | US-15-T01; US-15-T03; B-SEC-01; B-SEC-02; B-SEC-05; US-15-T02; B-SEC-03; B-SEC-04; B-SEC-04; test_unknown_owner_and_empty_fridge_stop_before_provider; test_inventory_isolation_and_immutable_addition_time |

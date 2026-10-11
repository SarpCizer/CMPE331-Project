# Requirement to test traceability

Each story has at least one executable functional test. IDs are included in test names. Tests exercise acceptance behavior through the unimplemented application boundary; browser presentation criteria additionally need UI checks.

| Story | Requirement | Executable cases | Additional verification |
|---|---|---|---|
| [US-01](US-01.md) | Register an account | US-01-T01, US-01-T02 | NFR checks as relevant |
| [US-02](US-02.md) | Sign in | US-02-T01 | NFR checks as relevant |
| [US-03](US-03.md) | Save dietary and allergen preferences | US-03-T01 | NFR checks as relevant |
| [US-04](US-04.md) | Add fridge ingredients manually | US-04-T01, US-04-T02 | NFR checks as relevant |
| [US-05](US-05.md) | List ingredients and their addition dates | US-05-T01 | UI labels/empty states; NFR checks |
| [US-06](US-06.md) | Delete fridge ingredients manually | US-06-T01 | NFR checks as relevant |
| [US-07](US-07.md) | Generate recipes using the fridge and preferences | US-07-T01, US-07-T02, US-07-T03 | NFR checks as relevant |
| [US-08](US-08.md) | View recipe details | US-08-T01, US-08-T02, US-08-T03, US-08-T04, US-08-T05, US-08-T06, US-08-T07 | UI labels/empty states; NFR checks |
| [US-09](US-09.md) | Handle recipe service failures | US-09-T01 | UI labels/empty states; NFR checks |
| [US-10](US-10.md) | Add missing recipe ingredients in one action | US-10-T01 | NFR checks as relevant |
| [US-11](US-11.md) | Manage the shopping list | US-11-T01 | NFR checks as relevant |
| [US-12](US-12.md) | Save a favorite recipe | US-12-T01 | NFR checks as relevant |
| [US-13](US-13.md) | List and remove favorite recipes | US-13-T01 | UI labels/empty states; NFR checks |
| [US-14](US-14.md) | Keep previously viewed recipes | US-14-T01 | NFR checks as relevant |
| [US-15](US-15.md) | Protect personal data | US-15-T01, US-15-T02, US-15-T03 | NFR checks as relevant |

Functional suite: [requirements.test.mjs](../../tests/functional/requirements.test.mjs). Quality cases: [non-functional.md](non-functional.md). A story having a test does not mean all its criteria are automated or implemented.

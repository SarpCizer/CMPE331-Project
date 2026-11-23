# Implemented database and transaction contract

Refs #16, #17, #18, #19, #20, #21. PostgreSQL 17 is the shared/cloud target; SQLite >= 3.35 is supported for isolated development. Alembic is the only schema release path: `python -m fridgely_app migrate`. App imports do not create/reset tables. Back up shared data before schema changes.

| Analysis entity | Physical relation / invariant |
| --- | --- |
| ACCOUNT | `accounts`: opaque ID, unique normalized email, salted Argon2id hash and UTC creation time. Registration normalizes with email-validator; an additional unique `lower(email)` index rejects case variants at the database boundary. |
| DIETARY_PREFERENCE | `dietary_preferences`: `(owner_id, position)` primary key; exact `display_value`, nonunique derived `value_key`. |
| ALLERGEN_EXCLUSION | `allergen_exclusions`: same ordered structure; repeated and differently cased values remain separate list entries. |
| Preference owner | `account_preferences`: one row per account, parent of both ordered lists; no JSON shadow copy remains. |
| INVENTORY_ENTRY | `inventory_entries`: owned name and immutable server UTC addition time. Matching keys are derived from names; addition time is not an expiry date. |
| RECIPE | `recipes`: owned accepted snapshot, unique `(owner_id,id)`, positive time/servings, nonnegative calories. Strict numeric and complete-child validation occurs before persistence. |
| RECIPE_INGREDIENT / RECIPE_STEP | `recipe_ingredients` / `recipe_steps`: `(recipe_id,position)` keys preserve order; only reconstructed through an owned recipe. |
| SHOPPING_ENTRY | `shopping_items`: unique `(owner_id,name_key)`; stable ID and display name on repeated actions. |
| FAVORITE / RECIPE_VIEW | `favorites` / `recipe_views`: `(owner_id,recipe_id)` keys and composite foreign keys to the same owner's recipe. Removing a favorite cannot cascade to its parent recipe or history. |

Migration `0002_ordered_preferences` copies each JSON list from `0001_owned_schema` into indexed ordered rows before removing the old JSON columns. It preserves exact strings, order and repeated entries. Re-running upgrade at head is a no-op. The downgrade reconstructs the old arrays in position order. Constraints reject duplicate positions and missing owners. All preference writes still accept and return `{dietary:[],allergens:[]}`, so existing teammates' ports and the frontend API remain compatible.

| Operation | Commit boundary |
| --- | --- |
| Register | Account and empty preference owner together; uniqueness violations become 409 after rollback. Concurrent case variants produce one account. |
| Replace preferences | Both complete ordered lists in one SQLAlchemy transaction; empty input deletes prior rows. Derived keys do not replace returned values. |
| Generate | Read current owner-scoped input; PostgreSQL generation uses REPEATABLE READ for its input snapshot. Validate the entire provider batch before inserting recipes and ordered children in one transaction. |
| Add missing ingredients | Normalize recipe/inventory names, insert missing owned shopping items under a unique owner/name key, commit before replying. |
| Save/remove favorite | Owned recipe association only; idempotent save and isolated removal. |
| Open recipe details | Owner-qualified recipe lookup and committed history upsert before the successful HTTP response. |

HTTP identities always come from verified JWT subjects, never caller-supplied owner fields. No generation, detail, favorite, history or shopping operation changes inventory. The new tests record a genuine red-to-green implementation sequence in the PR; prior feature work is not retroactively described as tests-first.

The preference reader now returns both ordered lists with one owner-qualified
`UNION ALL` statement. This gives a profile read one statement snapshot on
PostgreSQL and avoids the previous parent lookup plus two lazy relationship
queries. Exact display strings, repeated entries and position order are retained;
an absent/empty profile produces two empty lists. The API and recipe input reader
share this function. The separate write transaction still atomically replaces
both arrays. SQLite and PostgreSQL regressions enforce the single-query boundary,
ordering and owner isolation. Refs #20, #43, #62.

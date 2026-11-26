# Fridgely HTTP API

The React website calls the real FastAPI application at `/api`. The same application also implements the original root-path acceptance contract. Swagger UI is available at `/api/docs` (or `/docs`); its OpenAPI 3 schema is `/api/openapi.json`. Documentation assets are bundled locally, with no CDN or external schema validator. Use the **API documentation** link on the sign-in page or application footer.

1. `POST /api/accounts` with `{"email":"you@example.com","password":"a-long-password"}` creates an account (201). Passwords require at least eight characters and are stored with Argon2id.
2. `POST /api/sessions` with the same body returns `{"token":"..."}` (200). Paste the token into Swagger's **Authorize** dialog. Do not include the word `Bearer` in that dialog.
3. Protected operations use `Authorization: Bearer <token>`. Tokens expire after one hour. Swagger does not persist authorization across page reloads.

| Resource | Operations |
| --- | --- |
| `/api/accounts`, `/api/sessions` | Register and sign in |
| `/api/profile/preferences` | GET / PUT dietary preferences and excluded ingredients |
| `/api/inventory` | GET / POST fridge ingredients with server timestamps and optional quantity/unit pairs |
| `/api/inventory/{item_id}` | PATCH an owned quantity/unit pair or DELETE an owned ingredient |
| `/api/recipes/generate` | POST recipes based on the authenticated user's current fridge and preferences |
| `/api/recipes/{recipe_id}` | GET an owned recipe and update viewing history |
| `/api/recipes/{recipe_id}/shopping-items` | POST absent or insufficient ingredients to the owned shopping list |
| `/api/shopping-items` | GET / POST shopping items with optional quantity/unit |
| `/api/shopping-items/{item_id}` | DELETE an owned shopping item |
| `/api/shopping-items/{item_id}/purchase` | POST confirmed bought quantity; atomically refill fridge and remove the item |
| `/api/favorites`, `/api/favorites/{recipe_id}` | GET / POST favorites; DELETE an owned favorite |
| `/api/history` | GET viewing history |
| `/api/health` | GET database readiness; 200 when connected, 503 when unavailable |

Generated recipes include `ingredientAmounts`, one display measurement for each
entry in `ingredients` in the same order. The ingredient names still drive
allergen validation and shopping-list matching. Older recipes omit this field
when their measurements are unknown.

Validation errors return a sanitized `{"error":"..."}` with HTTP 400. Invalid/expired tokens return 401; another user's resource returns 404; duplicate accounts return 409. Recipe generation rejects an empty fridge (400), invalid provider output (502) and excluded ingredients (422). Missing provider configuration, an outage or the 28-second provider deadline returns 503 with `retryable: true`. Failed generation leaves stored collections unchanged. The interactive schema documents request and response models and these errors.

The [selected recipe provider's credentials](cloud-deployment.md#recipe-provider-settings) belong in server environment settings. Accounts, inventory, preferences, shopping, existing favorites and history remain available when generation reports a provider failure. The isolated test server uses controlled recipe fixtures.

## Manual fridge quantities

Refs #77, #78. `POST /api/inventory` accepts `name` plus an optional `quantity`/`unit` pair. `PATCH /api/inventory/{item_id}` requires both fields and updates only the authenticated owner's entry; its name, ID and addition date stay unchanged. Quantity must be finite, greater than zero and at most 1,000,000. Units are `pcs`, `kg`, `g`, `L`, `ml`, `pack` and `bunch`; `pcs`, `pack` and `bunch` require whole numbers.

Both fields are null when the amount is unknown, including existing entries upgraded by migration `0003_inventory_quantities`. No amount is invented during migration. Known amounts are included in the server-side AI input; recipe ingredient names retain their matching contract. Measurable shortages are also checked when adding missing shopping ingredients (see below). Recipe generation/viewing and shopping/favorite actions never deduct or recalculate fridge quantities.

## Confirm cooking and restock (user-approved extension #81)

New provider output uses positive numeric `g`, `kg`, `ml`, `L`, `pcs`, `pack` or `bunch` measurements, e.g. `200 ml`, instead of cups/spoons. Legacy recipe measurements remain readable. The UI converts only kg/g or L/ml (and matching count units); ambiguous or cross-dimension amounts require the user's entry. No density conversion is assumed.

`POST /api/recipes/{recipe_id}/cook` accepts `{requestId, items: [{inventoryId, quantity, unit}]}` after the user selects **I cooked this**, reviews actual amounts for the displayed serving count and confirms. Deductions use the inventory entry's unit. Unknown/missing stock is explicitly reported rather than guessed. Zero in the confirmation skips an ingredient. Recipe viewing, generating, history, favorites and shopping actions still do not deduct stock.

Each item must belong to the authenticated user and match a recipe ingredient. The transaction rejects duplicate entries, nonpositive/nonfinite quantities, fractional count units, changed units, insufficient or concurrently changed stock. All updates and the durable confirmation commit together. Retrying an identical owner-scoped request ID does not deduct again, including after a lost response/restart; reusing it for different input returns 409. An intentional later cooking uses a new request ID. Stock can reach zero but cannot become negative through cooking. `PATCH /inventory/{id}` now permits zero for manual correction/refilling; new inventory quantities remain positive.

Zero entries retain IDs, names and addition timestamps, display red **Out of stock** text, and offer **Add to shopping list** via the existing deduplicated `/shopping-items` endpoint. They are excluded from recipe generation and from present-ingredient matching. Refilling restores their availability. This extension is explicitly requested by Berfin; original course reports/PDF and release tag are preserved.

A pending cooking confirmation stores its complete original body before submission. After a lost/uncertain response and a reload, **Retry previous confirmation** resends that body before considering refreshed stock. A zero entry is never omitted from an outstanding retry. Starting a new cooking remains unavailable until the previous outcome is reconciled. A definitive validation/stock conflict permits reviewing a fresh confirmation; uncertain network/server failures keep the original pending operation.


## Missing and insufficient shopping ingredients (#83)

**Add missing ingredients** works from generated recipes, saved favorites and history. The server reads current owned stock, so a saved recipe needing `2 pcs` banana with `1 pcs` in the fridge adds banana to shopping. Entirely absent and zero-stock ingredients are also added; sufficient ingredients are excluded. Compatible g/kg and ml/L measurements and identical count units are summed across duplicate stock and recipe entries using decimal arithmetic. The comparison uses the saved recipe amounts for its displayed serving count, not edited cooking inputs.

Legacy recipes without measurements, unknown fridge quantities and incompatible units retain name-based presence behavior; no cup/density/weight conversion is guessed. Measured recipe additions carry the actual deficit and unit; manual additions can carry a planned quantity. Unknown legacy measurements remain name-only. Repeated additions do not duplicate a product. Shopping entries persist across reload and can be removed after purchase. Ordinary shopping additions/removals do not change fridge stock. The explicit confirmed-purchase extension below transfers the actual bought amount. No schema migration is needed.


## Shopping amounts and confirmed purchases (user-approved extension #85)

`POST /api/shopping-items` accepts `name` plus an optional positive finite `quantity`/`unit` pair, at most 1,000,000. Units match fridge entry: pcs, g, kg, ml, L, pack and bunch; count units require whole numbers. Unknown amounts remain omitted in responses, preserving old name-only clients and rows. Re-adding a normalized name with an explicit amount replaces its shopping amount, never increments it. Name-only/manual additions preserve an existing amount. Measured recipe additions ensure at least the current deficit without accumulating repeated clicks or reducing a larger compatible amount.

**Bought — add to fridge** opens a review of the amount actually purchased (which may differ from the planned amount). `POST /api/shopping-items/{item_id}/purchase` requires that positive amount and unit. After confirmation, one transaction records a durable owner/item receipt, adds to compatible known stock or creates a new known inventory row, and removes the shopping item. g/kg and ml/L convert; matching count units combine. Unknown or incompatible stock stays separate. Refilling a depleted row preserves its ID/date. Exceeding a fridge quantity limit returns409 without changing either collection. The entire shopping item leaves the list even if the confirmed amount differs from the plan.

Each shopping item can be purchased once. Replaying the same item/amount after a lost response or reconnect returns success without adding again; a different amount on that completed item returns409. Concurrent confirmations cannot refill twice. Retrying the original confirmation is safe; a reload also shows the committed fridge/list state. **Cancel purchase** sends no write. Ordinary **Remove** only deletes the shopping item and never adds stock (the original US11 behavior). Only this new explicit confirmed action transfers stock. Ownership, sanitized errors and commit-before-success apply at both root and /api routes.

Migration `0006_shopping_quantities` adds nullable shopping amount columns and a purchase receipt table; existing names, IDs, owners and unknown amounts are preserved. No provider, billing or historical course-report artifacts are changed. Version0.3.0.


The collections overlay compatibility fixture is pinned to `b58f4f298091dad47486c6d29d49586de83c63ee`: current production host `a06303e` plus only the required0006 database migration. The old frozen929776c fixture has no shopping amount columns and cannot exercise this schema extension. The fixture contains no new purchase endpoint/frontend; the overlay continues to hash and protect all teammate source. Already-shared identical test files are retained rather than overwritten; differing existing tests are rejected. This separately checks the module against the prior host with the required storage upgrade, while integrated CI checks the complete new application.


## Measured recipe deficits in shopping (#85/#86 extension)

**Add missing ingredients** on a generated, saved or favorite recipe compares its full displayed serving quantities with fresh owned stock in the shopping transaction. For example, a recipe requiring2 pcs banana with1 pcs in the fridge adds1 pcs;200 ml milk with0.1 L in stock adds100 ml. Entirely absent or depleted ingredients use the full required amount. Duplicate compatible stock rows and recipe requirements are summed with decimal arithmetic before subtraction. Adding to shopping never changes stock or calls the AI provider.

Mass uses g/kg, volume uses ml/L, and matching pcs/pack/bunch units are comparable; no cup, package-size or density guesses are made. Unknown stock or incompatible recipe/stock dimensions retain the prior name-presence fallback. Unknown or ambiguous absent-ingredient measurements are added name-only for manual review. Values too large for the bounded amount fields also remain name-only.

Automatic additions fill an unknown shopping amount and ensure the maximum of an existing compatible planned amount and the new deficit. They never sum repeated requests or reduce an already larger amount. A previously entered incompatible shopping unit is preserved for review. Manual re-addition with an explicit amount still replaces the planned amount intentionally. The optional read-only shopping-shortages callback preserves older collection integrations, which continue using names when no quantity adapter is provided. No additional database migration is needed beyond0006.

The **Bought — add to fridge** review defaults to this computed missing quantity. The user can confirm the actual purchased amount, which is transferred atomically with the durable purchase receipt and shopping removal; the #87 SQLite overlap fix is retained.


## Weekly meal planner (#88)

All operations require the verified JWT subject and are also available at the
original root paths. `weekStart` is an ISO Monday date. Day indexes are 0–6.
User-added slot keys `dish-1` through `dish-20` identify independently planned
dishes, with no fixed meal categories. Each dish has an integer `servings` of
1–20. The frontend sends the user's local Monday for every operation.

| Route | Behavior |
| --- | --- |
| `GET /api/weekly-plan?weekStart=2026-11-23` | Owned week, including recipes, ordered steps, planned servings and scaledAmounts |
| `GET /api/weekly-plan/recipes` | Up to 100 owned saved/generated recipes for reuse, ordered by title and ID |
| `PUT /api/weekly-plan/{day}/{meal}` | `{weekStart, recipeId, servings}` saves an owned recipe in one slot |
| `DELETE /api/weekly-plan/{day}/{meal}?weekStart=2026-11-23` | Clears one owned slot, preserving a revision against stale generation |
| `POST /api/weekly-plan/{day}/{meal}/generate` | `{weekStart, dish, servings}` creates a requested recipe and atomically saves its slot |
| `POST /api/weekly-plan/shopping-items` | `{weekStart}` scales and aggregates all dishes, subtracts stock once, adds deficits |

Typed dishes use the existing configured provider with current dietary/allergen
preferences, requested name and exact portions. An empty fridge is allowed here:
the plan may require shopping. Provider calls happen outside SQL transactions;
invalid, excluded, timed-out or unavailable results never partially save a recipe
or replace the prior plan. A slot changed during generation returns 409 and the
UI refreshes the saved week. A valid recipe and slot commit together before 200.
Selecting or rescaling saved recipes does not call the provider.

Shopping uses exact fractional arithmetic for portion scaling before subtracting
owned stock. Compatible g/kg, ml/L and matching count units are combined. Whole
items are rounded up once after aggregating the week; mass/volume deficits round
up to 0.001 of the selected shopping unit. Unknown or incompatible measurements
are returned in `needsReview`; missing unknown amounts remain name-only. Larger
existing shopping amounts are kept. Repeating the same request is not additive.
Changing/removing a plan does not automatically delete old shopping entries.
Planning never reserves or deducts fridge stock, and does not mark dishes cooked.

Migration `0007_weekly_meal_plans` adds only the owner/week/day/slot table, composite
owner/recipe FK, portion and slot constraints and revisioned cleared slots. It
preserves existing accounts, inventory, recipes, favorites and shopping rows.

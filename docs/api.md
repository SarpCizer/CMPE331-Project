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
| `/api/recipes/{recipe_id}/shopping-items` | POST missing ingredients to the owned shopping list |
| `/api/shopping-items` | GET / POST shopping items |
| `/api/shopping-items/{item_id}` | DELETE an owned shopping item |
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

Both fields are null when the amount is unknown, including existing entries upgraded by migration `0003_inventory_quantities`. No amount is invented during migration. Known amounts are included in the server-side AI input; recipe ingredient names and name-based missing-shopping matching retain their contract. Recipe generation/viewing and shopping/favorite actions never deduct or recalculate fridge quantities.

## Confirm cooking and restock (user-approved extension #81)

New provider output uses positive numeric `g`, `kg`, `ml`, `L`, `pcs`, `pack` or `bunch` measurements, e.g. `200 ml`, instead of cups/spoons. Legacy recipe measurements remain readable. The UI converts only kg/g or L/ml (and matching count units); ambiguous or cross-dimension amounts require the user's entry. No density conversion is assumed.

`POST /api/recipes/{recipe_id}/cook` accepts `{requestId, items: [{inventoryId, quantity, unit}]}` after the user selects **I cooked this**, reviews actual amounts for the displayed serving count and confirms. Deductions use the inventory entry's unit. Unknown/missing stock is explicitly reported rather than guessed. Zero in the confirmation skips an ingredient. Recipe viewing, generating, history, favorites and shopping actions still do not deduct stock.

Each item must belong to the authenticated user and match a recipe ingredient. The transaction rejects duplicate entries, nonpositive/nonfinite quantities, fractional count units, changed units, insufficient or concurrently changed stock. All updates and the durable confirmation commit together. Retrying an identical owner-scoped request ID does not deduct again, including after a lost response/restart; reusing it for different input returns 409. An intentional later cooking uses a new request ID. Stock can reach zero but cannot become negative through cooking. `PATCH /inventory/{id}` now permits zero for manual correction/refilling; new inventory quantities remain positive.

Zero entries retain IDs, names and addition timestamps, display red **Out of stock** text, and offer **Add to shopping list** via the existing deduplicated `/shopping-items` endpoint. They are excluded from recipe generation and from present-ingredient matching. Refilling restores their availability. This extension is explicitly requested by Berfin; original course reports/PDF and release tag are preserved.

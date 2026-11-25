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

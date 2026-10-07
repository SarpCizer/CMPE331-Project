# Proposed acceptance API contract

This is a test boundary proposal for review, not an implemented API. Production framework choices remain open. Protected routes derive the owner from the JWT. Errors use `{ error: string }`; provider service failures also return `retryable: true`. Responses below specify the body directly, without an envelope. Validation failures are 400; missing resources 404; unauthenticated requests 401; foreign resources 403 or 404. Mutations must be atomic on error.

| Method and route | Request | Expected response |
|---|---|---|
| POST /accounts | email, password | 201 `{id,email}`; 409 duplicate; no password/hash exposed |
| POST /sessions | email, password | 200 `{token}`; 401 wrong credentials |
| GET /profile/preferences | none | 200 `{dietary:[],allergens:[]}` |
| PUT /profile/preferences | dietary and allergens string arrays | 200 saved preference object |
| GET /inventory | none | 200 ingredient array |
| POST /inventory | `{name}` | 201 `{id,name,addedAt}` |
| DELETE /inventory/:id | none | 204 |
| POST /recipes/generate | empty object | 200 recipe array; 400 empty fridge; 422 declared allergen conflict; 502 malformed output; 503 unavailable/timeout |
| GET /recipes/:id | none | 200 recipe object; records view |
| POST /recipes/:id/shopping-items | empty object | 200 resulting shopping-item array |
| GET /shopping-items | none | 200 shopping-item array |
| POST /shopping-items | `{name}` | 201 `{id,name}` for a new item |
| DELETE /shopping-items/:id | none | 204 |
| POST /favorites | `{recipeId}` | 200 recipe object, including repeated saves |
| GET /favorites | none | 200 recipe array |
| DELETE /favorites/:recipeId | none | 204; viewed history unaffected |
| GET /history | none | 200 `[{recipe,lastViewedAt}]`, newest first |

A recipe is `{id,title,ingredients:string[],steps:string[],cookingMinutes,caloriesPerServing,servings}`. Cooking time is positive, calories nonnegative and serving count a positive integer. All accepted recipes belong to the requesting account. Provider-generated IDs are test fixture IDs; the production service should allocate safe internal IDs and isolate them by account.

The injected provider implements `generate({ingredients,dietary,allergens})` and returns recipe candidates. The injected clock returns a UTC ISO 8601 timestamp. Validate the entire batch before persisting; a declared allergen conflict returns 422 with no partial recipes saved. At minimum, compare normalized declared ingredient names against the normalized allergen vocabulary; the final taxonomy and synonym strategy require review. Mock-provider tests are supplemented by later live-service checks.

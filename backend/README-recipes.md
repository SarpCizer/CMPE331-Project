# Fridgely recipe generation

This module implements US-07, the data contract for US-08, and US-09. It uses the same FastAPI, SQLAlchemy, verified account type and recipe response schema as the collections module on `backend_work`. The existing recipe detail route in collections owns view history.

## Connect to the shared backend

Install HTTPX alongside the backend's runtime dependencies. The integration test lock file on `backend_work` already includes HTTPX. Create and close the shared `httpx.AsyncClient(timeout=28.0)` in the host application's lifespan. Set `OPENAI_API_KEY` in the server environment. `OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`.

Use the same session factory, inventory reader and verified account dependency for both modules. The inventory reader returns ingredient names for the given owner. The preferences reader returns a pair of sequences, dietary choices followed by allergen exclusions. Both readers use the supplied session.

```python
from fridgely_collections import CoreCallbacks, build_collections
from fridgely_recipes.api import build_recipes
from fridgely_recipes.provider import OpenAIRecipeProvider

recipes = build_recipes(
    session_factory=SessionLocal,
    require_account=require_verified_account,
    inventory_lookup=inventory_names,
    preferences_lookup=read_preferences,
    provider=OpenAIRecipeProvider(http_client),
)
collections = build_collections(
    session_factory=SessionLocal,
    require_account=require_verified_account,
    core=CoreCallbacks(
        recipe_lookup=recipes.store.find_owned,
        inventory_lookup=inventory_names,
    ),
)
app.include_router(recipes.router)
app.include_router(collections.router)
```

Both routes expect `require_verified_account` to return Sarp's `AccountPrincipal` after token verification. `POST /recipes/generate` reads a snapshot and closes its read session before calling OpenAI. It validates the whole batch before committing recipes, ingredients and steps in a single transaction. Collections looks up the committed recipe by both owner and recipe ID using its existing session. That lookup performs no writes or commits.

The route accepts an empty command object. It returns a full recipe array on 200, 400 for an empty fridge, 422 for a declared ingredient that matches an allergen exclusion, 502 for invalid output, and a retryable 503 for provider failure or timeout. Matching uses trimmed case-insensitive names. Production migrations must add the three recipe tables and connect their ownership constraints with the shared account, favorites and history schema. `create_recipe_schema` is available for explicit local setup.

## Run the integration checks

For an isolated checkout that combines both feature branches without publishing a merge:

```powershell
git fetch origin
git worktree add --detach ../fridgely-recipe-integration origin/ayse/recipe-ai
Set-Location ../fridgely-recipe-integration
git merge --no-commit --no-ff origin/backend_work
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-test.lock
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

The tests mount both FastAPI routers over a shared SQLite database. They verify recipe generation, persistence, owner isolation, and the use of generated recipes in detail, history, favorites and shopping routes. Provider responses, preferences and token checks use fixtures. Live OpenAI, real JWT verification, the production PostgreSQL migration and browser checks are separate integration steps.

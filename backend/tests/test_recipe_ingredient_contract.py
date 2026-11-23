"""US-07/09/10: every accepted recipe must support owned shopping actions."""
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app
from fridgely_recipes.storage import Recipe, RecipeIngredient, RecipeStep

RECIPE = {
    "title": "Tomato rice", "ingredients": ["rice", "tomato"],
    "steps": ["Cook rice", "Add tomato"], "cookingMinutes": 20,
    "caloriesPerServing": 325, "servings": 2,
}
PERSONAL_PATHS = ("/inventory", "/profile/preferences", "/shopping-items", "/favorites", "/history")


@pytest.fixture(params=["sqlite", "postgresql"])
def ingredient_host(tmp_path, request):
    url = (f"sqlite:///{tmp_path / 'ingredients.db'}" if request.param == "sqlite"
           else os.getenv("TEST_DATABASE_URL"))
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for the PostgreSQL ingredient contract check")
    engine = make_engine(url)
    try:
        migrate(engine)
    finally:
        engine.dispose()
    state = SimpleNamespace(candidates=[RECIPE.copy()])

    class Provider:
        async def generate(self, _data):
            return state.candidates

    app = create_app(database_url=url,
        jwt_secret="ingredient-contract-test-only-signing-key-at-least-32-bytes",
        recipe_provider=Provider())
    with TestClient(app) as client:
        credentials = {"email": f"ingredient-{uuid4().hex}@example.test",
                       "password": "Ingredient-Contract-Password!"}
        registered = client.post("/accounts", json=credentials)
        assert registered.status_code == 201
        signed_in = client.post("/sessions", json=credentials)
        assert signed_in.status_code == 200
        headers = {"Authorization": f"Bearer {signed_in.json()['token']}"}
        assert client.post("/inventory", headers=headers, json={"name": "rice"}).status_code == 201
        preferences = {"dietary": ["vegan"], "allergens": ["peanut"]}
        assert client.put("/profile/preferences", headers=headers, json=preferences).status_code == 200

        def counts():
            with app.state.sessions() as session:
                owner = registered.json()["id"]
                return (
                    session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id == owner)),
                    session.scalar(select(func.count()).select_from(RecipeIngredient).join(Recipe).where(Recipe.owner_id == owner)),
                    session.scalar(select(func.count()).select_from(RecipeStep).join(Recipe).where(Recipe.owner_id == owner)),
                )

        yield SimpleNamespace(client=client, headers=headers, state=state, counts=counts)


@pytest.mark.parametrize("unsupported", [
    "a" * 257, "green\nonion", "rice\x00milk", "\u0390" * 256,
], ids=["overlong-display", "embedded-newline", "embedded-null", "overlong-casefold-key"])
@pytest.mark.parametrize("invalid_first", [False, True], ids=["invalid-last", "invalid-first"])
def test_invalid_ingredient_rejects_entire_batch_without_changing_owned_data(
        ingredient_host, unsupported, invalid_first):
    h = ingredient_host
    initial = h.client.post("/recipes/generate", headers=h.headers, json={})
    assert initial.status_code == 200
    recipe = initial.json()[0]
    detail = f"/recipes/{recipe['id']}"
    assert h.client.get(detail, headers=h.headers).status_code == 200
    assert h.client.post("/favorites", headers=h.headers, json={"recipeId": recipe["id"]}).status_code == 200
    assert h.client.post(f"{detail}/shopping-items", headers=h.headers, json={}).status_code == 200
    before = [h.client.get(path, headers=h.headers).json() for path in PERSONAL_PATHS]
    before_counts = h.counts()
    invalid = {**RECIPE, "ingredients": ["rice", unsupported]}
    h.state.candidates = [invalid, RECIPE.copy()] if invalid_first else [RECIPE.copy(), invalid]

    response = h.client.post("/recipes/generate", headers=h.headers, json={})

    assert response.status_code == 502
    assert response.json() == {"error": "The recipe service returned an invalid response."}
    assert h.counts() == before_counts == (1, 2, 2)
    assert [h.client.get(path, headers=h.headers).json() for path in PERSONAL_PATHS] == before


@pytest.mark.parametrize("name", ["a" * 256, "\u00df" * 256], ids=["display-boundary", "casefold-key-boundary"])
def test_valid_boundary_ingredient_survives_generation_and_idempotent_shopping(ingredient_host, name):
    h = ingredient_host
    h.state.candidates = [{**RECIPE, "ingredients": ["rice", name]}]
    before = h.client.get("/inventory", headers=h.headers).json()
    generated = h.client.post("/recipes/generate", headers=h.headers, json={})
    assert generated.status_code == 200
    recipe = generated.json()[0]
    assert recipe["ingredients"] == ["rice", name]
    path = f"/recipes/{recipe['id']}/shopping-items"
    first = h.client.post(path, headers=h.headers, json={})
    assert first.status_code == 200
    assert [item["name"] for item in first.json()] == [name]
    again = h.client.post(path, headers=h.headers, json={})
    assert again.status_code == 200 and again.json() == first.json()
    assert h.client.get("/inventory", headers=h.headers).json() == before
    assert h.counts() == (1, 2, 2)

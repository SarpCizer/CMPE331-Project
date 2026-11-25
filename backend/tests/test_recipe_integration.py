import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from fridgely_collections import CoreCallbacks, RecipeDTO, build_collections
from fridgely_recipes.api import build_recipes
from fridgely_recipes.provider import OpenAIRecipeProvider
from fridgely_recipes.storage import Recipe, RecipeIngredient, RecipeStep, create_recipe_schema

RECIPE = {
    "title": "Tomato rice",
    "ingredients": ["rice", "tomato"],
    "ingredientAmounts": ["1 cup", "2 medium"],
    "steps": ["Cook the rice", "Add the tomato"],
    "cookingMinutes": 20,
    "caloriesPerServing": 325,
    "servings": 2,
}


def output(*recipes):
    return httpx.Response(200, json={
        "status": "completed",
        "output": [{
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": json.dumps({"recipes": list(recipes)})}],
        }],
    })


@pytest.fixture
def recipe_app(h):
    create_recipe_schema(h.engine)
    state = SimpleNamespace(
        empty=False, requests=[], response_factory=lambda: output(RECIPE),
        stalled=False, provider_cancelled=False, preferences=(["vegan"], ["peanut"]),
    )

    async def respond(request):
        state.requests.append(request)
        if state.stalled:
            try:
                await asyncio.sleep(60)
            finally:
                state.provider_cancelled = True
        return state.response_factory()

    wire = httpx.AsyncClient(transport=httpx.MockTransport(respond))

    @asynccontextmanager
    async def lifespan(_app):
        async with wire:
            yield

    def inventory_lookup(session, owner):
        return [] if state.empty else h.core.inventory_lookup(session, owner)

    def preferences_lookup(_session, owner):
        return state.preferences if owner == "1" else ([], [])

    module = build_recipes(
        session_factory=h.sessions,
        require_account=h.auth,
        inventory_lookup=inventory_lookup,
        preferences_lookup=preferences_lookup,
        provider=OpenAIRecipeProvider(wire, api_key="test-provider-key", model="gpt-4o-mini"),
        timeout_seconds=0.1,
    )
    collections = build_collections(
        session_factory=h.sessions,
        require_account=h.auth,
        core=CoreCallbacks(module.store.find_owned, inventory_lookup),
        clock=h.clock,
    )
    app = FastAPI(lifespan=lifespan)
    app.include_router(module.router)
    app.include_router(collections.router)

    def counts():
        with h.sessions() as session:
            return tuple(session.scalar(select(func.count()).select_from(model))
                         for model in (Recipe, RecipeIngredient, RecipeStep))

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client, state=state, counts=counts, store=module.store,
            alice=h.alice, bob=h.bob, snapshot=h.snapshot,
        )


def generate(a, **kwargs):
    return a.client.post("/recipes/generate", headers=a.alice, **kwargs)


def test_generated_recipe_is_shared_with_collections_but_is_private(recipe_app):
    a = recipe_app
    inventory = a.snapshot()
    response = generate(a, json={})
    assert response.status_code == 200
    recipe, = response.json()
    assert recipe == {**RECIPE, "id": recipe["id"]}
    assert a.counts() == (1, 2, 2)
    assert a.snapshot() == inventory

    request, = a.state.requests
    assert str(request.url) == "https://api.openai.com/v1/responses"
    assert request.headers["Authorization"] == "Bearer test-provider-key"
    body = json.loads(request.content)
    assert json.loads(body["input"]) == {"ingredients": [" RICE "], "dietary": ["vegan"], "allergens": ["peanut"]}
    assert body["text"]["format"]["strict"] is True
    assert body["store"] is False

    detail = f"/recipes/{recipe['id']}"
    assert a.client.get("/history", headers=a.alice).json() == []
    assert a.client.get(detail, headers=a.bob).status_code == 404
    assert a.client.get("/history", headers=a.bob).json() == []
    assert a.client.get(detail, headers=a.alice).json() == recipe
    assert a.client.get("/history", headers=a.alice).json()[0]["recipe"] == recipe
    assert a.client.post("/favorites", headers=a.alice, json={"recipeId": recipe["id"]}).json() == recipe
    shopping = a.client.post(f"{detail}/shopping-items", headers=a.alice, json={})
    assert shopping.status_code == 200
    assert [item["name"] for item in shopping.json()] == ["tomato"]
    assert a.snapshot() == inventory


def test_unknown_owner_and_empty_fridge_stop_before_provider(recipe_app):
    a = recipe_app
    unauthorized = a.client.post("/recipes/generate")
    assert unauthorized.status_code == 401
    assert "TEST_SECRET" not in unauthorized.text
    assert generate(a, json={"owner": "2"}).status_code == 400
    a.state.empty = True
    assert generate(a, json={}).status_code == 400
    assert a.state.requests == []
    assert a.counts() == (0, 0, 0)


@pytest.mark.parametrize(("change", "status"), [
    ({"ingredients": [" PEANUT "], "ingredientAmounts": ["1 tbsp"]}, 422),
    ({"ingredients": ["  "]}, 502),
    ({"steps": []}, 502),
    ({"cookingMinutes": 0}, 502),
    ({"caloriesPerServing": None}, 502),
    ({"caloriesPerServing": -1}, 502),
    ({"servings": 1.5}, 502),
    ({"servings": True}, 502),
])
def test_invalid_recipe_rejects_whole_batch(recipe_app, change, status):
    a = recipe_app
    a.state.response_factory = lambda: output(RECIPE, {**RECIPE, **change})
    response = generate(a, json={})
    assert response.status_code == status
    assert set(response.json()) == {"error"}
    assert a.counts() == (0, 0, 0)


@pytest.mark.parametrize("make_response", [
    lambda: httpx.Response(200, text="malformed JSON"),
    lambda: httpx.Response(200, json={"status": "incomplete"}),
    lambda: httpx.Response(200, json={
        "status": "completed",
        "output": [{"type": "message", "role": "assistant", "content": [
            {"type": "refusal", "refusal": "private detail"},
        ]}],
    }),
])
def test_invalid_provider_response_is_sanitized(recipe_app, make_response):
    a = recipe_app
    a.state.response_factory = make_response
    response = generate(a, json={})
    assert response.status_code == 502
    assert "private detail" not in response.text
    assert a.counts() == (0, 0, 0)


def test_provider_failure_preserves_existing_recipe_and_allows_retry(recipe_app):
    a = recipe_app
    first = generate(a, json={}).json()[0]
    detail = f"/recipes/{first['id']}"
    assert a.client.get(detail, headers=a.alice).json() == first
    assert a.client.post("/favorites", headers=a.alice, json={"recipeId": first["id"]}).status_code == 200
    assert a.client.post(f"{detail}/shopping-items", headers=a.alice, json={}).status_code == 200
    collections = ("/favorites", "/history", "/shopping-items")
    before = [a.client.get(path, headers=a.alice).json() for path in collections]
    inventory = a.snapshot()
    preferences = a.state.preferences
    a.state.response_factory = lambda: httpx.Response(429, text="private detail")
    failed = generate(a, json={})
    assert failed.status_code == 503
    assert failed.json()["retryable"] is True
    assert "private detail" not in failed.text
    assert a.counts() == (1, 2, 2)
    assert [a.client.get(path, headers=a.alice).json() for path in collections] == before
    assert a.snapshot() == inventory
    assert a.state.preferences == preferences

    a.state.preferences = (["vegetarian"], ["walnut"])
    a.state.response_factory = lambda: output(RECIPE)
    assert generate(a, json={}).status_code == 200
    assert json.loads(json.loads(a.state.requests[-1].content)["input"])["allergens"] == ["walnut"]


def test_stalled_provider_is_cancelled_and_does_not_write(recipe_app):
    a = recipe_app
    a.state.stalled = True
    response = generate(a, json={})
    assert response.status_code == 503
    assert response.json()["retryable"] is True
    assert a.state.provider_cancelled
    assert a.counts() == (0, 0, 0)


def test_sqlalchemy_rolls_back_all_recipes_if_batch_write_fails(recipe_app):
    a = recipe_app
    dto = RecipeDTO(id="same-id", **RECIPE)
    with pytest.raises(IntegrityError):
        a.store.insert_batch("1", [dto, dto])
    assert a.counts() == (0, 0, 0)

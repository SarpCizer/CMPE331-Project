import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fridgely_app import host
from fridgely_app.database import make_engine, migrate, session_factory
from fridgely_recipes.storage import Recipe, RecipeIngredient, SqlRecipeStore


RECIPE = {
    "title": "Tomato rice",
    "ingredients": ["rice", "tomato"],
    "ingredientAmounts": ["1 cup", "2 medium"],
    "steps": ["Cook the rice", "Add the tomato"],
    "cookingMinutes": 20,
    "caloriesPerServing": 325,
    "servings": 2,
}
PREFERENCES = {"dietary": ["vegan"], "allergens": ["peanut"]}
ACCOUNT = "0123456789abcdef0123456789abcdef"


def cloudflare_result(body):
    return httpx.Response(200, json={"success": True, "result": {"response": body}})


@pytest.fixture
def cloudflare_host(tmp_path, monkeypatch):
    monkeypatch.setenv("RECIPE_PROVIDER", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", ACCOUNT)
    monkeypatch.setenv("CLOUDFLARE_AI_TOKEN", "test-cloudflare-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-token")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    state = SimpleNamespace(requests=[], respond=lambda: cloudflare_result({"recipes": [RECIPE]}))

    def respond(outbound):
        state.requests.append(outbound)
        return state.respond()

    def make_wire(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(host, "httpx", SimpleNamespace(AsyncClient=make_wire, Timeout=httpx.Timeout))

    url = f"sqlite:///{tmp_path / 'cloudflare.db'}"
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    state.new_app = lambda: host.create_app(
        database_url=url, jwt_secret="test-cloudflare-signing-secret-at-least-32-bytes",
        frontend_dir=tmp_path,
    )
    return state


def sign_in(client):
    credentials = {"email": "cloudflare-test@example.test", "password": "Cloudflare-Recipe-Test!"}
    assert client.post("/api/accounts", json=credentials).status_code == 201
    session = client.post("/api/sessions", json=credentials)
    assert session.status_code == 200
    headers = {"Authorization": f"Bearer {session.json()['token']}"}
    assert client.post("/api/inventory", headers=headers, json={"name": "rice"}).status_code == 201
    assert client.put("/api/profile/preferences", headers=headers, json=PREFERENCES).status_code == 200
    return headers


@pytest.mark.parametrize("encode", [False, True], ids=["object", "json-text"])
def test_cloudflare_recipes_work_through_the_real_host(cloudflare_host, encode):
    state = cloudflare_host
    batch = {"recipes": [RECIPE]}
    state.respond = lambda: cloudflare_result(json.dumps(batch) if encode else batch)
    with TestClient(state.new_app()) as client:
        headers = sign_in(client)
        before = client.get("/api/inventory", headers=headers).json()
        generated = client.post("/api/recipes/generate", headers=headers, json={})
        assert generated.status_code == 200
        recipe, = generated.json()
        assert recipe == {**RECIPE, "id": recipe["id"]}
        detail = f"/api/recipes/{recipe['id']}"
        assert client.get(detail, headers=headers).json() == recipe
        assert client.get("/api/history", headers=headers).json()[0]["recipe"] == recipe
        assert client.post("/api/favorites", headers=headers, json={"recipeId": recipe["id"]}).json() == recipe
        shopping = client.post(detail + "/shopping-items", headers=headers, json={})
        assert shopping.status_code == 200
        assert [item["name"] for item in shopping.json()] == ["tomato"]
        assert client.get("/api/inventory", headers=headers).json() == before

    outbound, = state.requests
    assert outbound.url.host == "api.cloudflare.com"
    assert outbound.url.path == f"/client/v4/accounts/{ACCOUNT}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    assert outbound.headers["Authorization"] == "Bearer test-cloudflare-token"
    payload = json.loads(outbound.content)
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert json.loads(payload["messages"][1]["content"]) == {"ingredients": ["rice"], **PREFERENCES}
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["required"] == ["recipes"]
    fields = payload["response_format"]["json_schema"]["properties"]["recipes"]["items"]
    assert "ingredientAmounts" in fields["required"]


def test_cloudflare_receives_known_fridge_amounts_only(cloudflare_host):
    with TestClient(cloudflare_host.new_app()) as client:
        headers = sign_in(client)
        assert client.post("/api/inventory", headers=headers, json={
            "name": "egg", "quantity": 2, "unit": "pcs",
        }).status_code == 201
        before = client.get("/api/inventory", headers=headers).json()
        assert client.post("/api/recipes/generate", headers=headers, json={}).status_code == 200
        assert client.get("/api/inventory", headers=headers).json() == before

    request, = cloudflare_host.requests
    prompt = json.loads(json.loads(request.content)["messages"][1]["content"])
    assert set(prompt["ingredients"]) == {"rice", "egg"}
    assert prompt["availableAmounts"] == [{"name": "egg", "quantity": 2, "unit": "pcs"}]


def test_migration_preserves_recipes_saved_without_amounts(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    migrate(engine, "0003_inventory_quantities")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO accounts (id, email, password_hash, created_at) "
            "VALUES ('owner', 'legacy@example.test', 'fixture', CURRENT_TIMESTAMP)"
        )
        connection.exec_driver_sql(
            "INSERT INTO recipes (id, owner_id, title, cooking_minutes, calories_per_serving, servings) "
            "VALUES ('old-recipe', 'owner', 'Rice', 20, 200, 2)"
        )
        connection.exec_driver_sql(
            "INSERT INTO recipe_ingredients (recipe_id, position, name, name_key) "
            "VALUES ('old-recipe', 0, 'Rice', 'rice')"
        )
        connection.exec_driver_sql(
            "INSERT INTO recipe_steps (recipe_id, position, instruction) "
            "VALUES ('old-recipe', 0, 'Cook the rice')"
        )

    migrate(engine)
    sessions = session_factory(engine)
    with sessions() as session:
        assert session.get(RecipeIngredient, ("old-recipe", 0)).amount is None
        saved = SqlRecipeStore(sessions).find_owned(session, "owner", "old-recipe").recipe
        assert saved.ingredients == ["Rice"]
        assert "ingredientAmounts" not in saved.model_dump()
    engine.dispose()


@pytest.mark.parametrize(("response_factory", "expected"), [
    (lambda: httpx.Response(429, text="private quota detail"), 503),
    (lambda: httpx.Response(200, json={"success": False, "errors": ["private quota detail"]}), 503),
    (lambda: cloudflare_result("private malformed detail"), 502),
    (lambda: cloudflare_result({"recipes": [RECIPE, {
        **RECIPE, "ingredients": ["peanut"], "ingredientAmounts": ["1 tbsp"],
    }]}), 422),
    (lambda: cloudflare_result({"recipes": [RECIPE, {
        key: value for key, value in RECIPE.items() if key != "ingredientAmounts"
    }]}), 502),
    (lambda: cloudflare_result({"recipes": [RECIPE, {**RECIPE, "ingredientAmounts": ["1 cup"]}]}), 502),
    (lambda: cloudflare_result({"recipes": [RECIPE, {**RECIPE, "ingredientAmounts": ["1 cup", " "]}]}), 502),
])
def test_cloudflare_failures_leave_no_partial_recipe(cloudflare_host, response_factory, expected):
    state = cloudflare_host
    state.respond = response_factory
    app = state.new_app()
    with TestClient(app) as client:
        headers = sign_in(client)
        before = client.get("/api/inventory", headers=headers).json()
        response = client.post("/api/recipes/generate", headers=headers, json={})
        assert response.status_code == expected
        assert response.json().get("retryable", False) is (expected == 503)
        assert "private" not in response.text
        assert client.get("/api/inventory", headers=headers).json() == before
        with app.state.sessions() as session:
            assert session.scalar(select(func.count()).select_from(Recipe)) == 0
    assert len(state.requests) == 1


def test_missing_cloudflare_token_does_not_use_the_openai_key(cloudflare_host, monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_AI_TOKEN")
    with TestClient(cloudflare_host.new_app()) as client:
        assert client.get("/api/health").status_code == 200
        headers = sign_in(client)
        response = client.post("/api/recipes/generate", headers=headers, json={})
        assert response.status_code == 503
        assert response.json()["retryable"] is True
    assert cloudflare_host.requests == []


def test_openai_is_still_the_default_provider(cloudflare_host, monkeypatch):
    monkeypatch.delenv("RECIPE_PROVIDER")
    cloudflare_host.respond = lambda: httpx.Response(200, json={
        "status": "completed",
        "output": [{"type": "message", "role": "assistant", "content": [
            {"type": "output_text", "text": json.dumps({"recipes": [RECIPE]})},
        ]}],
    })
    with TestClient(cloudflare_host.new_app()) as client:
        headers = sign_in(client)
        assert client.post("/api/recipes/generate", headers=headers, json={}).status_code == 200
    outbound, = cloudflare_host.requests
    assert str(outbound.url) == "https://api.openai.com/v1/responses"
    assert outbound.headers["Authorization"] == "Bearer test-openai-token"
    schema = json.loads(outbound.content)["text"]["format"]["schema"]
    assert "ingredientAmounts" in schema["properties"]["recipes"]["items"]["required"]

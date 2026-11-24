from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import event, select
from sqlalchemy.exc import OperationalError

from fridgely_collections import (
    AccountPrincipal, CollectionsBase, CoreCallbacks, OwnedRecipe, build_collections,
    create_app, recipe_from_zip_record, zip_inventory_reader,
)
from fridgely_collections.models import Favorite, RecipeView, ShoppingItem
from fridgely_collections.schemas import RecipeDTO
from conftest import AcceptedRecipe, Ingredient, UserInventory
from test_collections_api import call


def test_data_survives_new_application_and_sessions(h):
    item = call(h, "POST", "/shopping-items", {"name": "onion"}).json()
    call(h, "POST", "/favorites", {"recipeId": "recipe-a"})
    call(h, "GET", "/recipes/recipe-a")
    history = call(h, "GET", "/history").json()
    h.engine.dispose()
    app = create_app(session_factory=h.sessions, core=h.core, require_account=h.auth)
    with TestClient(app) as client:
        assert client.get("/shopping-items", headers=h.alice).json() == [item]
        assert client.get("/favorites", headers=h.alice).json() == [h.recipes[0].model_dump()]
        assert client.get("/history", headers=h.alice).json() == history
        assert client.get("/history", headers=h.bob).json() == []


def test_missing_ingredient_batch_rolls_back_after_partial_write(h):
    def fail_on_onion(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO shopping_items") and "onion" in parameters:
            raise OperationalError(statement, parameters, RuntimeError("DATABASE_SECRET"))
    event.listen(h.engine, "before_cursor_execute", fail_on_onion)
    try:
        response = call(h, "POST", "/recipes/recipe-a/shopping-items", {})
    finally:
        event.remove(h.engine, "before_cursor_execute", fail_on_onion)
    assert response.status_code == 503 and "DATABASE_SECRET" not in response.text
    assert call(h, "GET", "/shopping-items").json() == []


def test_failed_history_commit_never_returns_success(h):
    def fail_commit(session):
        raise OperationalError("COMMIT", {}, RuntimeError("DATABASE_SECRET"))
    event.listen(h.sessions.class_, "before_commit", fail_commit)
    try:
        response = call(h, "GET", "/recipes/recipe-a")
    finally:
        event.remove(h.sessions.class_, "before_commit", fail_commit)
    assert response.status_code == 503 and "DATABASE_SECRET" not in response.text
    assert call(h, "GET", "/history").json() == []


def test_core_data_owner_mismatch_fails_closed(h):
    malicious = CoreCallbacks(
        lambda session, owner, rid: OwnedRecipe("2", h.recipes[0]),
        h.core.inventory_lookup)
    app = create_app(session_factory=h.sessions, core=malicious, require_account=h.auth)
    with TestClient(app) as client:
        for path in ["/recipes/recipe-a", "/recipes/recipe-a/shopping-items"]:
            response = client.get(path, headers=h.alice) if path.endswith("recipe-a") else client.post(
                path, json={}, headers=h.alice)
            assert response.status_code == 404
    assert call(h, "GET", "/history").json() == []


def test_invalid_external_inventory_rolls_back(h):
    broken = CoreCallbacks(h.core.recipe_lookup, lambda session, owner: "not-a-list")
    app = create_app(session_factory=h.sessions, core=broken, require_account=h.auth)
    with TestClient(app) as client:
        response = client.post("/recipes/recipe-a/shopping-items", json={}, headers=h.alice)
        assert response.status_code == 503
    assert call(h, "GET", "/shopping-items").json() == []


def test_no_unauthenticated_default_and_no_teammate_routes(h):
    with pytest.raises(TypeError):
        create_app(session_factory=h.sessions, core=h.core)
    for path in ["/accounts", "/sessions", "/inventory", "/recipes/generate", "/predict", "/pantry/add"]:
        assert call(h, "POST", path, {}).status_code in {404, 405}
    assert set(CollectionsBase.metadata.tables) == {"shopping_items", "favorites", "recipe_views"}


def test_mounting_does_not_override_other_routes_or_existing_details(h):
    host = FastAPI()
    @host.get("/recipes/{recipe_id}")
    def host_details(recipe_id: str):
        return {"host": recipe_id}
    module = build_collections(session_factory=h.sessions, core=h.core,
        require_account=h.auth, include_recipe_details=False)
    host.include_router(module.router)
    with TestClient(host) as client:
        assert client.get("/recipes/recipe-a").json() == {"host": "recipe-a"}
        assert client.get("/history", headers=h.alice).json() == []
    # Existing detail service can call this hook after its verified auth.
    assert module.service.open_recipe("1", "recipe-a").id == "recipe-a"
    assert len(module.service.history("1")) == 1


def test_zip_inventory_adapter_reads_only_verified_owners_names(h):
    reader = zip_inventory_reader(inventory_model=UserInventory, ingredient_model=Ingredient)
    before = h.snapshot()
    with h.sessions() as session:
        assert reader(session, "1") == [" RICE "]
        assert reader(session, "2") == ["pepper"]
    assert h.snapshot() == before


def test_legacy_recipe_requires_real_metadata_and_canonical_names():
    record = {"id": 42, "name": "Menemen", "ingredient_str": "2 adet domates, yumurta",
              "instructions": "Cook the ingredients", "score": .9}
    adapted = recipe_from_zip_record(record, internal_id="owned-menemen",
        ingredient_names=["domates", "yumurta"], steps=["Cook the ingredients"],
        cooking_minutes=15, calories_per_serving=200, servings=2)
    assert adapted.id == "owned-menemen" and adapted.title == "Menemen"
    assert adapted.ingredients == ["domates", "yumurta"]
    assert "score" not in adapted.model_dump()
    with pytest.raises(TypeError):
        recipe_from_zip_record(record, internal_id="owned-menemen")
    with pytest.raises(ValidationError):
        recipe_from_zip_record(record, internal_id="owned-menemen",
            ingredient_names=["domates"], steps=["Cook"], cooking_minutes=0,
            calories_per_serving=200, servings=2)


def test_bad_json_is_400_and_does_not_leak_internal_errors(h):
    response = h.client.post("/shopping-items", content=b"{broken", headers=h.alice)
    assert response.status_code == 400 and response.json() == {"error": "Invalid request"}


def test_invalid_clock_does_not_record_history(h):
    h.clock.now = datetime(2026, 11, 19)  # No time zone from the injected dependency.
    response = call(h, "GET", "/recipes/recipe-a")
    assert response.status_code == 503
    assert call(h, "GET", "/history").json() == []

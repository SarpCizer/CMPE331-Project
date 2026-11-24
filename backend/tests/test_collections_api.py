from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest


def call(h, method, path, body=None, who="alice"):
    return h.client.request(method, path, json=body, headers=getattr(h, who))


def test_us10_add_missing_deduplicates_and_preserves_stock(h):
    before = h.snapshot()
    existing = call(h, "POST", "/shopping-items", {"name": " TOMATO "})
    assert existing.status_code == 201
    first = call(h, "POST", "/recipes/recipe-a/shopping-items", {})
    assert first.status_code == 200
    second = call(h, "POST", "/recipes/recipe-a/shopping-items", {})
    assert second.json() == first.json()
    assert {r["name"].strip().casefold() for r in first.json()} == {"tomato", "onion"}
    assert existing.json() in second.json()
    assert h.snapshot() == before
    assert call(h, "GET", "/history").json() == []


def test_us11_manual_items_are_private_and_have_stable_ids(h):
    before = h.snapshot()
    first = call(h, "POST", "/shopping-items", {"name": " Onion "})
    duplicate = call(h, "POST", "/shopping-items", {"name": "ONION"})
    assert first.status_code == 201 and duplicate.status_code == 200
    assert first.json() == duplicate.json()
    assert set(first.json()) == {"id", "name"}
    assert call(h, "GET", "/shopping-items", who="bob").json() == []
    assert call(h, "DELETE", f"/shopping-items/{first.json()['id']}", who="bob").status_code == 404
    deleted = call(h, "DELETE", f"/shopping-items/{first.json()['id']}")
    assert deleted.status_code == 204 and deleted.content == b""
    assert call(h, "GET", "/shopping-items").json() == []
    assert h.snapshot() == before


@pytest.mark.parametrize("body", [{}, {"name": " "}, {"name": None}, {"name": 5},
    {"name": ["onion"]}, {"name": "a"*257}, {"name": "oni\non"},
    {"name": "onion", "ownerId": "2"}])
def test_us11_bad_item_requests_have_no_side_effects(h, body):
    response = call(h, "POST", "/shopping-items", body)
    assert response.status_code == 400 and set(response.json()) == {"error"}
    assert call(h, "GET", "/shopping-items").json() == []


def test_us12_favorite_idempotence_and_no_implicit_view(h):
    before = h.snapshot()
    first = call(h, "POST", "/favorites", {"recipeId": "recipe-a"})
    second = call(h, "POST", "/favorites", {"recipeId": "recipe-a"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == h.recipes[0].model_dump()
    assert call(h, "GET", "/favorites").json() == [first.json()]
    assert call(h, "GET", "/history").json() == []
    assert h.snapshot() == before


def test_us13_remove_favorite_keeps_recipe_and_history(h):
    before = h.snapshot()
    assert call(h, "GET", "/recipes/recipe-a").status_code == 200
    history = call(h, "GET", "/history").json()
    call(h, "POST", "/favorites", {"recipeId": "recipe-a"})
    deleted = call(h, "DELETE", "/favorites/recipe-a")
    assert deleted.status_code == 204 and deleted.content == b""
    assert call(h, "GET", "/favorites").json() == []
    assert call(h, "GET", "/history").json() == history
    assert call(h, "GET", "/recipes/recipe-a").json() == h.recipes[0].model_dump()
    assert h.snapshot() == before


def test_us14_history_tracks_views_only_and_is_newest_first(h):
    before = h.snapshot()
    assert call(h, "GET", "/history").json() == []
    call(h, "GET", "/recipes/recipe-a")
    h.clock.now = datetime(2026, 11, 19, 13, tzinfo=timezone.utc)
    call(h, "GET", "/recipes/recipe-b")
    h.clock.now = datetime(2026, 11, 19, 14, tzinfo=timezone.utc)
    call(h, "GET", "/recipes/recipe-a")
    history = call(h, "GET", "/history").json()
    assert [entry["recipe"]["id"] for entry in history] == ["recipe-a", "recipe-b"]
    assert history[0]["lastViewedAt"] == "2026-11-19T14:00:00.000Z"
    # A late, older request must not move the latest view backwards.
    h.clock.now = datetime(2026, 11, 19, 11, tzinfo=timezone.utc)
    call(h, "GET", "/recipes/recipe-a")
    assert call(h, "GET", "/history").json() == history
    assert h.snapshot() == before


def test_us14_equal_view_timestamps_have_stable_order(h):
    call(h, "GET", "/recipes/recipe-b")
    call(h, "GET", "/recipes/recipe-a")
    assert [r["recipe"]["id"] for r in call(h, "GET", "/history").json()] == ["recipe-a", "recipe-b"]


ROUTES = [("GET", "/shopping-items", None), ("POST", "/shopping-items", {"name": "onion"}),
          ("DELETE", "/shopping-items/unknown", None),
          ("POST", "/recipes/recipe-a/shopping-items", {}),
          ("GET", "/favorites", None), ("POST", "/favorites", {"recipeId": "recipe-a"}),
          ("DELETE", "/favorites/recipe-a", None), ("GET", "/history", None),
          ("GET", "/recipes/recipe-a", None)]


@pytest.mark.parametrize("method,path,body", ROUTES)
@pytest.mark.parametrize("token", [None, "invalid-token", "expired-test-token"])
def test_all_personal_routes_require_host_authentication(h, method, path, body, token):
    headers = {} if token is None else {"Authorization": "Bearer " + token}
    response = h.client.request(method, path, json=body, headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"error": "Authentication required"}


def test_cross_account_recipe_and_collection_access_is_denied(h):
    call(h, "GET", "/recipes/recipe-a")
    call(h, "POST", "/favorites", {"recipeId": "recipe-a"})
    item = call(h, "POST", "/shopping-items", {"name": "onion"}).json()
    before = {p: call(h, "GET", p).json() for p in ["/favorites", "/history", "/shopping-items"]}
    for path in before:
        assert call(h, "GET", path + "?userId=1", who="bob").json() == []
    for method, path, body in [("GET", "/recipes/recipe-a", None),
        ("POST", "/recipes/recipe-a/shopping-items", {}),
        ("POST", "/favorites", {"recipeId": "recipe-a"}),
        ("DELETE", "/favorites/recipe-a", None),
        ("DELETE", f"/shopping-items/{item['id']}", None)]:
        response = call(h, method, path, body, who="bob")
        assert response.status_code == 404 and response.json() == {"error": "Resource not found"}
    assert {p: call(h, "GET", p).json() for p in before} == before


@pytest.mark.parametrize("path,body", [
    ("/favorites", {"recipeId": "bob-recipe", "userId": "2"}),
    ("/recipes/recipe-a/shopping-items", {"owner_id": "2"}),
    ("/favorites", {"recipeId": 1}), ("/favorites", {"recipeId": " "})])
def test_owner_spoofing_and_invalid_identifiers_are_rejected(h, path, body):
    assert call(h, "POST", path, body).status_code == 400
    assert call(h, "GET", "/favorites").json() == []
    assert call(h, "GET", "/shopping-items").json() == []


def test_concurrent_duplicate_shopping_inserts_preserve_one_id(h):
    def add(i):
        return call(h, "POST", "/shopping-items", {"name": " Onion " if i % 2 else "ONION"})
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(add, range(18)))
    assert all(r.status_code in {200, 201} for r in responses)
    assert sum(r.status_code == 201 for r in responses) == 1
    assert len({r.json()["id"] for r in responses}) == 1
    assert len(call(h, "GET", "/shopping-items").json()) == 1


def test_concurrent_add_missing_and_favorites_remain_idempotent(h):
    def add(i):
        return call(h, "POST", "/recipes/recipe-a/shopping-items", {}) if i % 2 else call(
            h, "POST", "/favorites", {"recipeId": "recipe-a"})
    before = h.snapshot()
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(add, range(18)))
    assert all(r.status_code == 200 for r in responses)
    assert len(call(h, "GET", "/shopping-items").json()) == 2
    assert len(call(h, "GET", "/favorites").json()) == 1
    assert call(h, "GET", "/history").json() == []
    assert h.snapshot() == before

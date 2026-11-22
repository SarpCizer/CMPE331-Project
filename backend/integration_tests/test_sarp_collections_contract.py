"""Issues #30-#34: Sarp's module in the real teammate host, not test-auth callbacks.

Run through scripts/verify_team_compatibility.py. Accounts, JWTs, migrations,
inventory and recipe persistence come from the pinned team checkout. Only the
external recipe provider and clock are controlled fixtures.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app

SIGNING_KEY = "test-only-sarp-compatibility-signing-key-32-bytes"
PASSWORD = "Test-only-Compatibility-Password!"
RECIPES = [
    {"title": "Rice meal", "ingredients": ["rice", " TOMATO ", "onion", "ONION"],
     "steps": ["Combine", "Cook"], "cookingMinutes": 20,
     "caloriesPerServing": 300, "servings": 2},
    {"title": "Carrot rice", "ingredients": ["rice", "carrot"],
     "steps": ["Cook"], "cookingMinutes": 15, "caloriesPerServing": 250, "servings": 1},
]


@pytest.fixture(params=["", "/api"], ids=["contract-root", "frontend-api-prefix"])
def shared_host(tmp_path, request):
    state = SimpleNamespace(now=datetime(2026, 11, 23, 12, tzinfo=timezone.utc))
    url = f"sqlite:///{(tmp_path/'shared.db').as_posix()}"
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()

    class Provider:
        async def generate(self, _input):
            return deepcopy(RECIPES)

    def new_app():
        return create_app(database_url=url, jwt_secret=SIGNING_KEY,
                          clock=lambda: state.now, recipe_provider=Provider())

    app = new_app()
    with TestClient(app) as client:
        prefix = request.param

        def account(email):
            body = {"email": email, "password": PASSWORD}
            assert client.post(prefix + "/accounts", json=body).status_code == 201
            login = client.post(prefix + "/sessions", json=body)
            assert login.status_code == 200
            return {"Authorization": "Bearer " + login.json()["token"]}

        alice, bob = account("sarp-alice@example.test"), account("sarp-bob@example.test")

        def send(method, path, body=None, headers=None):
            return client.request(method, prefix + path, json=body,
                                  headers=alice if headers is None else headers)

        assert send("POST", "/inventory", {"name": " RICE "}).status_code == 201
        generated = send("POST", "/recipes/generate", {})
        assert generated.status_code == 200
        yield SimpleNamespace(client=client, app=app, state=state, prefix=prefix,
            alice=alice, bob=bob, send=send, recipes=generated.json(), new_app=new_app)


def test_issue31_and32_real_inventory_missing_names_and_stable_shopping_ids(shared_host):
    h = shared_host
    before = h.send("GET", "/inventory").json()
    item = h.send("POST", "/shopping-items", {"name": " tomato "})
    assert item.status_code == 201
    duplicate = h.send("POST", "/shopping-items", {"name": "TOMATO"})
    assert duplicate.status_code == 200 and duplicate.json() == item.json()
    path = f"/recipes/{h.recipes[0]['id']}/shopping-items"
    first, second = h.send("POST", path, {}), h.send("POST", path, {})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert {r["name"].strip().casefold() for r in first.json()} == {"tomato", "onion"}
    assert item.json() in first.json()
    assert h.send("POST", "/shopping-items", {"name": " "}).status_code == 400
    assert h.send("GET", "/shopping-items").json() == first.json()
    deleted = h.send("DELETE", f"/shopping-items/{item.json()['id']}")
    assert deleted.status_code == 204 and deleted.content == b""
    assert h.send("GET", "/inventory").json() == before


def test_issue30_33_34_complete_recipe_and_independent_favorite_history(shared_host):
    h = shared_host
    before = h.send("GET", "/inventory").json()
    rid = h.recipes[0]["id"]
    assert h.send("GET", "/history").json() == []
    for _ in range(2):
        saved = h.send("POST", "/favorites", {"recipeId": rid})
        assert saved.status_code == 200 and saved.json() == h.recipes[0]
    assert h.send("GET", "/history").json() == []
    opened = h.send("GET", f"/recipes/{rid}")
    assert opened.status_code == 200 and opened.json() == h.recipes[0]
    assert set(opened.json()) == {"id", "title", "ingredients", "steps", "cookingMinutes",
                                  "caloriesPerServing", "servings"}
    assert opened.json()["steps"] == RECIPES[0]["steps"]
    history = h.send("GET", "/history").json()
    assert len(history) == 1 and history[0]["recipe"] == h.recipes[0]
    h.state.now += timedelta(minutes=1)
    h.send("GET", f"/recipes/{h.recipes[1]['id']}")
    h.state.now += timedelta(minutes=1)
    h.send("GET", f"/recipes/{rid}")
    latest = h.send("GET", "/history").json()
    assert [r["recipe"]["id"] for r in latest] == [rid, h.recipes[1]["id"]]
    assert latest[0]["lastViewedAt"] == "2026-11-23T12:02:00.000Z"
    assert h.send("DELETE", f"/favorites/{rid}").status_code == 204
    assert h.send("GET", "/favorites").json() == []
    assert h.send("GET", "/history").json() == latest
    assert h.send("GET", "/inventory").json() == before


def test_issue31_to34_cross_account_url_body_and_owner_spoofing(shared_host):
    h = shared_host
    rid = h.recipes[0]["id"]
    item = h.send("POST", "/shopping-items", {"name": "onion"}).json()
    h.send("POST", "/favorites", {"recipeId": rid})
    h.send("GET", f"/recipes/{rid}")
    paths = ["/inventory", "/shopping-items", "/favorites", "/history"]
    before = {p: h.send("GET", p).json() for p in paths}
    for method, path, body in [
        ("GET", f"/recipes/{rid}", None),
        ("POST", f"/recipes/{rid}/shopping-items", {}),
        ("POST", "/favorites", {"recipeId": rid}),
        ("DELETE", f"/favorites/{rid}", None),
        ("DELETE", f"/shopping-items/{item['id']}", None),
    ]:
        assert h.send(method, path, body, headers=h.bob).status_code == 404
    for path in paths:
        assert h.send("GET", path + "?userId=someone-else", headers=h.bob).json() == []
    assert h.send("POST", "/shopping-items", {"name": "intrusion", "ownerId": "other"}).status_code == 400
    assert {p: h.send("GET", p).json() for p in paths} == before


@pytest.mark.parametrize("kind", ["missing", "forged", "expired"])
def test_real_jwt_is_required_for_every_sarp_route(shared_host, kind):
    h = shared_host
    headers = {}
    if kind != "missing":
        token = h.alice["Authorization"].split()[1]
        if kind == "forged":
            claims = jwt.decode(token, options={"verify_signature": False})
            token = jwt.encode(claims, "test-only-other-signing-key-at-least-32-bytes", algorithm="HS256")
        else:
            h.state.now += timedelta(hours=2)
        headers = {"Authorization": "Bearer " + token}
    rid = h.recipes[0]["id"]
    for method, path, body in [
        ("GET", "/shopping-items", None), ("POST", "/shopping-items", {"name": "onion"}),
        ("DELETE", "/shopping-items/missing", None),
        ("POST", f"/recipes/{rid}/shopping-items", {}), ("GET", "/favorites", None),
        ("POST", "/favorites", {"recipeId": rid}), ("DELETE", f"/favorites/{rid}", None),
        ("GET", "/history", None), ("GET", f"/recipes/{rid}", None),
    ]:
        assert h.send(method, path, body, headers=headers).status_code == 401


def test_issue34_shared_transaction_failure_cannot_return_success(shared_host):
    h = shared_host
    before = h.send("GET", "/history").json()

    def fail_commit(_session):
        raise OperationalError("COMMIT", {}, RuntimeError("TEST_DATABASE_SECRET"))

    session_class = h.app.state.sessions.class_
    event.listen(session_class, "before_commit", fail_commit)
    try:
        response = h.send("GET", f"/recipes/{h.recipes[0]['id']}")
    finally:
        event.remove(session_class, "before_commit", fail_commit)
    assert response.status_code == 503 and "TEST_DATABASE_SECRET" not in response.text
    assert h.send("GET", "/history").json() == before


def test_sarp_collections_survive_real_host_restart(shared_host):
    h = shared_host
    rid = h.recipes[0]["id"]
    h.send("POST", f"/recipes/{rid}/shopping-items", {})
    h.send("POST", "/favorites", {"recipeId": rid})
    h.send("GET", f"/recipes/{rid}")
    paths = ["/inventory", "/shopping-items", "/favorites", "/history"]
    before = {p: h.send("GET", p).json() for p in paths}
    with TestClient(h.new_app()) as client:
        for path in paths:
            assert client.get(h.prefix + path, headers=h.alice).json() == before[path]
            assert client.get(h.prefix + path, headers=h.bob).json() == []

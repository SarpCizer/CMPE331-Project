"""NFR-01/02: verify every protected method and inspect seeded credential handling."""
from datetime import datetime, timezone
import logging
import os
import secrets
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import MetaData, select

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app
from fridgely_app.models import Account
from fridgely_app.security import AUDIENCE, ISSUER, PASSWORDS


ROUTES = [
    ("GET", "/profile/preferences", None),
    ("PUT", "/profile/preferences", {"dietary": [], "allergens": []}),
    ("GET", "/inventory", None), ("POST", "/inventory", {"name": "intrusion"}),
    ("PATCH", "/inventory/{inventory}", {"quantity": 2, "unit": "pcs"}),
    ("DELETE", "/inventory/{inventory}", None),
    ("POST", "/recipes/generate", {}), ("GET", "/recipes/{recipe}", None),
    ("POST", "/recipes/{recipe}/shopping-items", {}),
    ("POST", "/recipes/{recipe}/cook", {"requestId": "security-matrix-cooking", "items": [
        {"inventoryId": "{inventory}", "quantity": 1, "unit": "pcs"}]}),
    ("GET", "/shopping-items", None), ("POST", "/shopping-items", {"name": "intrusion"}),
    ("DELETE", "/shopping-items/{shopping}", None),
    ("POST", "/shopping-items/{shopping}/purchase", {"quantity": 2, "unit": "pcs"}),
    ("POST", "/favorites", {"recipeId": "{recipe}"}),
    ("GET", "/favorites", None), ("DELETE", "/favorites/{recipe}", None),
    ("GET", "/history", None),
    ("GET", "/surprise-recipes", None),
    ("GET", "/weekly-plan", None),
    ("GET", "/weekly-plan/recipes", None),
    ("POST", "/weekly-plan/{day}/{meal}/generate", {"weekStart":"2026-11-23", "dish":"Pasta", "servings":2}),
    ("PUT", "/weekly-plan/{day}/{meal}", {"weekStart": "2026-11-23", "recipeId": "{recipe}"}),
    ("DELETE", "/weekly-plan/{day}/{meal}", None),
    ("POST", "/weekly-plan/shopping-items", {"weekStart": "2026-11-23"}),
]
RECIPE = {"title": "Rice bowl", "ingredients": ["rice", "tomato"],
    "steps": ["Cook rice", "Add tomato"], "cookingMinutes": 20,
    "caloriesPerServing": 300, "servings": 2}


def snapshot(harness):
    with harness.app.state.engine.connect() as connection:
        return {table.name: sorted((tuple(row) for row in connection.execute(select(table))), key=repr)
            for table in harness.metadata.sorted_tables}


def send(harness, prefix, method, path, body=None, token=None):
    path = path.format(**harness.ids)
    if body is not None:
        body = {key: value.format(**harness.ids) if isinstance(value, str) else value
            for key, value in body.items()}
    return harness.client.request(method, prefix + path, json=body,
        headers={"Authorization": f"Bearer {token}"} if token else {})


@pytest.fixture(scope="module", params=["sqlite", "postgresql"])
def matrix(request, tmp_path_factory):
    url = (f"sqlite:///{tmp_path_factory.mktemp('security') / 'matrix.db'}"
        if request.param == "sqlite" else os.getenv("TEST_DATABASE_URL"))
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for the PostgreSQL security matrix")
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    state = SimpleNamespace(calls=0, fail=False)
    provider_marker = secrets.token_urlsafe(32)

    class Provider:
        async def generate(self, _data):
            state.calls += 1
            if state.fail:
                raise RuntimeError(provider_marker)
            return [RECIPE.copy()]

    signing_key = secrets.token_urlsafe(48)
    clock = datetime.now(timezone.utc)
    app = create_app(database_url=url, jwt_secret=signing_key,
        recipe_provider=Provider(), clock=lambda: clock)
    with TestClient(app) as client:
        harness = SimpleNamespace(client=client, app=app, state=state, ids={},
            password=secrets.token_urlsafe(24), signing_key=signing_key, provider_marker=provider_marker)
        harness.metadata = MetaData()
        harness.metadata.reflect(bind=app.state.engine)
        accounts = []
        for _ in range(2):
            email = f"matrix-{uuid4().hex}@example.test"
            credentials = {"email": email, "password": harness.password}
            created = client.post("/accounts", json=credentials)
            assert created.status_code == 201
            login = client.post("/sessions", json=credentials)
            assert login.status_code == 200
            accounts.append(SimpleNamespace(id=created.json()["id"], token=login.json()["token"], email=email))
        harness.alice, harness.bob = accounts
        for account in accounts:
            headers = {"Authorization": f"Bearer {account.token}"}
            added = client.post("/inventory", headers=headers, json={"name": "rice"})
            assert added.status_code == 201
            prefs = client.put("/profile/preferences", headers=headers,
                json={"dietary": ["vegan"], "allergens": ["peanut"]})
            assert prefs.status_code == 200
            generated = client.post("/recipes/generate", headers=headers, json={})
            assert generated.status_code == 200
            recipe, = generated.json()
            shopping = client.post("/shopping-items", headers=headers, json={"name": "oats"})
            assert shopping.status_code == 201
            assert client.post("/favorites", headers=headers, json={"recipeId": recipe["id"]}).status_code == 200
            if account is harness.alice:
                harness.ids = {"day": 0, "meal": "dish-1", "inventory": added.json()["id"], "recipe": recipe["id"],
                    "shopping": shopping.json()["id"]}
        claims = {"sub": harness.alice.id, "iat": int(clock.timestamp()) - 100,
            "exp": int(clock.timestamp()) + 3600, "aud": AUDIENCE, "iss": ISSUER}
        harness.tokens = {
            "missing": None, "malformed": "invalid.token.signature",
            "forged": jwt.encode(claims, secrets.token_urlsafe(48), algorithm="HS256"),
            "expired": jwt.encode({**claims, "exp": int(clock.timestamp()) - 1}, signing_key, algorithm="HS256"),
            "unsigned": jwt.encode(claims, key="", algorithm="none"),
        }
        yield harness


@pytest.mark.parametrize("prefix", ["", "/api"], ids=["root", "api"])
@pytest.mark.parametrize("token_kind", ["missing", "malformed", "forged", "expired", "unsigned"])
@pytest.mark.parametrize("method,path,body", ROUTES, ids=[f"{method} {path}" for method, path, _ in ROUTES])
def test_every_protected_method_rejects_invalid_tokens_without_writes(matrix, prefix, token_kind, method, path, body):
    before, calls = snapshot(matrix), matrix.state.calls
    response = send(matrix, prefix, method, path, body, matrix.tokens[token_kind])
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert set(response.json()) == {"error"}
    unchanged = snapshot(matrix) == before
    assert unchanged, "Denied requests must leave every persisted collection unchanged"
    assert matrix.state.calls == calls, "Denied requests must not call the recipe provider"


@pytest.mark.parametrize("prefix", ["", "/api"], ids=["root", "api"])
@pytest.mark.parametrize("method,path,body", [row for row in ROUTES if any(key in row[1] for key in ("{inventory}", "{shopping}", "{recipe}")) or row[0:2] == ("POST", "/favorites") or row[0] == "PUT" and row[1].startswith("/weekly-plan/")])
def test_foreign_url_and_body_ids_are_denied_without_writes(matrix, prefix, method, path, body):
    before = snapshot(matrix)
    response = send(matrix, prefix, method, path, body, matrix.bob.token)
    assert response.status_code in {403, 404}
    unchanged = snapshot(matrix) == before
    assert unchanged, "Foreign resource IDs must not change either account"


@pytest.mark.parametrize("prefix", ["", "/api"], ids=["root", "api"])
def test_seeded_credentials_absent_from_storage_errors_and_captured_logs(matrix, prefix, caplog):
    before = snapshot(matrix)
    caplog.set_level(logging.DEBUG)
    login = matrix.client.post(prefix + "/sessions",
        json={"email": matrix.alice.email, "password": matrix.password})
    assert login.status_code == 200
    token = login.json()["token"]
    with matrix.app.state.sessions() as session:
        first = session.get(Account, matrix.alice.id).password_hash
        second = session.get(Account, matrix.bob.id).password_hash
        assert first != second
        assert first.startswith("$argon2id$") and second.startswith("$argon2id$")
        assert PASSWORDS.verify(first, matrix.password) and PASSWORDS.verify(second, matrix.password)
    matrix.state.fail = True
    try:
        failed = send(matrix, prefix, "POST", "/recipes/generate", {}, token)
        assert failed.status_code == 503 and failed.json()["retryable"] is True
    finally:
        matrix.state.fail = False
    errors_and_logs = failed.text + caplog.text
    database_text = repr(snapshot(matrix))
    markers = [matrix.password, matrix.signing_key, matrix.provider_marker, token,
        matrix.alice.token, matrix.bob.token]
    leaked = any(marker in errors_and_logs or marker in database_text for marker in markers)
    assert not leaked, "A seeded credential or provider diagnostic leaked"
    unchanged = snapshot(matrix) == before
    assert unchanged, "A provider failure must leave all saved collections unchanged"


def test_openapi_personal_methods_match_the_security_matrix(matrix):
    paths = matrix.client.get("/api/openapi.json").json()["paths"]
    protected = {(method.upper(), path) for path, methods in paths.items()
        for method, operation in methods.items() if isinstance(operation, dict) and operation.get("security")}
    expected = {(method, path.replace("{inventory}", "{item_id}").replace("{shopping}", "{item_id}")
        .replace("{recipe}", "{recipe_id}")) for method, path, _ in ROUTES}
    assert protected == expected, "Update the matrix when a protected method is added or removed"

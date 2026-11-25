from types import SimpleNamespace
from uuid import uuid4

import os
import pytest
from fastapi.testclient import TestClient

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app
from fridgely_collections.schemas import RecipeDTO
from fridgely_recipes.storage import SqlRecipeStore


@pytest.fixture(params=["sqlite", "postgresql"])
def kitchen(tmp_path, request):
    url = f"sqlite:///{tmp_path / 'cooking.db'}" if request.param == "sqlite" else os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL cooking verification")
    suffix = uuid4().hex
    recipe_id = uuid4().hex
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    app = create_app(database_url=url, jwt_secret='synthetic-cooking-test-secret-32-characters')
    with TestClient(app) as client:
        def account(email):
            credentials = {'email': email, 'password': 'Synthetic-password-123!'}
            owner = client.post('/api/accounts', json=credentials).json()['id']
            token = client.post('/api/sessions', json=credentials).json()['token']
            return owner, {'Authorization': f'Bearer {token}'}
        owner, alice = account(f'cook-{suffix}@example.test')
        _, bob = account(f'other-{suffix}@example.test')
        SqlRecipeStore(app.state.sessions).insert_batch(owner, [RecipeDTO(
            id=recipe_id, title='Rice and eggs', ingredients=['rice', 'egg'],
            ingredientAmounts=['150 g', '2'], steps=['Cook.'], cookingMinutes=10,
            caloriesPerServing=200, servings=2)])
        def add(name, quantity=2, unit='pcs', headers=None):
            return client.post('/api/inventory', headers=headers or alice,
                json={'name': name, 'quantity': quantity, 'unit': unit}).json()
        def stock():
            return client.get('/api/inventory', headers=alice).json()
        yield SimpleNamespace(client=client, alice=alice, bob=bob, add=add, stock=stock, recipe_id=recipe_id)


def command(item, quantity, request_id=None, unit=None):
    return {'requestId': request_id or uuid4().hex, 'items': [
        {'inventoryId': item['id'], 'quantity': quantity, 'unit': unit or item['unit']}]}


def cook(kitchen, body, headers=None, recipe=None):
    return kitchen.client.post(f'/api/recipes/{recipe or kitchen.recipe_id}/cook', headers=headers or kitchen.alice, json=body)


def test_confirmed_cooking_depletes_and_retry_is_idempotent(kitchen):
    item = kitchen.add('egg')
    before = kitchen.stock()
    assert kitchen.client.get(f'/api/recipes/{kitchen.recipe_id}', headers=kitchen.alice).status_code == 200
    assert kitchen.stock() == before
    body = command(item, 2)
    assert cook(kitchen, body).status_code == 200
    assert kitchen.stock() == [{**item, 'quantity': 0}]
    assert cook(kitchen, body).json()['replayed'] is True
    assert kitchen.stock()[0]['quantity'] == 0


def test_shortage_rolls_back_entire_recipe(kitchen):
    egg, rice = kitchen.add('egg'), kitchen.add('rice', .1, 'kg')
    before = kitchen.stock()
    body = command(egg, 1)
    body['items'] += command(rice, .15)['items']
    assert cook(kitchen, body).status_code == 409
    assert kitchen.stock() == before


@pytest.mark.parametrize('case', ['foreign_recipe', 'foreign_item', 'missing_recipe', 'unrelated', 'unit', 'duplicate', 'negative', 'boolean', 'fractional'])
def test_invalid_cooking_never_changes_stock(kitchen, case):
    item = kitchen.add('egg')
    body = command(item, 1)
    headers, recipe, expected = None, kitchen.recipe_id, 400
    if case == 'foreign_recipe': headers, expected = kitchen.bob, 404
    if case == 'foreign_item':
        body = command(kitchen.add('egg', headers=kitchen.bob), 1)
        expected = 404
    if case == 'missing_recipe': recipe, expected = 'missing', 404
    if case == 'unrelated': body = command(kitchen.add('banana'), 1)
    if case == 'unit': body['items'][0]['unit'], expected = 'kg', 409
    if case == 'duplicate': body['items'] *= 2
    if case == 'negative': body['items'][0]['quantity'] = -1
    if case == 'boolean': body['items'][0]['quantity'] = True
    if case == 'fractional': body['items'][0]['quantity'] = 1.5
    before = kitchen.stock()
    assert cook(kitchen, body, headers, recipe).status_code == expected
    assert kitchen.stock() == before


def test_idempotency_key_cannot_be_reused_for_a_different_deduction(kitchen):
    item = kitchen.add('egg', 3)
    body = command(item, 1)
    assert cook(kitchen, body).status_code == 200
    body['items'][0]['quantity'] = 2
    assert cook(kitchen, body).status_code == 409
    assert kitchen.stock()[0]['quantity'] == 2


def test_zero_stock_can_be_refilled_and_is_excluded_from_recipe_input(kitchen):
    from fridgely_app.core import inventory_names, inventory_amounts
    item = kitchen.add('egg')
    path = '/api/inventory/' + item['id']
    assert kitchen.client.patch(path, headers=kitchen.alice, json={'quantity': 0, 'unit': 'pcs'}).status_code == 200
    owner = kitchen.client.get('/api/inventory', headers=kitchen.alice).json()[0]
    with kitchen.client.app.state.sessions() as session:
        from fridgely_app.models import InventoryEntry
        account_id = session.get(InventoryEntry, owner['id']).owner_id
        assert inventory_names(session, account_id) == []
        assert inventory_amounts(session, account_id) == ()
    assert kitchen.client.patch(path, headers=kitchen.alice, json={'quantity': 3, 'unit': 'pcs'}).status_code == 200
    assert kitchen.stock()[0]['quantity'] == 3


@pytest.mark.parametrize('same_request', [True, False])
def test_simultaneous_confirmations_cannot_overspend(kitchen, same_request):
    from concurrent.futures import ThreadPoolExecutor
    item = kitchen.add('egg', 2)
    first = command(item, 2)
    second = first if same_request else command(item, 2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda body: cook(kitchen, body), [first, second]))
    assert any(response.status_code == 200 for response in responses)
    assert all(response.status_code in {200, 409, 503} for response in responses)
    assert kitchen.stock()[0]['quantity'] == 0
    if same_request:
        assert cook(kitchen, first).json()['replayed'] is True


def test_database_failure_rolls_back_stock_and_confirmation(kitchen):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    item = kitchen.add('egg')
    before = kitchen.stock()
    body = command(item, 1)
    def fail(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith('UPDATE inventory_entries'):
            raise SQLAlchemyError('synthetic private database detail')
    engine = kitchen.client.app.state.engine
    event.listen(engine, 'before_cursor_execute', fail)
    try:
        response = cook(kitchen, body)
        assert response.status_code == 503
        assert 'synthetic' not in response.text
    finally:
        event.remove(engine, 'before_cursor_execute', fail)
    assert kitchen.stock() == before
    assert cook(kitchen, body).status_code == 200
    assert kitchen.stock()[0]['quantity'] == 1

import os
from uuid import uuid4
import pytest
from sqlalchemy import text
from fridgely_app.database import make_engine, migrate
from test_recipe_consumption import kitchen


def add(kitchen, **body):
    return kitchen.client.post('/api/shopping-items', headers=kitchen.alice, json=body)


def test_manual_quantity_persists_replaces_without_summing_and_removes(kitchen):
    before = kitchen.stock()
    response = add(kitchen, name=' Rice ', quantity=.5, unit='kg')
    assert response.status_code == 201
    item = response.json()
    assert item['quantity'] == .5 and item['unit'] == 'kg'
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == [item]
    updated = add(kitchen, name='RICE', quantity=750, unit='g')
    assert updated.status_code == 200
    assert updated.json() == {**item, 'quantity': 750, 'unit': 'g'}
    assert add(kitchen, name='rice', quantity=750, unit='g').json() == updated.json()
    assert add(kitchen, name='rice').json() == updated.json()
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.bob).json() == []
    assert kitchen.client.delete('/api/shopping-items/' + item['id'], headers=kitchen.bob).status_code == 404
    assert kitchen.client.delete('/api/shopping-items/' + item['id'], headers=kitchen.alice).status_code == 204
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == []
    assert kitchen.stock() == before


@pytest.mark.parametrize('body', [
    {'quantity': 0, 'unit': 'pcs'}, {'quantity': -1, 'unit': 'g'},
    {'quantity': 1.5, 'unit': 'pcs'}, {'quantity': 1.5, 'unit': 'pack'},
    {'quantity': 1.5, 'unit': 'bunch'}, {'quantity': True, 'unit': 'pcs'},
    {'quantity': '2', 'unit': 'pcs'}, {'quantity': 1000001, 'unit': 'g'},
    {'quantity': 2}, {'unit': 'kg'}, {'quantity': 1, 'unit': 'cup'},
    {'quantity': 2, 'unit': 'pcs', 'owner_id': 'someone-else'},
])
def test_invalid_amount_never_changes_list(kitchen, body):
    original = add(kitchen, name='egg', quantity=2, unit='pcs').json()
    assert add(kitchen, name='egg', **body).status_code == 400
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == [original]


def test_recipe_missing_addition_preserves_explicit_shopping_amount(kitchen):
    item = add(kitchen, name='rice', quantity=500, unit='g').json()
    response = kitchen.client.post(f'/api/recipes/{kitchen.recipe_id}/shopping-items', headers=kitchen.alice, json={})
    assert response.status_code == 200
    assert next(x for x in response.json() if x['name'] == 'rice') == item
    assert kitchen.stock() == []


@pytest.mark.parametrize('database', ['sqlite', 'postgresql'])
def test_upgrade_preserves_legacy_rows_and_owner_identity(tmp_path, database):
    url = f"sqlite:///{tmp_path / 'legacy-shopping.db'}" if database == 'sqlite' else os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('TEST_DATABASE_URL is required for PostgreSQL legacy shopping upgrade')
    engine = make_engine(url)
    cleanup = None
    schema = 'shopping_upgrade_' + uuid4().hex
    if database == 'postgresql':
        from sqlalchemy import event
        cleanup = make_engine(url)
        with cleanup.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        @event.listens_for(engine, 'connect')
        def isolate(connection, _record):
            cursor = connection.cursor()
            cursor.execute(f'SET search_path TO "{schema}"')
            cursor.close()
    try:
        migrate(engine, '0005_cooking_confirmations')
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO accounts (id,email,password_hash,created_at) VALUES ('legacy','legacy-shopping@example.test','synthetic-hash',CURRENT_TIMESTAMP)"))
            connection.execute(text("INSERT INTO shopping_items (id,owner_id,name,name_key) VALUES ('item','legacy','Milk','milk')"))
        migrate(engine)
        migrate(engine)
        with engine.connect() as connection:
            assert tuple(connection.execute(text('SELECT id,owner_id,name,name_key,quantity,unit FROM shopping_items')).one()) == ('item','legacy','Milk','milk',None,None)
    finally:
        engine.dispose()
        if cleanup is not None:
            with cleanup.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            cleanup.dispose()


def purchase(kitchen, item, quantity=2, unit='pcs', headers=None):
    return kitchen.client.post('/api/shopping-items/' + item['id'] + '/purchase',
        headers=headers or kitchen.alice, json={'quantity': quantity, 'unit': unit})


def test_purchase_atomically_refills_depleted_stock_and_replay_survives_reconnect(kitchen):
    stock = kitchen.add('egg', 1)
    kitchen.client.patch('/api/inventory/' + stock['id'], headers=kitchen.alice, json={'quantity': 0, 'unit': 'pcs'})
    item = add(kitchen, name='egg').json()
    assert purchase(kitchen, item, headers=kitchen.bob).status_code == 404
    result = purchase(kitchen, item)
    assert result.status_code == 200
    assert result.json()['replayed'] is False
    assert kitchen.stock()[0]['quantity'] == 2
    assert kitchen.stock()[0]['id'] == stock['id']
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == []
    kitchen.client.app.state.engine.dispose()
    assert purchase(kitchen, item).json()['replayed'] is True
    assert purchase(kitchen, item, 3).status_code == 409
    assert kitchen.stock()[0]['quantity'] == 2


@pytest.mark.parametrize('stock_unit,stock_amount,bought_unit,bought_amount,expected', [
    ('kg', .5, 'g', 250, .75), ('L', .2, 'ml', 200, .4),
])
def test_purchase_converts_only_compatible_units(kitchen, stock_unit, stock_amount, bought_unit, bought_amount, expected):
    kitchen.add('product', stock_amount, stock_unit)
    item = add(kitchen, name='product').json()
    assert purchase(kitchen, item, bought_amount, bought_unit).status_code == 200
    assert kitchen.stock()[0]['quantity'] == expected


def test_purchase_keeps_unknown_or_incompatible_stock_separate(kitchen):
    kitchen.client.post('/api/inventory', headers=kitchen.alice, json={'name': 'milk'})
    kitchen.add('milk', 2, 'pcs')
    before = kitchen.stock()
    item = add(kitchen, name='milk').json()
    assert purchase(kitchen, item, 500, 'ml').status_code == 200
    after = kitchen.stock()
    assert all(row in after for row in before)
    assert any(row['quantity'] == 500 and row['unit'] == 'ml' for row in after)


def test_purchase_storage_failure_rolls_back_shopping_and_inventory(kitchen):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    item = add(kitchen, name='egg').json()
    before = kitchen.stock()
    def fail(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith('DELETE FROM shopping_items'):
            raise SQLAlchemyError('Synthetic private storage detail')
    engine = kitchen.client.app.state.engine
    event.listen(engine, 'before_cursor_execute', fail)
    try:
        response = purchase(kitchen, item)
        assert response.status_code == 503
        assert 'Synthetic' not in response.text
    finally:
        event.remove(engine, 'before_cursor_execute', fail)
    assert kitchen.stock() == before
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == [item]
    assert purchase(kitchen, item).status_code == 200
    assert kitchen.stock()[0]['quantity'] == 2


def test_simultaneous_purchase_never_refills_twice(kitchen):
    from concurrent.futures import ThreadPoolExecutor
    item = add(kitchen, name='egg').json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: purchase(kitchen, item), range(2)))
    assert any(r.status_code == 200 for r in responses)
    assert all(r.status_code in {200, 503} for r in responses)
    assert purchase(kitchen, item).status_code == 200
    assert kitchen.stock()[0]['quantity'] == 2


def test_purchase_overflow_and_invalid_command_leave_both_collections_unchanged(kitchen):
    kitchen.add('egg', 1000000)
    item = add(kitchen, name='egg', quantity=2, unit='pcs').json()
    before = kitchen.stock()
    assert purchase(kitchen, item).status_code == 409
    for body in [{}, {'quantity': 0, 'unit': 'pcs'}, {'quantity': True, 'unit': 'pcs'},
                 {'quantity': 1.5, 'unit': 'pcs'}, {'quantity': 1, 'unit': 'cup'},
                 {'quantity': 1, 'unit': 'pcs', 'owner_id': 'other'}]:
        response = kitchen.client.post('/api/shopping-items/' + item['id'] + '/purchase',
            headers=kitchen.alice, json=body)
        assert response.status_code == 400
    assert kitchen.stock() == before
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == [item]


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity'])
def test_nonfinite_shopping_amount_is_rejected(kitchen, value):
    response = kitchen.client.post('/api/shopping-items', headers={**kitchen.alice, 'Content-Type': 'application/json'},
        content='{"name":"egg","quantity":' + value + ',"unit":"pcs"}')
    assert response.status_code == 400
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == []


@pytest.mark.parametrize('transient', [True, False])
def test_purchase_database_lock_retries_or_fails_without_partial_writes(kitchen, transient):
    import sqlite3
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError
    item = add(kitchen, name='egg').json()
    attempts = []
    def locked(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith('INSERT INTO purchase_confirmations') and (not attempts or not transient):
            attempts.append(True)
            original = sqlite3.OperationalError('Controlled database lock')
            original.sqlite_errorcode = 5
            raise OperationalError('Controlled transaction retry', {}, original)
    engine = kitchen.client.app.state.engine
    event.listen(engine, 'before_cursor_execute', locked)
    try:
        response = purchase(kitchen, item)
    finally:
        event.remove(engine, 'before_cursor_execute', locked)
    if transient:
        assert response.status_code == 200
        assert kitchen.stock()[0]['quantity'] == 2
        assert purchase(kitchen, item).json()['replayed'] is True
    else:
        assert response.status_code == 503
        assert kitchen.stock() == []
        assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == [item]

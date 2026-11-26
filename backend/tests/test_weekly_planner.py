import pytest
from sqlalchemy import text
from fridgely_app.database import make_engine, migrate
from test_recipe_consumption import kitchen
from test_recipe_shortages import recipe

WEEK = '2026-11-23'


def put(k, day, meal, rid, week=WEEK, headers=None):
    return k.client.put(f'/api/weekly-plan/{day}/{meal}', headers=headers or k.alice,
        json={'weekStart': week, 'recipeId': rid})


def get(k, week=WEEK, headers=None):
    return k.client.get('/api/weekly-plan', params={'weekStart': week}, headers=headers or k.alice)


def shopping(k, week=WEEK):
    return k.client.post('/api/weekly-plan/shopping-items', headers=k.alice, json={'weekStart': week})


def test_week_persists_preparation_and_totals_subtract_stock_once(kitchen):
    kitchen.add('banana', 1)
    kitchen.add('milk', .1, 'L')
    rid = recipe(kitchen, ['banana', 'milk'], ['1 pcs', '100 ml'])
    before = kitchen.stock()
    assert get(kitchen).json() == {'weekStart': WEEK, 'entries': []}
    assert put(kitchen, 0, 'dinner', rid).status_code == 200
    result = put(kitchen, 1, 'breakfast', rid)
    assert result.status_code == 200
    entries = result.json()['entries']
    assert len(entries) == 2
    assert entries[0]['recipe']['steps'] == ['Prepare.']
    assert get(kitchen).json()['entries'] == entries
    kitchen.client.app.state.engine.dispose()
    assert len(get(kitchen).json()['entries']) == 2
    result = shopping(kitchen)
    assert result.status_code == 200
    data = result.json()
    assert data['plannedMeals'] == 2
    assert data['needsReview'] == []
    assert {x['name']: (x['quantity'], x['unit']) for x in data['shopping']} == {'banana': (1, 'pcs'), 'milk': (100, 'ml')}
    assert shopping(kitchen).json()['shopping'] == data['shopping']
    assert kitchen.stock() == before
    assert get(kitchen, '2026-11-30').json()['entries'] == []
    assert get(kitchen, headers=kitchen.bob).json()['entries'] == []
    assert put(kitchen, 0, 'dinner', rid, headers=kitchen.bob).status_code == 404
    removed = kitchen.client.delete('/api/weekly-plan/0/dinner', params={'weekStart': WEEK}, headers=kitchen.alice)
    assert removed.status_code == 200 and len(removed.json()['entries']) == 1
    assert kitchen.stock() == before


@pytest.mark.parametrize('week,day,meal', [('2026-11-24',0,'dinner'), ('not-a-date',0,'dinner'),
    (WEEK,7,'dinner'), (WEEK,-1,'dinner'), (WEEK,0,'snack')])
def test_invalid_plan_never_changes_saved_meals(kitchen, week, day, meal):
    assert put(kitchen, 0, 'dinner', kitchen.recipe_id).status_code == 200
    before = get(kitchen).json()
    assert put(kitchen, day, meal, kitchen.recipe_id, week).status_code == 400
    assert get(kitchen).json() == before


def test_empty_week_and_unknown_amounts_are_explicit(kitchen):
    assert shopping(kitchen).status_code == 400
    kitchen.add('egg', 1)
    rid = recipe(kitchen, ['egg', 'salt'], ['1 cup', 'to taste'])
    assert put(kitchen, 6, 'lunch', rid).status_code == 200
    result = shopping(kitchen).json()
    assert set(result['needsReview']) == {'egg', 'salt'}
    assert [x['name'] for x in result['shopping']] == ['salt']
    assert 'quantity' not in result['shopping'][0]


def test_other_day_edits_and_other_week_plans_are_preserved(kitchen):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda day: put(kitchen, day, 'dinner', kitchen.recipe_id), [0,1]))
    assert all(r.status_code == 200 for r in results)
    assert len(get(kitchen).json()['entries']) == 2
    assert put(kitchen, 0, 'lunch', kitchen.recipe_id, '2026-11-30').status_code == 200
    assert len(get(kitchen).json()['entries']) == 2
    assert len(get(kitchen, '2026-11-30').json()['entries']) == 1


def test_shopping_failure_rolls_back_all_weekly_items(kitchen):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    assert put(kitchen, 0, 'dinner', kitchen.recipe_id).status_code == 200
    attempts=[]
    def fail(_connection,_cursor,statement,_params,_context,_many):
        if statement.startswith('INSERT INTO shopping_items'):
            attempts.append(True)
            if len(attempts) == 2: raise SQLAlchemyError('Synthetic private detail')
    engine=kitchen.client.app.state.engine
    event.listen(engine,'before_cursor_execute',fail)
    try:
        response=shopping(kitchen)
        assert response.status_code == 503 and 'Synthetic' not in response.text
    finally:
        event.remove(engine,'before_cursor_execute',fail)
    assert kitchen.client.get('/api/shopping-items',headers=kitchen.alice).json() == []
    assert shopping(kitchen).status_code == 200


def test_plan_upgrade_preserves_legacy_collections(tmp_path):
    engine=make_engine(f'sqlite:///{tmp_path / "legacy-plan.db"}')
    try:
        migrate(engine,'0006_shopping_quantities')
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO accounts(id,email,password_hash,created_at) VALUES('legacy','planner@example.test','synthetic',CURRENT_TIMESTAMP)"))
            connection.execute(text("INSERT INTO shopping_items(id,owner_id,name,name_key,quantity,unit) VALUES('item','legacy','Milk','milk',2,'L')"))
        migrate(engine);migrate(engine)
        with engine.connect() as connection:
            assert tuple(connection.execute(text('SELECT id,owner_id,name,quantity,unit FROM shopping_items')).one()) == ('item','legacy','Milk',2,'L')
            assert connection.execute(text('SELECT count(*) FROM weekly_meals')).scalar_one() == 0
    finally: engine.dispose()

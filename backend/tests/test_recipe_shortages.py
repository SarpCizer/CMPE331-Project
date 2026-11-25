import pytest
from test_recipe_consumption import kitchen
from fridgely_collections.schemas import RecipeDTO
from fridgely_recipes.storage import SqlRecipeStore
from uuid import uuid4


def recipe(kitchen, names, amounts):
    from fridgely_app.models import InventoryEntry
    with kitchen.client.app.state.sessions() as session:
        owner = session.get(InventoryEntry, kitchen.stock()[0]['id']).owner_id
    recipe_id = uuid4().hex
    SqlRecipeStore(kitchen.client.app.state.sessions).insert_batch(owner, [RecipeDTO(
        id=recipe_id, title='Shopping shortage test', ingredients=names,
        ingredientAmounts=amounts, steps=['Prepare.'], cookingMinutes=5,
        caloriesPerServing=100, servings=1)])
    return recipe_id


def missing(kitchen, recipe_id, headers=None):
    return kitchen.client.post(f'/api/recipes/{recipe_id}/shopping-items',
        headers=headers or kitchen.alice, json={})


def test_favorite_shortage_is_added_once_and_can_be_removed(kitchen):
    kitchen.add('banana', 1)
    kitchen.add('milk', .2, 'L')
    kitchen.add('sugar', .94, 'kg')
    rid = recipe(kitchen, ['banana', 'milk', 'sugar'], ['2 pcs', '200 ml', '20 g'])
    before = kitchen.stock()
    assert kitchen.client.post('/api/favorites', headers=kitchen.alice, json={'recipeId': rid}).status_code in {200, 201}
    result = missing(kitchen, rid)
    assert result.status_code == 200
    items = result.json()
    assert [i['name'] for i in items] == ['banana']
    assert missing(kitchen, rid).json() == items
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == items
    assert kitchen.stock() == before
    assert kitchen.client.delete('/api/shopping-items/' + items[0]['id'], headers=kitchen.alice).status_code in {200, 204}
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json() == []
    assert kitchen.stock() == before


@pytest.mark.parametrize('stock,unit,names,amounts,expected', [
    (.1, 'kg', ['rice'], ['150 g'], ['rice']),
    (.2, 'L', ['milk'], ['200 ml'], []),
    (1, 'pcs', ['egg', 'egg'], ['1 pcs', '1 pcs'], ['egg']),
    (1, 'pcs', ['egg'], ['1 cup'], []),
    (1, 'pcs', ['egg'], None, []),
    (1, 'pcs', ['egg'], ['200 g'], []),
])
def test_quantified_and_legacy_availability(kitchen, stock, unit, names, amounts, expected):
    kitchen.add(names[0], stock, unit)
    rid = recipe(kitchen, names, amounts)
    before = kitchen.stock()
    assert [i['name'] for i in missing(kitchen, rid).json()] == expected
    assert kitchen.stock() == before


def test_duplicate_stock_and_owner_isolation(kitchen):
    kitchen.add('rice', .1, 'kg')
    kitchen.add(' Rice ', 50, 'g')
    kitchen.add('egg', 1)
    kitchen.add('egg', 5, headers=kitchen.bob)
    rid = recipe(kitchen, ['rice', 'egg'], ['150 g', '2 pcs'])
    assert [i['name'] for i in missing(kitchen, rid).json()] == ['egg']
    assert missing(kitchen, rid, kitchen.bob).status_code == 404
    assert kitchen.client.get('/api/shopping-items', headers=kitchen.bob).json() == []

@pytest.mark.parametrize('amount', ['to taste', '0 pcs', '1.5 pcs', '1 cup', '200 g'])
def test_unreliable_legacy_measurements_do_not_invent_shortages(kitchen, amount):
    kitchen.add('egg', 1)
    rid = recipe(kitchen, ['egg'], [amount])
    assert missing(kitchen, rid).json() == []


def test_unknown_stock_and_mixed_recipe_dimensions_preserve_presence(kitchen):
    kitchen.add('rice', .1, 'kg')
    assert kitchen.client.post('/api/inventory', headers=kitchen.alice, json={'name': 'rice'}).status_code == 201
    rid = recipe(kitchen, ['rice'], ['500 g'])
    assert missing(kitchen, rid).json() == []
    rid = recipe(kitchen, ['rice', 'rice'], ['500 g', '1 pcs'])
    assert missing(kitchen, rid).json() == []


def test_decimal_sums_and_zero_stock(kitchen):
    kitchen.add('milk', .1, 'L')
    kitchen.add('milk', .2, 'L')
    egg = kitchen.add('egg', 1)
    assert kitchen.client.patch('/api/inventory/' + egg['id'], headers=kitchen.alice,
        json={'quantity': 0, 'unit': 'pcs'}).status_code == 200
    rid = recipe(kitchen, ['milk', 'egg'], ['300 ml', '1 pcs'])
    assert [i['name'] for i in missing(kitchen, rid).json()] == ['egg']

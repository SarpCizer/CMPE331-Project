import pytest
from test_recipe_consumption import kitchen
from test_recipe_shortages import recipe, missing


def cart(kitchen):
    return kitchen.client.get('/api/shopping-items', headers=kitchen.alice).json()


def test_favorite_adds_only_actual_deficit_and_purchase_refills_it(kitchen):
    kitchen.add('banana', 1)
    kitchen.add('milk', .1, 'L')
    kitchen.add('sugar', .01, 'kg')
    rid = recipe(kitchen, ['banana', 'milk', 'sugar', 'egg'], ['2 pcs', '200 ml', '20 g', '2 pcs'])
    assert kitchen.client.post('/api/favorites', headers=kitchen.alice, json={'recipeId': rid}).status_code == 200
    before = kitchen.stock()
    response = missing(kitchen, rid)
    assert response.status_code == 200
    amounts = {i['name']: (i.get('quantity'), i.get('unit')) for i in response.json()}
    assert amounts == {'banana': (1, 'pcs'), 'milk': (100, 'ml'), 'sugar': (10, 'g'), 'egg': (2, 'pcs')}
    assert missing(kitchen, rid).json() == response.json()
    assert kitchen.stock() == before
    for item in response.json():
        bought = kitchen.client.post('/api/shopping-items/' + item['id'] + '/purchase', headers=kitchen.alice,
            json={'quantity': item['quantity'], 'unit': item['unit']})
        assert bought.status_code == 200
    assert cart(kitchen) == []
    assert {i['name']: i['quantity'] for i in kitchen.stock()} == {'banana': 2, 'milk': .2, 'sugar': .02, 'egg': 2}
    assert missing(kitchen, rid).json() == []


def test_duplicate_recipe_and_stock_rows_are_summed_before_shortage(kitchen):
    kitchen.add('rice', .05, 'kg')
    kitchen.add(' Rice ', 50, 'g')
    rid = recipe(kitchen, ['rice', 'RICE'], ['100 g', '0.1 kg'])
    result = missing(kitchen, rid).json()
    assert len(result) == 1
    assert result[0]['quantity'] == 100 and result[0]['unit'] == 'g'


def test_existing_amounts_are_not_accumulated_or_reduced(kitchen):
    kitchen.add('rice', .05, 'kg')
    rid = recipe(kitchen, ['rice'], ['200 g'])
    item = kitchen.client.post('/api/shopping-items', headers=kitchen.alice,
        json={'name': 'rice', 'quantity': .1, 'unit': 'kg'}).json()
    result = missing(kitchen, rid).json()
    assert result == [{**item, 'quantity': .15}]
    assert missing(kitchen, rid).json() == result
    kitchen.client.post('/api/shopping-items', headers=kitchen.alice, json={'name': 'rice', 'quantity': .5, 'unit': 'kg'})
    result = missing(kitchen, rid).json()
    assert result == [{**item, 'quantity': .5}]


def test_unknown_cart_amount_is_filled_and_incompatible_amount_is_preserved(kitchen):
    kitchen.add('rice', .05, 'kg')
    rid = recipe(kitchen, ['rice'], ['200 g'])
    item = kitchen.client.post('/api/shopping-items', headers=kitchen.alice, json={'name': 'rice'}).json()
    result = missing(kitchen, rid).json()
    assert result == [{**item, 'quantity': 150, 'unit': 'g'}]
    kitchen.client.post('/api/shopping-items', headers=kitchen.alice, json={'name': 'rice', 'quantity': 1, 'unit': 'pack'})
    assert missing(kitchen, rid).json() == [{**item, 'quantity': 1, 'unit': 'pack'}]


def test_legacy_unknown_measurements_do_not_invent_amounts(kitchen):
    kitchen.add('egg', 1)
    rid = recipe(kitchen, ['egg', 'onion'], ['1 pcſ', 'to taste'])
    result = missing(kitchen, rid).json()
    assert [i['name'] for i in result] == ['onion']
    assert 'quantity' not in result[0]


def test_foreign_stock_does_not_reduce_own_shortage(kitchen):
    kitchen.add('banana', 1)
    kitchen.add('milk', 1, 'L', headers=kitchen.bob)
    rid = recipe(kitchen, ['milk'], ['200 ml'])
    result = missing(kitchen, rid).json()
    assert [(i['quantity'], i['unit']) for i in result] == [(200, 'ml')]
    assert missing(kitchen, rid, kitchen.bob).status_code == 404


def test_zero_stock_uses_full_requirement_and_expanding_casefold_name_is_safe(kitchen):
    name = 'ß' * 150
    item = kitchen.add(name, 1)
    kitchen.client.patch('/api/inventory/' + item['id'], headers=kitchen.alice, json={'quantity': 0, 'unit': 'pcs'})
    rid = recipe(kitchen, [name], ['2 pcs'])
    result = missing(kitchen, rid)
    assert result.status_code == 200
    assert result.json()[0]['name'] == name
    assert result.json()[0]['quantity'] == 2

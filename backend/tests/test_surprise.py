from test_recipe_consumption import kitchen


def test_surprise_includes_only_fully_measured_owned_stock(kitchen):
    path='/api/surprise-recipes'
    assert kitchen.client.get(path).status_code==401
    assert kitchen.client.get(path,headers=kitchen.alice).json()==[]
    kitchen.add('rice',.15,'kg');kitchen.add('egg',2)
    before=kitchen.stock()
    recipes=kitchen.client.get(path,headers=kitchen.alice).json()
    assert [x['id'] for x in recipes]==[kitchen.recipe_id]
    assert kitchen.client.get(path,headers=kitchen.bob).json()==[]
    assert kitchen.stock()==before
    egg=next(x for x in before if x['name']=='egg')
    kitchen.client.patch('/api/inventory/'+egg['id'],headers=kitchen.alice,json={'quantity':1,'unit':'pcs'})
    assert kitchen.client.get(path,headers=kitchen.alice).json()==[]

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


def test_unknown_measurements_and_current_exclusions_are_not_claimed_cookable(kitchen):
    from sqlalchemy import select
    from fridgely_recipes.storage import RecipeIngredient
    kitchen.add('rice',150,'g');kitchen.add('egg',2)
    kitchen.client.put('/api/profile/preferences',headers=kitchen.alice,json={'dietary':[],'allergens':['egg']})
    assert kitchen.client.get('/api/surprise-recipes',headers=kitchen.alice).json()==[]
    kitchen.client.put('/api/profile/preferences',headers=kitchen.alice,json={'dietary':[],'allergens':[]})
    with kitchen.client.app.state.sessions() as session,session.begin():
        row=session.scalar(select(RecipeIngredient).where(RecipeIngredient.recipe_id==kitchen.recipe_id,RecipeIngredient.position==0))
        row.amount='1 cup'
    assert kitchen.client.get('/api/surprise-recipes',headers=kitchen.alice).json()==[]

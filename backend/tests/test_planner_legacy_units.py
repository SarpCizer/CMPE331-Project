from fractions import Fraction
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from fridgely_app.meal_planner import scaled_measurements
from fridgely_recipes.storage import RecipeIngredient
from test_recipe_consumption import kitchen


@pytest.mark.parametrize('amount,display,dimension,base',[
    ('150g','75 g','mass',75),('0.4kg','0.2 kg','mass',200),
    ('500ml','250 ml','volume',250),('1L','0.5 L','volume',500),
    (' 150 G ','75 g','mass',75),('500\tML','250 ml','volume',250),
    ('2','1 pcs','pcs',1),('2pcs','1 pcs','pcs',1),('150 g','75 g','mass',75),
])
def test_scaled_legacy_measurement_keeps_recognized_source_unit(amount,display,dimension,base):
    recipe=SimpleNamespace(servings=2,ingredients=['item'],ingredientAmounts=[amount])
    measured,shown=scaled_measurements(recipe,1)
    assert measured==[('item',(dimension,Fraction(base)))]
    assert shown==[display]


def test_saved_legacy_recipe_shows_same_dimension_as_shopping(kitchen):
    with kitchen.client.app.state.sessions() as session,session.begin():
        rows=session.scalars(select(RecipeIngredient).where(RecipeIngredient.recipe_id==kitchen.recipe_id)
            .order_by(RecipeIngredient.position)).all()
        rows[0].amount='150g';rows[1].amount='2pcs'
    result=kitchen.client.put('/api/weekly-plan/0/dish-1',headers=kitchen.alice,
        json={'weekStart':'2026-11-23','recipeId':kitchen.recipe_id,'servings':1})
    assert result.status_code==200
    entry,=result.json()['entries']
    assert entry['scaledAmounts']==['75 g','1 pcs']
    shopping=kitchen.client.post('/api/weekly-plan/shopping-items',headers=kitchen.alice,
        json={'weekStart':'2026-11-23'}).json()['shopping']
    assert {x['name']:(x['quantity'],x['unit']) for x in shopping}=={'rice':(75,'g'),'egg':(1,'pcs')}
    assert kitchen.stock()==[]

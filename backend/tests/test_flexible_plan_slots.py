from test_recipe_consumption import kitchen


def test_user_adds_independent_dishes_without_fixed_meal_categories(kitchen):
    for slot,servings in [('dish-1',1),('dish-2',4),('dish-3',2),('dish-4',1),('dish-5',3)]:
        response=kitchen.client.put(f'/api/weekly-plan/0/{slot}',headers=kitchen.alice,
            json={'weekStart':'2026-11-23','recipeId':kitchen.recipe_id,'servings':servings})
        assert response.status_code==200
    entries=response.json()['entries']
    assert [entry['meal'] for entry in entries]==[f'dish-{i}' for i in range(1,6)]
    assert [entry['servings'] for entry in entries]==[1,4,2,1,3]
    assert kitchen.client.put('/api/weekly-plan/1/dish-1',headers=kitchen.alice,
        json={'weekStart':'2026-11-23','recipeId':kitchen.recipe_id,'servings':2}).status_code==200
    assert kitchen.stock()==[]

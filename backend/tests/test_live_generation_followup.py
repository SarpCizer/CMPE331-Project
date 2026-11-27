"""Regressions for source-4284552 live latency/content failures; no live AI."""
import asyncio
import json
import httpx
import pytest
from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput, RecipeError, validate_batch
from test_cloudflare_recipe_provider import RECIPE


def test_compact_parallel_wire_round_trips_more_than_six_full_recipes():
    async def scenario():
        calls=[]
        async def respond(request):
            payload=json.loads(request.content);body=json.loads(payload['messages'][1]['content'])
            calls.append((payload,body))
            rows=[{'t':body['priorityIngredients'][0]+str(i),'i':RECIPE['ingredients'],
                'a':RECIPE['ingredientAmounts'],'s':RECIPE['steps'],
                'm':20,'k':325,'p':2} for i in range(4)]
            return httpx.Response(200,json={'success':True,'result':{'response':{'recipes':rows}}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            data=GenerationInput(tuple(f'food-{i}' for i in range(14)),('vegan',),('peanut',),
                tuple((f'food-{i}',2,'pcs') for i in range(14)))
            rows=await CloudflareRecipeProvider(client,account_id='synthetic',api_token='synthetic').generate(data)
        assert rows is not None and len(rows)==16
        for recipe in validate_batch(rows,data.allergens):
            assert recipe.ingredients==RECIPE['ingredients']
            assert recipe.ingredientAmounts==RECIPE['ingredientAmounts']
            assert recipe.steps==RECIPE['steps'] and recipe.servings==2
        for payload,body in calls:
            assert body['ingredients']==list(data.ingredients) and len(body['availableAmounts'])==14
            assert body['allergens']==['peanut'] and body['dietary']==['vegan']
            fields=payload['response_format']['json_schema']['properties']['recipes']['items']['properties']
            assert set(fields)=={'t','i','a','s','m','k','p'}
            assert payload['max_tokens']==3200 and 'no fixed recipe count' in payload['messages'][0]['content']
    asyncio.run(scenario())


@pytest.mark.parametrize('candidate',[
    {**RECIPE,'ingredients':['rice','salt'],'ingredientAmounts':['150 g','1 pack']},
    {**RECIPE,'title':'Strawberry sugar toast','ingredients':['strawberry','sugar','butter'],
        'ingredientAmounts':['100 g','20 g','20 g'],'steps':['Butter toast.','Add the strawberries.']},
])
def test_observed_unmeasured_seasoning_or_missing_toast_ingredient_is_rejected(candidate):
    with pytest.raises(RecipeError) as failure:validate_batch([candidate],())
    assert failure.value.status==502


@pytest.mark.parametrize('ingredient,temperature',[('chicken','74'),('fish','63')])
def test_protein_steps_include_thermometer_endpoint_without_losing_generated_steps(ingredient,temperature):
    candidate={**RECIPE,'ingredients':[ingredient,'salt'],'ingredientAmounts':['200 g','2 g'],
        'steps':['Heat the pan.','Cook until browned.','Serve hot.']}
    recipe,=validate_batch([candidate],())
    assert all(step in recipe.steps for step in candidate['steps'])
    assert any('thermometer' in step.casefold() and temperature in step for step in recipe.steps)


def test_known_bread_and_measured_salt_remain_accepted():
    candidate={**RECIPE,'title':'Strawberry toast','ingredients':['bread','strawberry','salt'],
        'ingredientAmounts':['2 pcs','100 g','1 g'],'steps':['Toast the bread.','Top with strawberries.']}
    recipe,=validate_batch([candidate],())
    assert recipe.ingredients==candidate['ingredients'] and recipe.steps==candidate['steps']

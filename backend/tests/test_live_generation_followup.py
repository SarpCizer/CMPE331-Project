"""Regressions for source-4284552 live latency/content failures; no live AI."""
import asyncio
import json
import httpx
import pytest
from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput, RecipeError, validate_batch
from test_cloudflare_recipe_provider import RECIPE
from test_cloudflare_recipe_provider import cloudflare_host, sign_in, cloudflare_result
from fastapi.testclient import TestClient


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


def test_toasting_seeds_does_not_require_bread():
    candidate={**RECIPE,'title':'Toasted seed topping','ingredients':['sesame'],
        'ingredientAmounts':['10 g'],'steps':['Toast the sesame seeds in a dry pan.']}
    recipe,=validate_batch([candidate],())
    assert recipe.steps==candidate['steps']


def test_legacy_seasoning_that_needs_manual_measure_review_can_still_be_displayed():
    # Existing wheel cards deliberately support legacy amounts that cannot yet
    # be converted into cooking deductions. The production provider adapter
    # separately rejects nonmetric new AI output before it reaches this layer.
    candidate={**RECIPE,'ingredients':['rice','salt'],'ingredientAmounts':['150 g','1 pinch']}
    recipe,=validate_batch([candidate],())
    assert recipe.ingredientAmounts==candidate['ingredientAmounts']


def test_kilogram_salt_dose_is_not_accepted_as_a_measured_recipe():
    candidate={**RECIPE,'ingredients':['rice','salt'],'ingredientAmounts':['150 g','1 kg']}
    with pytest.raises(RecipeError):validate_batch([candidate],())


def test_discovery_withholds_unusable_content_but_saves_complete_usable_choices_atomically(cloudflare_host):
    bad={**RECIPE,'ingredients':['rice','salt'],'ingredientAmounts':['150 g','1 pack']}
    cloudflare_host.respond=lambda:cloudflare_result({'recipes':[RECIPE,bad]})
    with TestClient(cloudflare_host.new_app()) as client:
        headers=sign_in(client)
        before=client.get('/api/inventory',headers=headers).json()
        response=client.post('/api/recipes/generate',headers=headers,json={})
        assert response.status_code==200
        rows=response.json()
        assert len(rows)==1 and rows[0]['ingredientAmounts']==RECIPE['ingredientAmounts']
        assert rows[0]['ingredients']==RECIPE['ingredients'] and rows[0]['steps']==RECIPE['steps']
        assert client.get('/api/history',headers=headers).json()==[]
        assert client.get('/api/recipes/'+rows[0]['id'],headers=headers).json()==rows[0]
        assert client.get('/api/inventory',headers=headers).json()==before
        assert [entry['recipe']['id'] for entry in client.get('/api/history',headers=headers).json()]==[rows[0]['id']]


@pytest.mark.parametrize('amount',['0 g','1 cup','NaN g','1.5 pcs'])
def test_compact_wire_keeps_existing_measure_validation(amount):
    async def scenario():
        async def respond(request):
            row={'t':'Invalid rice','i':['rice'],'a':[amount],'s':['Cook the rice.'],
                'm':20,'k':300,'p':2}
            return httpx.Response(200,json={'success':True,'result':{'response':{'recipes':[row]}}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            assert await CloudflareRecipeProvider(client,account_id='synthetic',api_token='synthetic').generate(
                GenerationInput(tuple('abcdefgh'),(),())) is None
    asyncio.run(scenario())

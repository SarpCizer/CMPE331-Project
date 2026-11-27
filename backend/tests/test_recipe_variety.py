"""Full-fridge input and broader, preference-aware provider requests."""
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from test_cloudflare_recipe_provider import cloudflare_host, sign_in, cloudflare_result, RECIPE
from fridgely_recipes.provider import recipe_instructions
from fridgely_recipes.service import GenerationInput

@pytest.mark.parametrize('provider', ['cloudflare','openai'])
def test_six_suggestions_keep_every_stocked_ingredient_including_recent_fish(cloudflare_host, monkeypatch, provider):
    monkeypatch.setenv('RECIPE_PROVIDER', provider)
    batch=[{**RECIPE, 'title':f'Idea {i+1}'} for i in range(6)]
    cloudflare_host.respond=lambda: cloudflare_result({'recipes':batch}) if provider=='cloudflare' else httpx.Response(200,json={
        'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps({'recipes':batch})}]}]})
    with TestClient(cloudflare_host.new_app()) as client:
        headers=sign_in(client)
        for name in ['milk','potatoes','egg','banana','tomatoes','strawberry','sugar','butter','salt','eggplant','olives','chicken','fish']:
            assert client.post('/api/inventory',headers=headers,json={'name':name,'quantity':2,'unit':'pcs'}).status_code==201
        before=client.get('/api/inventory',headers=headers).json()
        result=client.post('/api/recipes/generate',headers=headers,json={})
        assert result.status_code==200 and len(result.json())==6
        assert client.get('/api/inventory',headers=headers).json()==before
        for recipe in result.json():
            assert client.get('/api/recipes/'+recipe['id'],headers=headers).json()['title']==recipe['title']
    payload=json.loads(cloudflare_host.requests[0].content)
    instructions=payload['messages'][0]['content'] if provider=='cloudflare' else payload['instructions']
    data=json.loads(payload['messages'][1]['content'] if provider=='cloudflare' else payload['input'])
    assert data['ingredients']==[item['name'] for item in before]
    assert len(data['ingredients'])==14 and data['ingredients'][-1]=='fish'
    assert {'name':'fish','quantity':2,'unit':'pcs'} in data['availableAmounts']
    assert data['dietary']==['vegan'] and data['allergens']==['peanut']
    assert ('three distinct' if provider=='cloudflare' else 'six distinct') in instructions
    assert 'main ingredients' in instructions and 'end of the inventory' in instructions
    assert 'restrictions take priority' in instructions
    assert payload['max_tokens' if provider=='cloudflare' else 'max_output_tokens']==(3200 if provider=='cloudflare' else 4800)
    assert len(cloudflare_host.requests)==(2 if provider=='cloudflare' else 1)


def test_weekly_dish_keeps_single_recipe_guidance():
    data=GenerationInput(('fish',),(),(),requested_dish='Baked fish',requested_servings=2)
    instructions=recipe_instructions(data)
    assert 'exactly one recipe' in instructions
    assert 'six distinct' not in instructions

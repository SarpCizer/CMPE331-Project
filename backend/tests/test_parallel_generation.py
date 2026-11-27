"""Concurrency and data-preservation assertions with controlled outbound requests."""
import asyncio
import json
import httpx
import pytest
from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput
from test_cloudflare_recipe_provider import RECIPE


def test_large_fridge_groups_overlap_and_keep_full_input_and_all_recipe_fields():
    async def scenario():
        arrived=[];ready=asyncio.Event()
        names=('rice','milk','egg','tomatoes','banana','butter','chicken','fish')
        async def respond(request):
            payload=json.loads(request.content);data=json.loads(payload['messages'][1]['content'])
            arrived.append((payload,data))
            if len(arrived)==2:ready.set()
            await asyncio.wait_for(ready.wait(),.5)
            group=data['priorityIngredients']
            return httpx.Response(200,json={'success':True,'result':{'response':{'recipes':[
                {**RECIPE,'title':f'{group[0]} recipe {i}'} for i in range(3)]}}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider=CloudflareRecipeProvider(client,account_id='synthetic',api_token='synthetic')
            data=GenerationInput(names,('vegetarian',),('peanut',),tuple((name,2,'pcs') for name in names))
            result=await provider.generate(data)
        assert len(result)==6 and len(arrived)==2
        assert set(arrived[0][1]['priorityIngredients']) | set(arrived[1][1]['priorityIngredients'])==set(names)
        for payload,body in arrived:
            assert body['ingredients']==list(names)
            assert body['dietary']==['vegetarian'] and body['allergens']==['peanut']
            assert len(body['availableAmounts'])==8
            assert 'three distinct' in payload['messages'][0]['content']
            assert payload['max_tokens']==3200
        for recipe in result:
            assert recipe['steps']==RECIPE['steps'] and recipe['ingredientAmounts']==RECIPE['ingredientAmounts']
            assert recipe['servings']==RECIPE['servings']
    asyncio.run(scenario())


def test_failed_parallel_group_cancels_its_sibling():
    async def scenario():
        started=asyncio.Event();cancelled=asyncio.Event()
        async def respond(request):
            data=json.loads(json.loads(request.content)['messages'][1]['content'])
            if data['priorityIngredients'][0]=='a':
                await started.wait()
                return httpx.Response(429,json={'error':'synthetic quota'})
            started.set()
            try:await asyncio.sleep(10)
            except asyncio.CancelledError:cancelled.set();raise
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider=CloudflareRecipeProvider(client,account_id='synthetic',api_token='synthetic')
            with pytest.raises(ExceptionGroup):
                await asyncio.wait_for(provider.generate(GenerationInput(tuple('abcdefgh'),(),())),1)
        assert cancelled.is_set()
    asyncio.run(scenario())

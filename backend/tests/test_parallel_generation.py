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
            assert 'no fixed recipe count' in payload['messages'][0]['content']
            assert payload['max_tokens']==3200
        for recipe in result:
            assert recipe['steps']==RECIPE['steps'] and recipe['ingredientAmounts']==RECIPE['ingredientAmounts']
            assert recipe['servings']==RECIPE['servings']
    asyncio.run(scenario())


def test_non_retryable_auth_failure_cancels_its_sibling():
    async def scenario():
        started=asyncio.Event();cancelled=asyncio.Event()
        async def respond(request):
            data=json.loads(json.loads(request.content)['messages'][1]['content'])
            if data['priorityIngredients'][0]=='a':
                await started.wait()
                return httpx.Response(403,json={'error':'synthetic authorization failure'})
            started.set()
            try:await asyncio.sleep(10)
            except asyncio.CancelledError:cancelled.set();raise
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider=CloudflareRecipeProvider(client,account_id='synthetic',api_token='synthetic')
            with pytest.raises(httpx.HTTPStatusError):
                await asyncio.wait_for(provider.generate(GenerationInput(tuple('abcdefgh'),(),())),1)
        assert cancelled.is_set()
    asyncio.run(scenario())


def test_service_deadline_cancels_both_requests_and_writes_nothing():
    from fridgely_recipes.service import RecipeGenerationService, RecipeError

    async def scenario():
        started = []
        cancelled = []
        writes = []

        async def respond(request):
            started.append(request)
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.append(request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic')
            service = RecipeGenerationService(
                lambda owner: GenerationInput(tuple('abcdefgh'), (), ()), provider,
                lambda *args: writes.append(args), timeout_seconds=.05,
            )
            with pytest.raises(RecipeError) as failure:
                await service.generate('owner')
        assert failure.value.status == 503 and failure.value.retryable
        assert len(started) == len(cancelled) == 2
        assert writes == []

    asyncio.run(scenario())


@pytest.mark.parametrize('bad_recipe, expected_status', [
    ({**RECIPE, 'steps': []}, 502),
    ({**RECIPE, 'ingredients': ['peanut'], 'ingredientAmounts': ['10 g']}, 422),
    ({**RECIPE, 'ingredientAmounts': ['1 cup', '2 pcs']}, 502),
])
def test_one_bad_group_rejects_every_recipe_before_saving(bad_recipe, expected_status):
    from fridgely_recipes.service import RecipeGenerationService, RecipeError

    async def scenario():
        writes = []

        def respond(request):
            data = json.loads(json.loads(request.content)['messages'][1]['content'])
            recipe = RECIPE if data['priorityIngredients'][0] == 'a' else bad_recipe
            return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': [recipe]}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic')
            service = RecipeGenerationService(
                lambda owner: GenerationInput(tuple('abcdefgh'), (), ('peanut',)), provider,
                lambda *args: writes.append(args),
            )
            with pytest.raises(RecipeError) as failure:
                await service.generate('owner')
        assert failure.value.status == expected_status
        assert writes == []

    asyncio.run(scenario())


def test_duplicate_results_do_not_hide_distinct_preparations_with_same_title():
    async def scenario():
        requests = []

        def respond(request):
            requests.append(request)
            other = {**RECIPE, 'steps': ['Bake the rice and tomato']}
            return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': [RECIPE, other]}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic').generate(
                GenerationInput(tuple('abcdefgh'), (), ()))
        assert len(requests) == 2
        assert result == [RECIPE, {**RECIPE, 'steps': ['Bake the rice and tomato']}]

    asyncio.run(scenario())


def test_requested_weekly_dish_with_large_fridge_uses_one_request():
    async def scenario():
        requests = []

        def respond(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': [RECIPE]}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic').generate(
                GenerationInput(tuple('abcdefgh'), (), (), requested_dish='Tomato rice', requested_servings=2))
        payload, = requests
        body = json.loads(payload['messages'][1]['content'])
        assert body['requestedServings'] == 2 and body['requestedDish'] == 'Tomato rice'
        assert 'priorityIngredients' not in body and payload['max_tokens'] == 2400
        assert result == [RECIPE]

    asyncio.run(scenario())


def test_large_pantry_accepts_more_than_six_recipes_without_numeric_prompt_target():
    async def scenario():
        requests = []
        names = tuple(f'food-{i}' for i in range(14))

        def respond(request):
            payload = json.loads(request.content)
            body = json.loads(payload['messages'][1]['content'])
            requests.append((payload, body))
            # Provider can return any useful batch size, including >6 in total.
            recipes = [{**RECIPE, 'title': f'{body["priorityIngredients"][0]} dish {i}'} for i in range(4)]
            return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': recipes}}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic').generate(
                GenerationInput(names, (), ()))
        assert len(requests) == 4 and len(result) == 16
        assert set().union(*(set(body['priorityIngredients']) for _, body in requests)) == set(names)
        for payload, body in requests:
            instructions = payload['messages'][0]['content']
            assert 'six distinct' not in instructions and 'three distinct' not in instructions
            assert 'no fixed recipe count' in instructions
            assert body['ingredients'] == list(names)

    asyncio.run(scenario())

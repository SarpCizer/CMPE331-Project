"""US-07/08/09: whole, validated recipes survive unrelated transport failure."""
import asyncio
import json

import httpx
import pytest

from fridgely_recipes import provider as module
from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput, RecipeError, RecipeGenerationService
from test_cloudflare_recipe_provider import RECIPE

NAMES = tuple('abcdefgh')


def request_group(request):
    return json.loads(json.loads(request.content)['messages'][1]['content'])['priorityIngredients'][0]


def batch(title):
    return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': [
        {**RECIPE, 'title': f'{title} dish {i}'} for i in range(4)]}}})


def test_slow_group_does_not_discard_completed_whole_recipes(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_DEADLINE_SECONDS', .04, raising=False)

    async def scenario():
        cancelled = asyncio.Event()
        async def respond(request):
            if request_group(request) == 'a':
                return batch('Complete')
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.set()
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await asyncio.wait_for(CloudflareRecipeProvider(client,
                account_id='test', api_token='test').generate(GenerationInput(NAMES, (), ())), .5)
        assert len(result) == 4 and result.incomplete is True
        assert cancelled.is_set()
        assert all(row['steps'] == RECIPE['steps'] for row in result)
    asyncio.run(scenario())


def test_transient_group_retries_without_repeating_completed_siblings(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_RETRY_DELAY_SECONDS', 0, raising=False)

    async def scenario():
        calls = {'a': 0, 'b': 0}
        async def respond(request):
            name = request_group(request)
            calls[name] += 1
            if name == 'a' and calls[name] == 1:
                return httpx.Response(503, text='private upstream diagnostics')
            return batch(name)
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='test', api_token='test').generate(
                GenerationInput(NAMES, (), ()))
        assert calls == {'a': 2, 'b': 1}
        assert len(result) == 8 and result.incomplete is False
    asyncio.run(scenario())


def test_unavailable_group_does_not_cancel_healthy_sibling(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_RETRY_DELAY_SECONDS', 0, raising=False)

    async def scenario():
        async def respond(request):
            if request_group(request) == 'a':
                return httpx.Response(429, text='private quota detail')
            await asyncio.sleep(.01)
            return batch('Healthy')
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='test', api_token='test')
            writes = []
            service = RecipeGenerationService(lambda owner: GenerationInput(NAMES, (), ()), provider,
                lambda owner, rows: writes.append((owner, rows)))
            result = await service.generate('owner')
        assert len(result) == 4 and result.incomplete is True
        assert len(writes) == 1 and writes[0][0] == 'owner'
    asyncio.run(scenario())


def test_all_groups_unavailable_remains_retryable_without_writes(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_RETRY_DELAY_SECONDS', 0, raising=False)

    async def scenario():
        async def respond(request):
            raise httpx.ReadTimeout('private synthetic detail', request=request)
        writes = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='test', api_token='test')
            service = RecipeGenerationService(lambda owner: GenerationInput(NAMES, (), ()), provider,
                lambda *args: writes.append(args))
            with pytest.raises(RecipeError) as failure:
                await service.generate('owner')
        assert failure.value.status == 503 and failure.value.retryable
        assert 'private' not in str(failure.value) and writes == []
    asyncio.run(scenario())


def test_incomplete_batch_never_bypasses_exclusions_or_atomic_validation(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_DEADLINE_SECONDS', .04, raising=False)

    async def scenario():
        async def respond(request):
            if request_group(request) == 'a':
                return httpx.Response(200, json={'success': True, 'result': {'response': {'recipes': [
                    {**RECIPE, 'ingredients': ['peanut'], 'ingredientAmounts': ['10 g']}]}}})
            await asyncio.sleep(10)
        writes = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='test', api_token='test')
            service = RecipeGenerationService(lambda owner: GenerationInput(NAMES, (), ('peanut',)), provider,
                lambda *args: writes.append(args))
            with pytest.raises(RecipeError) as failure:
                await asyncio.wait_for(service.generate('owner'), .5)
        assert failure.value.status == 422 and writes == []
    asyncio.run(scenario())


def test_compact_prompt_has_one_unambiguous_amount_contract():
    async def scenario():
        async def respond(request):
            payload = json.loads(request.content)
            prompt = payload['messages'][0]['content']
            assert 'Supply a cooking amount object' not in prompt
            assert 'measured amount strings' in prompt
            assert payload['max_tokens'] == 3200
            return batch(request_group(request))
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            await CloudflareRecipeProvider(client, account_id='test', api_token='test').generate(
                GenerationInput(NAMES, (), ()))
    asyncio.run(scenario())


from fastapi.testclient import TestClient
from sqlalchemy import func, select
from fridgely_recipes.storage import Recipe
from test_cloudflare_recipe_provider import cloudflare_host, sign_in


def test_incomplete_transport_result_is_explicit_and_saved_atomically(cloudflare_host, monkeypatch):
    monkeypatch.setattr(module, 'GROUP_DEADLINE_SECONDS', .04)
    arrived = 0
    async def respond():
        nonlocal arrived
        arrived += 1
        if arrived == 1:
            return batch('Ready')
        await asyncio.sleep(10)
    cloudflare_host.respond = respond
    app = cloudflare_host.new_app()
    with TestClient(app) as client:
        headers = sign_in(client)
        for name in 'abcdefg':
            assert client.post('/api/inventory', headers=headers, json={'name': name}).status_code == 201
        before = client.get('/api/inventory', headers=headers).json()
        response = client.post('/api/recipes/generate', headers=headers, json={})
        assert response.status_code == 200
        assert response.headers['X-Fridgely-Generation-Incomplete'] == 'true'
        rows = response.json()
        assert len(rows) == 4
        assert client.get('/api/inventory', headers=headers).json() == before
        assert client.get('/api/history', headers=headers).json() == []
        with app.state.sessions() as session:
            assert session.scalar(select(func.count()).select_from(Recipe)) == 4
        for recipe in rows:
            assert client.get('/api/recipes/' + recipe['id'], headers=headers).json() == recipe
            assert client.get('/api/recipes/' + recipe['id']).status_code == 401


def test_completed_bad_response_remains_hard_failure_with_no_save(monkeypatch):
    monkeypatch.setattr(module, 'GROUP_DEADLINE_SECONDS', .04)
    async def scenario():
        async def respond(request):
            if request_group(request) == 'a':
                return batch('Good')
            return httpx.Response(200, json={'success': True, 'result': {'response': 'not valid JSON'}})
        writes = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            service = RecipeGenerationService(lambda owner: GenerationInput(NAMES, (), ()),
                CloudflareRecipeProvider(client, account_id='test', api_token='test'),
                lambda *args: writes.append(args))
            with pytest.raises(RecipeError) as failure:
                await service.generate('owner')
        assert failure.value.status == 502 and writes == []
    asyncio.run(scenario())


def test_declared_upstream_failure_does_not_erase_healthy_group(caplog):
    async def scenario():
        async def respond(request):
            if request_group(request) == 'a':
                return httpx.Response(200, json={'success': False, 'errors': ['private provider detail']})
            await asyncio.sleep(.01)
            return batch('Healthy')
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='test', api_token='test').generate(
                GenerationInput(NAMES, (), ()))
        assert len(result) == 4 and result.incomplete is True
    asyncio.run(scenario())
    assert 'private provider detail' not in caplog.text


@pytest.mark.parametrize('transport_error', [httpx.ReadError, httpx.RemoteProtocolError])
def test_disconnected_group_retries_and_preserves_completed_sibling(transport_error, monkeypatch, caplog):
    monkeypatch.setattr(module, 'GROUP_RETRY_DELAY_SECONDS', 0)
    async def scenario():
        calls = {'a': 0, 'b': 0}
        async def respond(request):
            name = request_group(request)
            calls[name] += 1
            if name == 'a':
                return batch('Completed')
            await asyncio.sleep(.01)
            raise transport_error('private synthetic disconnect', request=request)
        writes = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            service = RecipeGenerationService(lambda owner: GenerationInput(NAMES, (), ()),
                CloudflareRecipeProvider(client, account_id='test', api_token='test'),
                lambda owner, recipes: writes.append((owner, recipes)))
            rows = await service.generate('owner')
        assert calls == {'a': 1, 'b': 2}
        assert len(rows) == 4 and rows.incomplete is True
        assert len(writes) == 1 and writes[0][0] == 'owner'
        assert len(writes[0][1]) == 4
    asyncio.run(scenario())
    assert 'private synthetic disconnect' not in caplog.text

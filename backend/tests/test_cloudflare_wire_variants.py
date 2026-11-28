"""Provider-boundary format regressions; synthetic transport, never live credentials."""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest

from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput, RecipeError, RecipeGenerationService, validate_batch


ROW = {'t': 'Tomato rice', 'i': ['rice', 'tomatoes'], 'a': ['150 g', '100 g'],
       's': ['Rinse the rice.', 'Simmer rice and chopped tomatoes in water until cooked.'],
       'm': 25, 'k': 300, 'p': 2}
ALIASES = {'t': 'title', 'i': 'ingredients', 'a': 'ingredientAmounts', 's': 'steps',
           'm': 'cookingMinutes', 'k': 'caloriesPerServing', 'p': 'servings'}
DATA = GenerationInput(tuple('abcdefgh'), ('vegan',), ('peanut',),
                       tuple((name, 2, 'pcs') for name in 'abcdefgh'))


def generate(raw, usage=None, *, service=False):
    writes = []
    async def scenario():
        def respond(request):
            posted = json.loads(request.content)
            body = json.loads(posted['messages'][1]['content'])
            assert body['ingredients'] == list(DATA.ingredients)
            assert body['dietary'] == ['vegan'] and body['allergens'] == ['peanut']
            assert len(body['availableAmounts']) == 8
            result = {'response': raw}
            if usage is not None:
                result['usage'] = usage
            return httpx.Response(200, json={'success': True, 'result': result})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic')
            if service:
                host = RecipeGenerationService(lambda owner: DATA, provider,
                    lambda *args: writes.append(args))
                return await host.generate('synthetic-owner')
            return await provider.generate(DATA)
    return asyncio.run(scenario()), writes


@pytest.mark.parametrize('wrapper', ['json-fence', 'plain-fence', 'array', 'single', 'mixed', 'extra', 'same-alias'])
def test_unambiguous_complete_records_keep_every_field(wrapper):
    row = deepcopy(ROW)
    raw = {'recipes': [row]}
    if wrapper == 'json-fence': raw = '```json\n' + json.dumps(raw) + '\n```'
    if wrapper == 'plain-fence': raw = '```\n' + json.dumps(raw) + '\n```'
    if wrapper == 'array': raw = [row]
    if wrapper == 'single': raw = row
    if wrapper == 'mixed': row['title'] = row.pop('t'); row['steps'] = row.pop('s')
    if wrapper == 'extra': row.update(id='provider-cannot-choose-id', commentary='ignored metadata')
    if wrapper == 'same-alias': row['title'] = row['t']
    rows, _ = generate(raw)
    assert rows is not None and len(rows) == 1
    recipe, = validate_batch(rows, DATA.allergens)
    assert recipe.title == ROW['t'] and recipe.ingredients == ROW['i']
    assert recipe.ingredientAmounts == ROW['a'] and recipe.steps == ROW['s']
    assert (recipe.cookingMinutes, recipe.caloriesPerServing, recipe.servings) == (25, 300, 2)
    assert recipe.id != 'provider-cannot-choose-id'


@pytest.mark.parametrize('amount, expected', [
    ('150g', '150 g'), ('150\u00a0g', '150 g'), ('150 grams', '150 g'),
    ('150 milliliters', '150 ml'), ('150mL', '150 ml'), ('0.15l', '0.15 L'),
    ({'quantity': 150, 'unit': 'grams'}, '150 g'), ('2 pieces', '2 pcs'),
])
def test_explicit_measurement_spelling_does_not_change_quantity(amount, expected):
    row = {**ROW, 'a': [amount, '100 g']}
    rows, _ = generate({'recipes': [row]})
    assert rows is not None and rows[0]['ingredientAmounts'] == [expected, '100 g']


@pytest.mark.parametrize('usage', [None, {}, {'completion_tokens': 3199},
                                  {'completion_tokens': '3200'}, {'completion_tokens': True}])
def test_unconfirmed_truncation_never_recovers_or_writes(usage):
    raw = '{"recipes":[' + json.dumps(ROW) + ',{"t":"unfinished'
    with pytest.raises(RecipeError) as error:
        generate(raw, usage, service=True)
    assert error.value.status == 502


def test_confirmed_token_limit_keeps_all_complete_records_and_no_partial_recipe(caplog):
    rows = [{**ROW, 't': f'Complete rice preparation {i}'} for i in range(9)]
    raw = '{"recipes":[' + ','.join(map(json.dumps, rows)) + ',{"t":"unfinished-private-sentinel'
    result, _ = generate(raw, {'completion_tokens': 3200})
    assert result is not None and len(result) == 9
    checked = validate_batch(result, DATA.allergens)
    assert [recipe.title for recipe in checked] == [row['t'] for row in rows]
    assert all(recipe.ingredientAmounts == ROW['a'] and recipe.steps == ROW['s'] for recipe in checked)
    assert 'unfinished-private-sentinel' not in caplog.text


@pytest.mark.parametrize('raw', [
    '{"recipes":[{"t":"unfinished',
    '{"recipes":[' + json.dumps({**ROW, 'a': ['1 cup', '100 g']}) + ',{"t":"unfinished',
    '{"recipes":[' + json.dumps({**ROW, 'title': 'conflict'}) + ',{"t":"unfinished',
    'prefix ' + json.dumps({'recipes': [ROW]}),
    '{"recipes":[' + json.dumps(ROW) + ' garbage',
    ' ' * 262145,
])
def test_token_limit_never_repairs_invalid_complete_candidates_or_arbitrary_text(raw):
    with pytest.raises(RecipeError) as error:
        generate(raw, {'completion_tokens': 3200}, service=True)
    assert error.value.status == 502


@pytest.mark.parametrize('change', [
    {'title': 'conflicts with short title'}, {'s': []}, {'p': 0},
    {'a': ['0g', '100 g']}, {'a': ['1.5 pieces', '100 g']},
    {'a': ['1 cup', '100 g']}, {'a': ['NaN g', '100 g']},
    {'a': ['1000001g', '100 g']}, {'i': ['peanut', 'tomatoes']},
])
def test_normalization_keeps_validation_and_allergen_rejection_atomic(change, caplog):
    writes = []
    async def scenario():
        def respond(request):
            return httpx.Response(200, json={'success': True, 'result': {
                'response': {'recipes': [ROW, {**ROW, **change}]}}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = CloudflareRecipeProvider(client, account_id='private-secret-sentinel', api_token='private-secret-sentinel')
            service = RecipeGenerationService(lambda owner: DATA, provider, lambda *args: writes.append(args))
            with pytest.raises(RecipeError) as error:
                await service.generate('synthetic-owner')
            assert error.value.status in (422, 502)
    asyncio.run(scenario())
    assert writes == [] and 'private-secret-sentinel' not in caplog.text


def test_missing_recipe_field_is_not_invented():
    row = deepcopy(ROW); del row['s']
    with pytest.raises(RecipeError): generate({'recipes': [row]}, service=True)


def test_requested_weekly_dish_never_recovers_an_unfinished_batch():
    async def scenario():
        def respond(request):
            return httpx.Response(200, json={'success': True, 'result': {
                'response': '{"recipes":[' + json.dumps(ROW) + ',{"t":"unfinished',
                'usage': {'completion_tokens': 2400}}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            data = GenerationInput(DATA.ingredients, (), (), requested_dish='Tomato rice', requested_servings=2)
            return await CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic').generate(data)
    assert asyncio.run(scenario()) is None

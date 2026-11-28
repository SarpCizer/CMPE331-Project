"""Regressions for actual fd293bb output: undosed extras and lost usable choices."""
import asyncio
import json

from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy import func, select

from fridgely_recipes.provider import CloudflareRecipeProvider
from fridgely_recipes.service import GenerationInput, RecipeError, validate_batch
from fridgely_recipes.storage import Recipe
from test_cloudflare_recipe_provider import RECIPE, cloudflare_host, cloudflare_result, sign_in


def test_valid_empty_complementary_group_does_not_discard_other_complete_recipes():
    async def scenario():
        def respond(request):
            data = json.loads(json.loads(request.content)['messages'][1]['content'])
            rows = [] if data['priorityIngredients'][0] == 'a' else [RECIPE]
            return cloudflare_result({'recipes': rows})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            result = await CloudflareRecipeProvider(client, account_id='synthetic', api_token='synthetic').generate(
                GenerationInput(tuple('abcdefgh'), (), ('fish',)))
        assert result == [RECIPE]
    asyncio.run(scenario())


@pytest.mark.parametrize('extra', ['Serve with crusty bread.', 'Garnish with chopped fresh herbs.',
                                  'Garnish with lemon wedges if desired.'])
def test_optional_unlisted_side_or_garnish_is_omitted_without_inventing_ingredients(extra):
    candidate = {**RECIPE, 'steps': ['Cook the rice.', extra]}
    recipe, = validate_batch([candidate], ())
    assert recipe.steps == ['Cook the rice.']
    assert recipe.ingredients == RECIPE['ingredients'] and recipe.ingredientAmounts == RECIPE['ingredientAmounts']


def test_listed_garnish_and_toasted_seeds_keep_their_preparation_steps():
    candidate = {**RECIPE, 'ingredients': ['sesame', 'tomato'], 'ingredientAmounts': ['10 g', '2 pcs'],
                 'steps': ['Toast the sesame seeds.', 'Garnish with tomato.']}
    recipe, = validate_batch([candidate], ())
    assert recipe.steps == candidate['steps']


def test_mandatory_unlisted_oil_cannot_be_converted_to_an_invented_dose():
    candidate = {**RECIPE, 'steps': ['Brush the tomato with oil.', 'Grill and serve.']}
    with pytest.raises(RecipeError) as failure:
        validate_batch([candidate], ())
    assert failure.value.status == 502


def test_discovery_retains_every_usable_recipe_and_withholds_undosed_extra(cloudflare_host, caplog):
    valid = [{**RECIPE, 'title': f'Complete preparation {i}'} for i in range(9)]
    bad = {**RECIPE, 'title': 'private-title-sentinel', 'steps': ['Brush the tomato with oil.', 'Grill.']}
    cloudflare_host.respond = lambda: cloudflare_result({'recipes': [*valid, bad]})
    app = cloudflare_host.new_app()
    with TestClient(app) as client:
        headers = sign_in(client)
        before = client.get('/api/inventory', headers=headers).json()
        response = client.post('/api/recipes/generate', headers=headers, json={})
        assert response.status_code == 200
        rows = response.json()
        assert [r['title'] for r in rows] == [r['title'] for r in valid]
        assert len(rows) == 9
        with app.state.sessions() as database:
            assert database.scalar(select(func.count()).select_from(Recipe)) == 9
        assert client.get('/api/history', headers=headers).json() == []
        for row in rows:
            assert row['ingredientAmounts'] == RECIPE['ingredientAmounts'] and row['steps'] == RECIPE['steps']
            assert client.get('/api/recipes/' + row['id'], headers=headers).json() == row
        assert client.get('/api/inventory', headers=headers).json() == before
        assert {entry['recipe']['title'] for entry in client.get('/api/history', headers=headers).json()} == {r['title'] for r in valid}
    assert 'private-title-sentinel' not in caplog.text


@pytest.mark.parametrize('candidate', [
    {**RECIPE, 'steps': ['Fry the tomato in oil.']},
    {**RECIPE, 'ingredients': ['rice', 'salt'], 'ingredientAmounts': ['150 g', '1 pack']},
    {**RECIPE, 'title': 'Fruit toast', 'ingredients': ['banana'], 'ingredientAmounts': ['1 pcs'], 'steps': ['Butter toast.']},
])
def test_all_content_candidates_unusable_returns_failure_without_stock_or_history_writes(cloudflare_host, candidate):
    cloudflare_host.respond = lambda: cloudflare_result({'recipes': [candidate]})
    with TestClient(cloudflare_host.new_app()) as client:
        headers = sign_in(client)
        before = client.get('/api/inventory', headers=headers).json()
        assert client.post('/api/recipes/generate', headers=headers, json={}).status_code == 502
        assert client.get('/api/inventory', headers=headers).json() == before
        assert client.get('/api/history', headers=headers).json() == []


@pytest.mark.parametrize('bad, status', [
    ({**RECIPE, 'steps': []}, 502),
    ({**RECIPE, 'ingredients': ['peanut'], 'ingredientAmounts': ['10 g'], 'steps': ['Fry in oil.']}, 422),
    ({**RECIPE, 'ingredientAmounts': ['1 cup', '2 pcs']}, 502),
])
def test_content_curation_never_skips_schema_measurement_or_allergen_failure(cloudflare_host, bad, status):
    cloudflare_host.respond = lambda: cloudflare_result({'recipes': [RECIPE, bad]})
    with TestClient(cloudflare_host.new_app()) as client:
        headers = sign_in(client)
        before = client.get('/api/inventory', headers=headers).json()
        assert client.post('/api/recipes/generate', headers=headers, json={}).status_code == status
        assert client.get('/api/inventory', headers=headers).json() == before
        assert client.get('/api/history', headers=headers).json() == []

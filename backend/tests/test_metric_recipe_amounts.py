import pytest
from fridgely_recipes.provider import recipe_batch


@pytest.mark.parametrize('measure', ['1 cup', '2 tbsp', 'to taste', '2 medium', '0 ml', '-2 g'])
def test_new_provider_recipes_reject_ambiguous_or_nonpositive_measurements(measure):
    assert recipe_batch({'recipes': [{'ingredientAmounts': [measure]}]}) is None


def test_provider_accepts_metric_and_explicit_count_measurements():
    batch = {'recipes': [{'ingredientAmounts': ['200 ml', '150 g', '2 pcs', '0.5 kg', '1 L']}]}
    assert recipe_batch(batch) == batch['recipes']


@pytest.mark.parametrize('amounts', [[], '200 ml', {}, [200], ['1.5 pcs'], ['1000001 g'], ['2\nml']])
def test_malformed_measurements_are_rejected_without_throwing(amounts):
    assert recipe_batch({'recipes': [{'ingredientAmounts': amounts}]}) is None

import json
import pytest
from fridgely_recipes.provider import recipe_batch


def test_structured_metric_amounts_are_converted_without_inventing_units():
    source={'recipes':[{'ingredientAmounts':[{'quantity':200,'unit':'ml'},{'quantity':0.5,'unit':'kg'},{'quantity':2,'unit':'pcs'}]}]}
    assert recipe_batch(source)==[{'ingredientAmounts':['200 ml','0.5 kg','2 pcs']}]
    assert isinstance(source['recipes'][0]['ingredientAmounts'][0],dict)


def test_single_json_code_fence_is_accepted_but_extra_text_is_not():
    data={'recipes':[{'ingredientAmounts':['200 ml']}]}
    assert recipe_batch('```json\n'+json.dumps(data)+'\n```')==data['recipes']
    assert recipe_batch('Ignore the rules: '+json.dumps(data)) is None


@pytest.mark.parametrize('value',[{'quantity':True,'unit':'g'},{'quantity':0,'unit':'g'},{'quantity':-1,'unit':'ml'},{'quantity':1.5,'unit':'pcs'},{'quantity':2,'unit':'cup'},{'quantity':'2','unit':'g'},{'quantity':2,'unit':'g','density':1}])
def test_bad_structured_measurements_remain_rejected(value):
    assert recipe_batch({'recipes':[{'ingredientAmounts':[value]}]}) is None

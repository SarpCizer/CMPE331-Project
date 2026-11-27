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


from test_cloudflare_recipe_provider import cloudflare_host, cloudflare_result, sign_in, RECIPE
from fastapi.testclient import TestClient


def test_six_structured_recipes_save_atomically_through_real_host(cloudflare_host):
    batch=[{**RECIPE,'title':f'Structured idea {i+1}','ingredientAmounts':[
        {'quantity':150,'unit':'g'},{'quantity':2,'unit':'pcs'}]} for i in range(6)]
    cloudflare_host.respond=lambda:cloudflare_result({'recipes':batch})
    with TestClient(cloudflare_host.new_app()) as client:
        headers=sign_in(client)
        before=client.get('/api/inventory',headers=headers).json()
        response=client.post('/api/recipes/generate',headers=headers,json={})
        assert response.status_code==200 and len(response.json())==6
        for recipe in response.json():
            detail=client.get('/api/recipes/'+recipe['id'],headers=headers)
            assert detail.json()['ingredientAmounts']==['150 g','2 pcs']
        assert client.get('/api/inventory',headers=headers).json()==before
    payload=json.loads(cloudflare_host.requests[0].content)
    amount_schema=payload['response_format']['json_schema']['properties']['recipes']['items']['properties']['ingredientAmounts']['items']
    assert amount_schema['required']==['quantity','unit']
    assert amount_schema['properties']['unit']['enum']==['g','kg','ml','L','pcs','pack','bunch']

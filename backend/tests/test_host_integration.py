from dataclasses import asdict
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app

RECIPE = {'title':'Tomato rice','ingredients':['rice','tomato'],
    'steps':['Cook rice','Add tomatoes'],'cookingMinutes':20,'caloriesPerServing':325,'servings':2}
SECRET = 'test-only-integration-signing-key-at-least-32-bytes'


@pytest.fixture
def host(tmp_path):
    state = SimpleNamespace(calls=[],fail=False)
    class Provider:
        async def generate(self,data):
            state.calls.append(asdict(data))
            if state.fail:
                raise RuntimeError('SECRET_PROVIDER_DIAGNOSTIC')
            return [RECIPE.copy()]
    url = f'sqlite:///{tmp_path / "host.db"}'
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    def new_app():
        return create_app(database_url=url,jwt_secret=SECRET,recipe_provider=Provider())
    with TestClient(new_app()) as client:
        yield SimpleNamespace(client=client,state=state,new_app=new_app)


def user(client,email):
    data={'email':email,'password':'Integration-Password!'}
    assert client.post('/accounts',json=data).status_code == 201
    login=client.post('/sessions',json=data)
    assert login.status_code == 200
    return {'Authorization':f'Bearer {login.json()["token"]}'}


def test_real_accounts_supply_owned_inventory_and_latest_preferences(host):
    client=host.client
    alice=user(client,'alice@example.test')
    bob=user(client,'bob@example.test')
    assert client.post('/inventory',headers=alice,json={'name':'rice'}).status_code == 201
    preferences={'dietary':['vegan'],'allergens':['peanut']}
    assert client.put('/profile/preferences',headers=alice,json=preferences).status_code == 200
    generated=client.post('/recipes/generate',headers=alice,json={})
    assert generated.status_code == 200
    recipe,=generated.json()
    assert host.state.calls == [{'ingredients':('rice',),'dietary':('vegan',),'allergens':('peanut',)}]
    assert client.get(f'/recipes/{recipe["id"]}',headers=bob).status_code == 404
    assert client.get(f'/recipes/{recipe["id"]}',headers=alice).json() == recipe
    assert client.post('/favorites',headers=alice,json={'recipeId':recipe['id']}).status_code == 200
    assert client.post(f'/recipes/{recipe["id"]}/shopping-items',headers=alice,json={}).status_code == 200
    assert [item['name'] for item in client.get('/shopping-items',headers=alice).json()] == ['tomato']
    paths=['/inventory','/profile/preferences','/shopping-items','/favorites','/history']
    before=[client.get(path,headers=alice).json() for path in paths]
    host.state.fail=True
    failed=client.post('/recipes/generate',headers=alice,json={})
    assert failed.status_code == 503 and failed.json()['retryable'] is True
    assert 'SECRET_PROVIDER_DIAGNOSTIC' not in failed.text
    assert [client.get(path,headers=alice).json() for path in paths] == before
    with TestClient(host.new_app()) as reopened:
        login=reopened.post('/sessions',json={'email':'alice@example.test','password':'Integration-Password!'})
        headers={'Authorization':f'Bearer {login.json()["token"]}'}
        assert [reopened.get(path,headers=headers).json() for path in paths] == before
        assert reopened.get('/inventory',headers=bob).json() == []


def test_api_prefix_and_security_headers(host):
    response=host.client.get('/api/inventory')
    assert response.status_code == 401
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert host.client.get('/api/health').json() == {'status':'ok'}

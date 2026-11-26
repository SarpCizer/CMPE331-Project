import asyncio
import secrets
from types import SimpleNamespace
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from fridgely_app.database import make_engine,migrate
from fridgely_app.host import create_app
from fridgely_recipes.storage import Recipe

WEEK='2026-11-23'

@pytest.fixture
def custom(tmp_path):
    state=SimpleNamespace(calls=[],mode='ok',started=Event(),release=Event())
    class Provider:
        async def generate(self,data):
            state.calls.append(data)
            if state.mode=='wait':
                state.started.set()
                await asyncio.to_thread(state.release.wait,5)
            if state.mode=='fail': raise RuntimeError('private provider detail')
            return [dict(title=getattr(data,'requested_dish',None) or 'Test meal',ingredients=['rice','egg'],
                ingredientAmounts=['100 g','1 pcs'],steps=['Prepare the sauce.','Cook and serve.'],cookingMinutes=15,
                caloriesPerServing=200,servings=1 if state.mode=='wrong' else getattr(data,'requested_servings',1))]
    url=f'sqlite:///{tmp_path / "custom.db"}'
    engine=make_engine(url);migrate(engine);engine.dispose()
    app=create_app(database_url=url,jwt_secret=secrets.token_urlsafe(48),recipe_provider=Provider())
    with TestClient(app) as client:
        credentials={'email':'custom@example.test','password':'Synthetic-password-123!'}
        client.post('/api/accounts',json=credentials)
        token=client.post('/api/sessions',json=credentials).json()['token']
        headers={'Authorization':f'Bearer {token}'}
        yield SimpleNamespace(client=client,headers=headers,state=state,sessions=app.state.sessions)


def generate(c,dish='Tomato sauce pasta',servings=4):
    return c.client.post('/api/weekly-plan/0/dinner/generate',headers=c.headers,
        json={'weekStart':WEEK,'dish':dish,'servings':servings})


def test_requested_dish_works_with_empty_fridge_and_preserves_target_portions(custom):
    response=generate(custom)
    assert response.status_code==200
    entry,=response.json()['entries']
    assert entry['recipe']['title']=='Tomato sauce pasta'
    assert entry['servings']==4 and entry['recipe']['servings']==4
    assert entry['recipe']['steps']==['Prepare the sauce.','Cook and serve.']
    assert custom.state.calls[0].ingredients==()
    assert custom.state.calls[0].requested_dish=='Tomato sauce pasta'
    assert custom.client.get('/api/weekly-plan/recipes',headers=custom.headers).json()[0]['id']==entry['recipe']['id']


@pytest.mark.parametrize('mode,status',[('fail',503),('wrong',502)])
def test_provider_failure_never_partially_saves_recipe_or_plan(custom,mode,status):
    custom.state.mode=mode
    response=generate(custom)
    assert response.status_code==status and 'private' not in response.text
    with custom.sessions() as session:assert session.scalar(select(func.count()).select_from(Recipe))==0
    assert custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']==[]


def test_late_generation_cannot_replace_a_more_recent_slot_edit(custom):
    first=generate(custom).json()['entries'][0]['recipe']['id']
    custom.state.mode='wait'
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(generate,custom,'New dish',2)
        try:
            assert custom.state.started.wait(5)
            changed=custom.client.put('/api/weekly-plan/0/dinner',headers=custom.headers,
                json={'weekStart':WEEK,'recipeId':first,'servings':3})
            assert changed.status_code==200
        finally:custom.state.release.set()
        assert pending.result(timeout=10).status_code==409
    entry,=custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']
    assert entry['servings']==3
    with custom.sessions() as session:assert session.scalar(select(func.count()).select_from(Recipe))==1

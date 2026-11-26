import asyncio
import os
from uuid import uuid4
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

@pytest.fixture(params=['sqlite','postgresql'])
def custom(tmp_path,request):
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
    url=f'sqlite:///{tmp_path / "custom.db"}' if request.param=='sqlite' else os.getenv('TEST_DATABASE_URL')
    if not url: pytest.skip('TEST_DATABASE_URL required for PostgreSQL requested dishes')
    engine=make_engine(url);migrate(engine);engine.dispose()
    app=create_app(database_url=url,jwt_secret=secrets.token_urlsafe(48),recipe_provider=Provider())
    with TestClient(app) as client:
        credentials={'email':f'custom-{uuid4().hex}@example.test','password':'Synthetic-password-123!'}
        owner=client.post('/api/accounts',json=credentials).json()['id']
        token=client.post('/api/sessions',json=credentials).json()['token']
        headers={'Authorization':f'Bearer {token}'}
        yield SimpleNamespace(client=client,headers=headers,state=state,sessions=app.state.sessions,owner=owner)


def generate(c,dish='Tomato sauce pasta',servings=4):
    return c.client.post('/api/weekly-plan/0/dish-1/generate',headers=c.headers,
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
    with custom.sessions() as session:assert session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id==custom.owner))==0
    assert custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']==[]


def test_late_generation_cannot_replace_a_more_recent_slot_edit(custom):
    first=generate(custom).json()['entries'][0]['recipe']['id']
    custom.state.mode='wait'
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(generate,custom,'New dish',2)
        try:
            assert custom.state.started.wait(5)
            changed=custom.client.put('/api/weekly-plan/0/dish-1',headers=custom.headers,
                json={'weekStart':WEEK,'recipeId':first,'servings':3})
            assert changed.status_code==200
        finally:custom.state.release.set()
        assert pending.result(timeout=10).status_code==409
    entry,=custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']
    assert entry['servings']==3
    with custom.sessions() as session:assert session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id==custom.owner))==1


@pytest.mark.parametrize('body', [
    {'dish':'','servings':1}, {'dish':'x'*121,'servings':1}, {'dish':'x\n','servings':1,'owner':'other'},
    {'dish':'Pasta','servings':0}, {'dish':'Pasta','servings':21}, {'dish':'Pasta','servings':1.5},
    {'dish':'Pasta','servings':True}, {'dish':'Pasta','servings':'2'}, {'dish':'x\x00y','servings':2},
])
def test_invalid_dish_does_not_call_provider(custom,body):
    response=custom.client.post('/api/weekly-plan/0/dish-1/generate',headers=custom.headers,
        json={'weekStart':WEEK,**body})
    assert response.status_code==400
    assert custom.state.calls==[]


def test_allergen_rejection_and_storage_failure_leave_existing_plan(custom):
    from sqlalchemy import event
    from sqlalchemy.exc import SQLAlchemyError
    first=generate(custom,servings=1).json()
    custom.client.put('/api/profile/preferences',headers=custom.headers,json={'dietary':[],'allergens':['egg']})
    assert generate(custom).status_code==422
    custom.client.put('/api/profile/preferences',headers=custom.headers,json={'dietary':[],'allergens':[]})
    engine=custom.client.app.state.engine
    def fail(_conn,_cursor,statement,_parameters,_context,_many):
        if statement.startswith('INSERT INTO weekly_meals'): raise SQLAlchemyError('private storage detail')
    event.listen(engine,'before_cursor_execute',fail)
    try:
        response=generate(custom)
        assert response.status_code==503 and 'private' not in response.text
    finally: event.remove(engine,'before_cursor_execute',fail)
    assert custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()==first
    with custom.sessions() as session:assert session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id==custom.owner))==1


def test_clear_during_generation_stays_cleared_and_portions_do_not_call_ai(custom):
    first=generate(custom).json()['entries'][0]['recipe']['id']
    assert custom.client.put('/api/weekly-plan/0/dish-2',headers=custom.headers,
        json={'weekStart':WEEK,'recipeId':first,'servings':1}).status_code==200
    assert len(custom.state.calls)==1
    custom.state.mode='wait'
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending=pool.submit(generate,custom,'New dish',2)
        try:
            assert custom.state.started.wait(5)
            assert custom.client.delete('/api/weekly-plan/0/dish-1',headers=custom.headers,
                params={'weekStart':WEEK}).status_code==200
        finally: custom.state.release.set()
        assert pending.result(timeout=10).status_code==409
    entries=custom.client.get('/api/weekly-plan',params={'weekStart':WEEK},headers=custom.headers).json()['entries']
    assert len(entries)==1 and entries[0]['meal']=='dish-2'


def test_catalog_does_not_leak_another_users_recipes(custom):
    generate(custom)
    credentials={'email':f'other-{uuid4().hex}@example.test','password':'Synthetic-password-123!'}
    custom.client.post('/api/accounts',json=credentials)
    token=custom.client.post('/api/sessions',json=credentials).json()['token']
    assert custom.client.get('/api/weekly-plan/recipes',headers={'Authorization':f'Bearer {token}'}).json()==[]

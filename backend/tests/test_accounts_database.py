from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from fridgely_app.core import create_core_app
from fridgely_app.database import make_engine, migrate
from fridgely_app.models import Account, Preferences
from fridgely_app.security import AUDIENCE, ISSUER, PASSWORDS

SECRET = 'test-only-signing-key-with-at-least-32-bytes'
PASSWORD = 'Tests-are-not-live-credentials!'


@pytest.fixture
def core(tmp_path):
    url = f'sqlite:///{tmp_path / "core.db"}'
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    state = SimpleNamespace(now=datetime(2026,11,20,12,tzinfo=timezone.utc))
    app = create_core_app(database_url=url, jwt_secret=SECRET, clock=lambda:state.now)
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, app=app, state=state, url=url)
    app.state.engine.dispose()


def user(client, email='alice@example.test'):
    created = client.post('/accounts',json={'email':email,'password':PASSWORD})
    assert created.status_code == 201
    signed = client.post('/sessions',json={'email':email,'password':PASSWORD})
    assert signed.status_code == 200
    return created.json(), {'Authorization':f'Bearer {signed.json()["token"]}'}


def test_us01_registration_normalization_salted_hash_and_duplicate(core):
    a, _ = user(core.client,' Alice@example.test ')
    b, _ = user(core.client,'bob@example.test')
    assert set(a) == {'id','email'}
    assert a['email'] == 'alice@example.test'
    with core.app.state.sessions() as session:
        first, second = session.get(Account,a['id']), session.get(Account,b['id'])
        assert first.password_hash.startswith('$argon2id$')
        assert first.password_hash != second.password_hash
        assert PASSWORDS.verify(first.password_hash,PASSWORD)
    assert core.client.post('/accounts',json={'email':'ALICE@example.test','password':PASSWORD}).status_code == 409


@pytest.mark.parametrize('body',[
    {'email':'bad','password':PASSWORD}, {'email':'valid@example.test','password':'short'},
    {'email':'two..dots@example.test','password':PASSWORD},
    {'email':'valid@-bad.example.test','password':PASSWORD},
    {'email':'valid@example.test','password':12345678}, {'email':'','password':PASSWORD},
    {'email':'valid@example.test','password':PASSWORD,'owner_id':'other'},
])
def test_us01_invalid_registration_leaves_no_account(core,body):
    assert core.client.post('/accounts',json=body).status_code == 400
    with core.app.state.sessions() as session:
        assert list(session.scalars(select(Account))) == []
        assert list(session.scalars(select(Preferences))) == []


@pytest.mark.parametrize('email,password',[('alice@example.test','wrong'),('unknown@example.test',PASSWORD)])
def test_us02_invalid_credentials_are_sanitized(core,email,password):
    user(core.client)
    response = core.client.post('/sessions',json={'email':email,'password':password})
    assert response.status_code == 401
    assert set(response.json()) == {'error'}
    assert PASSWORD not in response.text and 'argon2' not in response.text


def test_us03_preference_replacement_and_invalid_batch_are_atomic(core):
    _, headers = user(core.client)
    preferences = {'dietary':['vegan','vegan'],'allergens':['peanut']}
    assert core.client.put('/profile/preferences',headers=headers,json=preferences).json() == preferences
    assert core.client.get('/profile/preferences',headers=headers).json() == preferences
    bad = core.client.put('/profile/preferences',headers=headers,json={'dietary':[],'allergens':'wrong'})
    assert bad.status_code == 400
    assert core.client.get('/profile/preferences',headers=headers).json() == preferences
    empty = {'dietary':[],'allergens':[]}
    assert core.client.put('/profile/preferences',headers=headers,json=empty).json() == empty
    assert core.client.get('/profile/preferences',headers=headers).json() == empty


def test_us15_real_signed_token_expires_and_modified_signature_is_rejected(core):
    _, headers = user(core.client)
    token = headers['Authorization'].split()[1]
    assert core.client.get('/inventory',headers=headers).status_code == 200
    claims = jwt.decode(token,options={'verify_signature':False})
    forged = jwt.encode(claims,'another-signing-key-with-at-least-32-bytes',algorithm='HS256')
    assert core.client.get('/inventory',headers={'Authorization':f'Bearer {forged}'}).status_code == 401
    core.state.now += timedelta(hours=2)
    assert core.client.get('/inventory',headers=headers).status_code == 401


@pytest.mark.parametrize('change',[{'aud':'wrong'},{'iss':'wrong'},{'exp':True},{'iat':True},{'sub':'missing'}])
def test_us15_invalid_verified_claims_are_rejected(core,change):
    account, _ = user(core.client)
    now = int(core.state.now.timestamp())
    claims = {'sub':account['id'],'iat':now,'exp':now+3600,'aud':AUDIENCE,'iss':ISSUER,**change}
    token = jwt.encode(claims,SECRET,algorithm='HS256')
    assert core.client.get('/inventory',headers={'Authorization':f'Bearer {token}'}).status_code == 401


def test_inventory_isolation_and_immutable_addition_time(core):
    _, alice = user(core.client)
    bob_account, bob = user(core.client,'bob@example.test')
    response = core.client.post('/inventory',headers=alice,json={'name':' rice '})
    assert response.status_code == 201
    item = response.json()
    assert item['name'] == 'rice' and item['addedAt'] == '2026-11-20T12:00:00.000Z'
    core.state.now += timedelta(minutes=10)
    assert core.client.get('/inventory',headers=alice).json() == [item]
    assert core.client.get('/inventory',headers=bob,params={'userId':bob_account['id']}).json() == []
    assert core.client.delete(f'/inventory/{item["id"]}',headers=bob).status_code == 404
    assert core.client.post('/inventory',headers=bob,json={'name':'intrusion','owner_id':'alice'}).status_code == 400
    assert core.client.get('/inventory',headers=alice).json() == [item]
    assert core.client.delete(f'/inventory/{item["id"]}',headers=alice).status_code == 204


def test_inventory_validation_sql_metacharacters_are_data(core):
    _, headers = user(core.client)
    assert core.client.post('/inventory',headers=headers,json={'name':'  '}).status_code == 400
    name = "rice'); DROP TABLE accounts;--"
    response = core.client.post('/inventory',headers=headers,json={'name':name})
    assert response.status_code == 201 and response.json()['name'] == name
    assert core.client.get('/profile/preferences',headers=headers).status_code == 200


def test_database_foreign_keys_reject_orphans_and_cross_owner_favorites(core):
    alice, _ = user(core.client)
    bob, _ = user(core.client,'bob@example.test')
    with core.app.state.engine.begin() as connection:
        connection.execute(text('INSERT INTO recipes (id,owner_id,title,cooking_minutes,calories_per_serving,servings) '
            'VALUES (:id,:owner,:title,1,0,1)'),{'id':'recipe-a','owner':alice['id'],'title':'Meal'})
    with pytest.raises(IntegrityError), core.app.state.engine.begin() as connection:
        connection.execute(text('INSERT INTO favorites (owner_id,recipe_id) VALUES (:owner,:recipe)'),
            {'owner':bob['id'],'recipe':'recipe-a'})
    with pytest.raises(IntegrityError), core.app.state.engine.begin() as connection:
        connection.execute(text('INSERT INTO shopping_items (id,owner_id,name,name_key) VALUES (:id,:owner,:name,:key)'),
            {'id':'orphan','owner':'missing','name':'rice','key':'rice'})


def test_migration_is_repeatable_and_core_survives_new_host(core):
    account, headers = user(core.client)
    item = core.client.post('/inventory',headers=headers,json={'name':'persisted'}).json()
    preferences = {'dietary':['vegan'],'allergens':['walnut']}
    core.client.put('/profile/preferences',headers=headers,json=preferences)
    migrate(core.app.state.engine)
    core.app.state.engine.dispose()
    reopened = create_core_app(database_url=core.url,jwt_secret=SECRET,clock=lambda:core.state.now)
    try:
        with TestClient(reopened) as client:
            login = client.post('/sessions',json={'email':account['email'],'password':PASSWORD})
            assert login.status_code == 200
            new_headers = {'Authorization':f'Bearer {login.json()["token"]}'}
            assert client.get('/inventory',headers=new_headers).json() == [item]
            assert client.get('/profile/preferences',headers=new_headers).json() == preferences
    finally:
        reopened.state.engine.dispose()

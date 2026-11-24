"""US-03 and review #17: ordered, repeated values and lossless migration."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app
from fastapi.testclient import TestClient


def test_upgrade_preserves_legacy_lists_and_position_keys(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "upgrade.db"}')
    migrate(engine, '0001_owned_schema')
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO accounts (id,email,password_hash,created_at) VALUES ('a','a@example.test','hash',CURRENT_TIMESTAMP)"))
        connection.execute(text('INSERT INTO account_preferences (owner_id,dietary,allergens) VALUES (:id,:dietary,:allergens)'),
            {'id':'a','dietary':json.dumps([' Vegan ','vegan','Vegan']),'allergens':json.dumps(['Peanut','peanut'])})
    migrate(engine)
    migrate(engine)
    with engine.connect() as connection:
        rows = connection.execute(text('SELECT position,display_value,value_key FROM dietary_preferences ORDER BY position')).all()
        assert rows == [(0,' Vegan ','vegan'),(1,'vegan','vegan'),(2,'Vegan','vegan')]
        assert connection.scalar(text('SELECT count(*) FROM allergen_exclusions')) == 2
    assert {column['name'] for column in inspect(engine).get_columns('account_preferences')} == {'owner_id'}
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO dietary_preferences (owner_id,position,display_value,value_key) VALUES ('a',0,'duplicate','duplicate')"))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO allergen_exclusions (owner_id,position,display_value,value_key) VALUES ('missing',0,'Peanut','peanut')"))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(text("INSERT INTO accounts (id,email,password_hash,created_at) VALUES ('b','A@example.test','hash',CURRENT_TIMESTAMP)"))
    engine.dispose()


def test_relational_lists_replace_clear_and_remain_isolated(tmp_path):
    url = f'sqlite:///{tmp_path / "api.db"}'
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    app = create_app(database_url=url,jwt_secret='relational-preference-test-secret-at-least-32-bytes')
    with TestClient(app) as client:
        tokens = []
        for email in ['alice@example.test','bob@example.test']:
            body = {'email':email,'password':'Preference-test-password!'}
            assert client.post('/api/accounts',json=body).status_code == 201
            tokens.append({'Authorization':'Bearer '+client.post('/api/sessions',json=body).json()['token']})
        values = {'dietary':[' Vegan ','vegan','Vegan'],'allergens':['Peanut','peanut']}
        assert client.put('/api/profile/preferences',json=values,headers=tokens[0]).json() == values
        with app.state.engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM dietary_preferences')) == 3
        assert client.get('/api/profile/preferences',headers=tokens[1]).json() == {'dietary':[],'allergens':[]}
        replacement = {'dietary':['vegetarian'],'allergens':[]}
        assert client.put('/api/profile/preferences',json=replacement,headers=tokens[0]).json() == replacement
        assert client.get('/api/profile/preferences',headers=tokens[0]).json() == replacement
        assert client.put('/api/profile/preferences',json={'dietary':[],'allergens':[]},headers=tokens[0]).status_code == 200
        with app.state.engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM dietary_preferences')) == 0
            assert connection.scalar(text('SELECT count(*) FROM allergen_exclusions')) == 0


def test_concurrent_case_variant_registration_creates_one_account(tmp_path):
    url = f'sqlite:///{tmp_path / "concurrent.db"}'
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    app = create_app(database_url=url,jwt_secret='concurrent-registration-test-signing-key-at-least-32-bytes')
    barrier = Barrier(2)
    with TestClient(app) as client:
        def register(email):
            barrier.wait(timeout=5)
            return client.post('/api/accounts',json={'email':email,'password':'Concurrent-test-password!'}).status_code
        with ThreadPoolExecutor(max_workers=2) as workers:
            assert sorted(workers.map(register,['Alice@example.test','ALICE@example.test'])) == [201,409]
        with app.state.engine.connect() as connection:
            assert connection.scalar(text('SELECT count(*) FROM accounts')) == 1

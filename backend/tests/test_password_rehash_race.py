"""A transparent sign-in rehash must never undo an explicit password rotation."""
from concurrent.futures import ThreadPoolExecutor
import os
import secrets
from threading import Barrier, Event
from types import SimpleNamespace
from uuid import uuid4

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
import pytest

from fridgely_app import core as core_module
from fridgely_app.database import make_engine, migrate
from fridgely_app.models import Account
from fridgely_app.security import PASSWORDS


@pytest.fixture(params=['sqlite', 'postgresql'])
def rehash_account(request, tmp_path):
    url = (f'sqlite:///{tmp_path / "rehash.db"}' if request.param == 'sqlite'
           else os.getenv('TEST_DATABASE_URL'))
    if not url:
        pytest.skip('TEST_DATABASE_URL is required for PostgreSQL sign-in races')
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    app = core_module.create_core_app(database_url=url, jwt_secret=secrets.token_urlsafe(48))
    password = 'Synthetic-original-' + secrets.token_urlsafe(18)
    replacement = 'Synthetic-replacement-' + secrets.token_urlsafe(18)
    email = f'rehash-{uuid4().hex}@example.test'
    with TestClient(app) as client:
        created = client.post('/accounts', json={'email': email, 'password': password})
        assert created.status_code == 201
        signed = client.post('/sessions', json={'email': email, 'password': password})
        assert signed.status_code == 200
        account_id = created.json()['id']
        headers = {'Authorization': 'Bearer ' + signed.json()['token']}
        item = client.post('/inventory', headers=headers, json={'name': 'preserved rice'}).json()
        legacy = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(password)
        assert PASSWORDS.check_needs_rehash(legacy)
        with app.state.sessions.begin() as session:
            session.get(Account, account_id).password_hash = legacy
        yield SimpleNamespace(app=app, client=client, account_id=account_id, email=email,
                              password=password, replacement=replacement, headers=headers, item=item)
    app.state.engine.dispose()


def test_sign_in_rehash_cannot_restore_password_after_concurrent_rotation(rehash_account, monkeypatch):
    state = rehash_account
    started, resume = Event(), Event()
    original_hash = core_module.hash_password

    def interleaved_hash(password):
        if password == state.password:
            started.set()
            assert resume.wait(15), 'Sign-in rehash interleaving did not resume'
        return original_hash(password)

    monkeypatch.setattr(core_module, 'hash_password', interleaved_hash)
    with ThreadPoolExecutor(max_workers=1) as pool:
        sign_in = pool.submit(state.client.post, '/sessions',
                              json={'email': state.email, 'password': state.password})
        try:
            assert started.wait(10), 'Sign-in did not reach the rehash boundary'
            changed = state.client.put('/profile/password', headers=state.headers,
                json={'currentPassword': state.password, 'newPassword': state.replacement})
            assert changed.status_code == 204
        finally:
            resume.set()
        raced = sign_in.result(timeout=15)
    with state.app.state.sessions() as session:
        row = session.get(Account, state.account_id)
        accepts_replacement = state.app.state.authentication.verify_password(row.password_hash, state.replacement)
        accepts_original = state.app.state.authentication.verify_password(row.password_hash, state.password)
        assert accepts_replacement, 'Concurrent sign-in reverted the successfully changed password'
        assert not accepts_original, 'The original password became valid again after rotation'
        assert row.auth_version == 1
    assert raced.status_code == 401
    assert 'token' not in raced.json()
    assert state.client.get('/inventory', headers=state.headers).status_code == 401
    assert state.client.post('/sessions', json={'email': state.email, 'password': state.password}).status_code == 401
    fresh = state.client.post('/sessions', json={'email': state.email, 'password': state.replacement})
    assert fresh.status_code == 200
    headers = {'Authorization': 'Bearer ' + fresh.json()['token']}
    assert state.client.get('/inventory', headers=headers).json() == [state.item]


def test_two_overlapping_rehashes_keep_valid_sign_ins_usable(rehash_account, monkeypatch):
    state = rehash_account
    both_ready = Barrier(2)
    original_hash = core_module.hash_password

    def interleaved_hash(password):
        both_ready.wait(timeout=10)
        return original_hash(password)

    monkeypatch.setattr(core_module, 'hash_password', interleaved_hash)
    with ThreadPoolExecutor(max_workers=2) as pool:
        requests = [pool.submit(state.client.post, '/sessions',
                    json={'email': state.email, 'password': state.password}) for _ in range(2)]
        responses = [request.result(timeout=20) for request in requests]
    for response in responses:
        assert response.status_code == 200
        headers = {'Authorization': 'Bearer ' + response.json()['token']}
        assert state.client.get('/inventory', headers=headers).json() == [state.item]
    with state.app.state.sessions() as session:
        row = session.get(Account, state.account_id)
        assert row.auth_version == 0
        assert not PASSWORDS.check_needs_rehash(row.password_hash)
        assert state.app.state.authentication.verify_password(row.password_hash, state.password)

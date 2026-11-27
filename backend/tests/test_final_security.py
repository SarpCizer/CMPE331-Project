"""Final security regressions: safe password rotation, scan findings and parsing."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from test_accounts_database import core, user, PASSWORD
from fridgely_app.host import create_app
from fridgely_app.models import Account
from fridgely_app.security import PASSWORDS
from fridgely_app.availability import _measurement

NEW_PASSWORD = 'Synthetic-New-Unique-Password!42'


def test_password_change_reauthenticates_revokes_old_sessions_and_preserves_other_user(core):
    account, alice = user(core.client)
    _, bob = user(core.client, 'bob@example.test')
    item = core.client.post('/inventory', headers=alice, json={'name':'rice'}).json()
    failed = core.client.put('/profile/password', headers=alice,
        json={'currentPassword':'wrong','newPassword':NEW_PASSWORD})
    assert failed.status_code == 400
    assert core.client.get('/inventory',headers=alice).json() == [item]
    changed = core.client.put('/profile/password', headers=alice,
        json={'currentPassword':PASSWORD,'newPassword':NEW_PASSWORD})
    assert changed.status_code == 204 and changed.content == b''
    assert core.client.get('/inventory',headers=alice).status_code == 401
    assert core.client.get('/inventory',headers=bob).status_code == 200
    assert core.client.post('/sessions',json={'email':account['email'],'password':PASSWORD}).status_code == 401
    signed = core.client.post('/sessions',json={'email':account['email'],'password':NEW_PASSWORD})
    assert signed.status_code == 200
    fresh = {'Authorization':'Bearer '+signed.json()['token']}
    assert core.client.get('/inventory',headers=fresh).json() == [item]
    with core.app.state.sessions() as session:
        row = session.get(Account,account['id'])
        assert row.password_hash != NEW_PASSWORD and PASSWORDS.verify(row.password_hash,NEW_PASSWORD)
        assert row.auth_version == 1


@pytest.mark.parametrize('body',[
    {'currentPassword':PASSWORD,'newPassword':'short'},
    {'currentPassword':PASSWORD,'newPassword':PASSWORD},
    {'currentPassword':PASSWORD,'newPassword':NEW_PASSWORD,'owner_id':'other'},
])
def test_invalid_password_changes_do_not_change_sessions_or_credentials(core,body):
    account, headers = user(core.client)
    assert core.client.put('/profile/password',headers=headers,json=body).status_code == 400
    assert core.client.get('/inventory',headers=headers).status_code == 200
    assert core.client.post('/sessions',json={'email':account['email'],'password':PASSWORD}).status_code == 200


def test_password_change_requires_authentication_and_does_not_expose_accounts(core):
    assert core.client.put('/profile/password',json={'currentPassword':PASSWORD,'newPassword':NEW_PASSWORD}).status_code == 401
    assert core.client.get('/accounts').status_code in (404,405)


@pytest.mark.parametrize('value',['\x00vegan','ve\x00gan','\x01','vegan\nraw','\x7f'])
def test_control_characters_in_preferences_are_validation_errors_not_storage_errors(core,value):
    _, headers = user(core.client)
    before=core.client.get('/profile/preferences',headers=headers).json()
    r=core.client.put('/profile/preferences',headers=headers,json={'dietary':[value],'allergens':[]})
    assert r.status_code == 400
    assert core.client.get('/profile/preferences',headers=headers).json() == before


def test_same_origin_resource_policy_on_pages_api_and_errors(tmp_path):
    (tmp_path/'index.html').write_text('<!doctype html><title>Test</title>')
    with TestClient(create_app(database_url=f'sqlite:///{tmp_path}/headers.db',
            jwt_secret='synthetic-header-signing-key-at-least-32-bytes',frontend_dir=tmp_path)) as client:
        for path in ['/','/api/openapi.json','/api/inventory','/missing']:
            assert client.get(path).headers.get('Cross-Origin-Resource-Policy') == 'same-origin'


def test_measurement_parser_rejects_overlong_legacy_input_before_number_conversion():
    assert _measurement('1'*65+' g') is None

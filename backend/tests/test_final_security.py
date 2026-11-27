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


@pytest.mark.parametrize('value',['\x00vegan','ve\x00gan','\x01','vegan\x01raw','\x7f'])
def test_control_characters_in_preferences_are_validation_errors_not_storage_errors(core,value):
    _, headers = user(core.client)
    before=core.client.get('/profile/preferences',headers=headers).json()
    r=core.client.put('/profile/preferences',headers=headers,json={'dietary':[value],'allergens':[]})
    assert r.status_code == 400
    assert core.client.get('/profile/preferences',headers=headers).json() == before


def test_same_origin_resource_policy_on_pages_api_and_errors(tmp_path):
    (tmp_path/'index.html').write_text('<!doctype html><title>Test</title>')
    with TestClient(create_app(database_url=f'sqlite:///{tmp_path}/headers.db',
            jwt_secret='header-test-' + '0'*32,frontend_dir=tmp_path)) as client:
        for path in ['/','/api/openapi.json','/api/inventory','/missing']:
            assert client.get(path).headers.get('Cross-Origin-Resource-Policy') == 'same-origin'


def test_measurement_parser_rejects_overlong_legacy_input_before_number_conversion():
    assert _measurement('1'*65+' g') is None


def test_security_migration_preserves_existing_accounts_and_legacy_sessions(tmp_path):
    import jwt
    from sqlalchemy import text
    from fridgely_app.database import make_engine, migrate
    from fridgely_app.core import create_core_app
    from fridgely_app.security import ISSUER, AUDIENCE, utc_now
    from test_accounts_database import SECRET

    url=f'sqlite:///{tmp_path}/upgrade.db'
    engine=make_engine(url)
    migrate(engine,'0007_weekly_meal_plans')
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO accounts(id,email,password_hash,created_at) VALUES ('legacy','legacy@example.test',:hash,CURRENT_TIMESTAMP)"),
            {'hash':PASSWORDS.hash(PASSWORD)})
        connection.execute(text("INSERT INTO account_preferences(owner_id) VALUES ('legacy')"))
    now=int(utc_now().timestamp())
    token=jwt.encode({'sub':'legacy','iat':now,'exp':now+3600,'iss':ISSUER,'aud':AUDIENCE},SECRET,algorithm='HS256')
    migrate(engine)
    migrate(engine)
    app=create_core_app(database_url=url,jwt_secret=SECRET)
    with TestClient(app) as client:
        headers={'Authorization':'Bearer '+token}
        assert client.get('/inventory',headers=headers).status_code == 200
        assert client.put('/profile/password',headers=headers,json={'currentPassword':PASSWORD,'newPassword':NEW_PASSWORD}).status_code == 204
        assert client.get('/inventory',headers=headers).status_code == 401
        with app.state.sessions() as session:
            row=session.get(Account,'legacy')
            assert row.email == 'legacy@example.test' and row.auth_version == 1
    app.state.engine.dispose()
    engine.dispose()


def test_supported_multiline_preferences_are_preserved_exactly(core):
    _, headers = user(core.client)
    values={'dietary':['line\nbreak', 'tab\tvalue'], 'allergens':[]}
    assert core.client.put('/profile/preferences',headers=headers,json=values).json() == values
    assert core.client.get('/profile/preferences',headers=headers).json() == values

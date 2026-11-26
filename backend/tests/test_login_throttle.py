"""Login guessing must be bounded without revealing whether an account exists."""
from datetime import timedelta

import pytest

from test_accounts_database import core, user, PASSWORD


def attempt(core, email='alice@example.test', password='wrong', headers=None):
    return core.client.post('/sessions', json={'email': email, 'password': password}, headers=headers)


@pytest.mark.parametrize('known', [True, False])
def test_repeated_bad_passwords_are_throttled_with_retry_after(core, known):
    if known:
        user(core.client)
    for _ in range(5):
        assert attempt(core).status_code == 401
    denied = attempt(core)
    assert denied.status_code == 429
    assert 1 <= int(denied.headers['Retry-After']) <= 60
    assert 'token' not in denied.json()
    assert 'alice' not in denied.text and PASSWORD not in denied.text


def test_retry_window_expires_and_other_accounts_remain_usable(core):
    user(core.client)
    user(core.client, 'bob@example.test')
    for _ in range(5):
        assert attempt(core).status_code == 401
    assert attempt(core, password=PASSWORD).status_code == 429
    assert attempt(core, email='bob@example.test', password=PASSWORD).status_code == 200
    core.state.now += timedelta(seconds=61)
    assert attempt(core, password=PASSWORD).status_code == 200


def test_spoofed_forwarded_headers_cannot_reset_the_guess_limit(core):
    user(core.client)
    for number in range(5):
        assert attempt(core, headers={'X-Forwarded-For': f'198.51.100.{number}'}).status_code == 401
    assert attempt(core, headers={'X-Forwarded-For': '203.0.113.20'}).status_code == 429


def test_successful_signin_resets_only_the_account_guess_bucket(core):
    user(core.client)
    assert attempt(core).status_code == 401
    assert attempt(core, password=PASSWORD).status_code == 200
    for _ in range(5):
        assert attempt(core).status_code == 401
    assert attempt(core).status_code == 429

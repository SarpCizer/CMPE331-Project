"""Login guessing must be bounded without revealing whether an account exists."""
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from fridgely_app.login_throttle import LoginThrottle

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


def test_simultaneous_guesses_cannot_reserve_more_than_the_allowed_window(core):
    throttle = LoginThrottle(lambda: core.state.now)
    def reserve(_):
        try:
            throttle.reserve('same-client', 'same-account@example.test')
            return True
        except HTTPException as error:
            assert error.status_code == 429
            return False
    with ThreadPoolExecutor(max_workers=20) as pool:
        allowed = list(pool.map(reserve, range(40)))
    assert sum(allowed) == 5


def test_rotating_accounts_is_bounded_and_expired_buckets_release_capacity(core):
    throttle = LoginThrottle(lambda: core.state.now, source_limit=3, max_buckets=4)
    for number in range(3):
        throttle.reserve('same-client', f'account-{number}@example.test')
        throttle.succeeded('same-client', f'account-{number}@example.test')
    with pytest.raises(HTTPException) as denied:
        throttle.reserve('same-client', 'another@example.test')
    assert denied.value.status_code == 429
    # A different source remains usable. At capacity, new keys fail closed.
    throttle.reserve('other-client', 'other@example.test')
    with pytest.raises(HTTPException) as full:
        throttle.reserve('third-client', 'third@example.test')
    assert full.value.status_code == 429
    core.state.now += timedelta(seconds=61)
    throttle.reserve('third-client', 'third@example.test')

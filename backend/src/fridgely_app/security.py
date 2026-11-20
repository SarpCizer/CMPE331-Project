from datetime import datetime, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Header, HTTPException
from sqlalchemy import select

from fridgely_collections.ports import AccountPrincipal
from .models import Account

PASSWORDS = PasswordHasher()
ISSUER = 'fridgely'
AUDIENCE = 'fridgely-web'


def utc_now():
    return datetime.now(timezone.utc)


class Authentication:
    def __init__(self, sessions, secret, clock=utc_now, lifetime=3600):
        if not isinstance(secret, str) or len(secret.encode()) < 32:
            raise ValueError('JWT_SECRET must contain at least 32 bytes')
        if not 60 <= lifetime <= 86400:
            raise ValueError('JWT lifetime must be between 60 and 86400 seconds')
        self.sessions, self.secret, self.clock, self.lifetime = sessions, secret, clock, lifetime
        # A missing account follows the same expensive verification path as a bad password.
        self.dummy_hash = PASSWORDS.hash('unusable-account-password')

    def issue(self, account_id):
        now = int(self.clock().timestamp())
        return jwt.encode({'sub':account_id, 'iat':now, 'exp':now+self.lifetime,
            'iss':ISSUER, 'aud':AUDIENCE}, self.secret, algorithm='HS256')

    def verify_password(self, encoded, password):
        try:
            return PASSWORDS.verify(encoded or self.dummy_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    def require_account(self, authorization: str | None = Header(default=None)):
        denied = HTTPException(401, 'Authentication required', headers={'WWW-Authenticate':'Bearer'})
        if not authorization or len(authorization) > 8192:
            raise denied
        scheme, _, token = authorization.partition(' ')
        if scheme.casefold() != 'bearer' or not token:
            raise denied
        try:
            # Signature/algorithm/audience/issuer are checked by PyJWT. Expiry uses the
            # same injected server clock as issuance and immutable inventory timestamps.
            claims = jwt.decode(token, self.secret, algorithms=['HS256'], issuer=ISSUER,
                audience=AUDIENCE, options={'require':['sub','exp','iat'],
                    'verify_exp':False, 'verify_iat':False})
            now = self.clock().timestamp()
            if (type(claims['exp']) is not int or type(claims['iat']) is not int
                    or claims['exp'] <= now or claims['iat'] > now + 30
                    or not isinstance(claims['sub'], str) or not claims['sub']):
                raise ValueError('Invalid claims')
            with self.sessions() as session:
                account = session.scalar(select(Account.id).where(Account.id == claims['sub']))
            if not account:
                raise ValueError('Missing account')
            return AccountPrincipal(account)
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            raise denied from None

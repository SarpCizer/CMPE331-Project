import re
from datetime import timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.schemas import ingredient_name
from .database import make_engine, session_factory
from .models import Account, InventoryEntry, Preferences
from .security import Authentication, PASSWORDS, utc_now


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Credentials(Command):
    email: Annotated[StrictStr, Field(max_length=254)]
    password: Annotated[StrictStr, Field(min_length=1, max_length=1024)]

    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        value = value.strip().casefold()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Invalid email')
        return value


class PreferenceCommand(Command):
    dietary: Annotated[list[Annotated[StrictStr, Field(min_length=1, max_length=128)]], Field(max_length=100)]
    allergens: Annotated[list[Annotated[StrictStr, Field(min_length=1, max_length=128)]], Field(max_length=100)]

    @field_validator('dietary', 'allergens')
    @classmethod
    def nonblank(cls, values):
        if any(not value.strip() for value in values):
            raise ValueError('Blank preference')
        return values


class InventoryCommand(Command):
    name: StrictStr


def iso_time(value):
    value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return value.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def inventory_names(session, owner):
    return list(session.scalars(select(InventoryEntry.name).where(InventoryEntry.owner_id == owner)
        .order_by(InventoryEntry.added_at, InventoryEntry.id)))


def preference_lists(session, owner):
    row = session.get(Preferences, owner)
    return (list(row.dietary), list(row.allergens)) if row else ([], [])


def create_core_app(*, database_url, jwt_secret, clock=utc_now, token_lifetime=3600):
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    authentication = Authentication(sessions, jwt_secret, clock, token_lifetime)
    app = FastAPI(title='Fridgely', docs_url=None, redoc_url=None)
    app.state.engine, app.state.sessions, app.state.authentication = engine, sessions, authentication
    router = APIRouter(route_class=CollectionsRoute)
    principal = authentication.require_account

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error):
        return JSONResponse({'error':'Invalid request'}, status_code=400)

    @app.exception_handler(HTTPException)
    async def http_error(_request, error):
        return JSONResponse({'error':'Authentication required' if error.status_code == 401 else 'Request denied'},
            status_code=error.status_code, headers=error.headers)

    @router.post('/accounts', status_code=201)
    def register(command: Credentials):
        if len(command.password) < 8:
            raise HTTPException(400)
        row = Account(id=uuid4().hex, email=command.email,
            password_hash=PASSWORDS.hash(command.password), created_at=clock())
        try:
            with sessions.begin() as session:
                session.add(row)
                session.flush()
                session.add(Preferences(owner_id=row.id, dietary=[], allergens=[]))
        except IntegrityError:
            raise HTTPException(409) from None
        return {'id':row.id, 'email':row.email}

    @router.post('/sessions')
    def sign_in(command: Credentials):
        with sessions() as session:
            row = session.scalar(select(Account).where(Account.email == command.email))
            valid = authentication.verify_password(row.password_hash if row else None, command.password)
            if not valid or row is None:
                raise HTTPException(401, headers={'WWW-Authenticate':'Bearer'})
            if PASSWORDS.check_needs_rehash(row.password_hash):
                row.password_hash = PASSWORDS.hash(command.password)
                session.commit()
            return {'token':authentication.issue(row.id)}

    @router.get('/profile/preferences')
    def get_preferences(user: AccountPrincipal = Depends(principal)):
        with sessions() as session:
            dietary, allergens = preference_lists(session, user.account_id)
            return {'dietary':dietary, 'allergens':allergens}

    @router.put('/profile/preferences')
    def put_preferences(command: PreferenceCommand, user: AccountPrincipal = Depends(principal)):
        with sessions.begin() as session:
            row = session.get(Preferences, user.account_id)
            row.dietary, row.allergens = list(command.dietary), list(command.allergens)
        return command.model_dump()

    @router.get('/inventory')
    def list_inventory(user: AccountPrincipal = Depends(principal)):
        with sessions() as session:
            rows = session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == user.account_id)
                .order_by(InventoryEntry.added_at, InventoryEntry.id))
            return [{'id':row.id,'name':row.name,'addedAt':iso_time(row.added_at)} for row in rows]

    @router.post('/inventory', status_code=201)
    def add_inventory(command: InventoryCommand, user: AccountPrincipal = Depends(principal)):
        name, _key = ingredient_name(command.name)
        row = InventoryEntry(id=uuid4().hex, owner_id=user.account_id, name=name, added_at=clock())
        with sessions.begin() as session:
            session.add(row)
        return {'id':row.id,'name':row.name,'addedAt':iso_time(row.added_at)}

    @router.delete('/inventory/{item_id}', status_code=204)
    def remove_inventory(item_id: str, user: AccountPrincipal = Depends(principal)):
        with sessions.begin() as session:
            removed = session.execute(delete(InventoryEntry).where(
                InventoryEntry.owner_id == user.account_id, InventoryEntry.id == item_id)).rowcount
            if not removed:
                raise HTTPException(404)
        return Response(status_code=204)

    @router.get('/health')
    def health():
        try:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
        except SQLAlchemyError:
            return JSONResponse({'status':'unavailable'}, status_code=503)
        return {'status':'ok'}

    app.include_router(router)
    return app

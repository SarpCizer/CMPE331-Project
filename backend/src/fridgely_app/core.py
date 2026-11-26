from datetime import timezone
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator
from email_validator import validate_email
from sqlalchemy import delete, literal, select, text, union_all
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.schemas import ingredient_name
from .database import make_engine, session_factory
from .models import Account, AllergenExclusion, DietaryPreference, InventoryEntry, Preferences
from .security import Authentication, PASSWORDS, hash_password, utc_now


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Credentials(Command):
    email: Annotated[StrictStr, Field(max_length=254)]
    password: Annotated[StrictStr, Field(min_length=1, max_length=1024)]

    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        value = value.strip().casefold()
        return validate_email(value, check_deliverability=False, test_environment=True).normalized


class PreferenceCommand(Command):
    dietary: Annotated[list[Annotated[StrictStr, Field(min_length=1, max_length=128)]], Field(max_length=100)]
    allergens: Annotated[list[Annotated[StrictStr, Field(min_length=1, max_length=128)]], Field(max_length=100)]

    @field_validator('dietary', 'allergens')
    @classmethod
    def nonblank(cls, values):
        if any(not value.strip() for value in values):
            raise ValueError('Blank preference')
        return values


class QuantityCommand(Command):
    quantity: Annotated[float, Field(gt=0, le=1000000, allow_inf_nan=False)] | None = None
    unit: Literal['pcs','kg','g','L','ml','pack','bunch'] | None = None

    @model_validator(mode='after')
    def validate_quantity(self):
        if (self.quantity is None) != (self.unit is None):
            raise ValueError('Quantity and unit must be supplied together')
        if self.unit in {'pcs','pack','bunch'} and not self.quantity.is_integer():
            raise ValueError('Count units require whole numbers')
        return self


class InventoryCommand(QuantityCommand):
    name: StrictStr


class InventoryUpdate(QuantityCommand):
    quantity: Annotated[float, Field(ge=0, le=1000000, allow_inf_nan=False)]
    unit: Literal['pcs','kg','g','L','ml','pack','bunch']


class AccountDTO(BaseModel):
    id: str
    email: str


class SessionDTO(BaseModel):
    token: str


class InventoryDTO(BaseModel):
    id: str
    name: str
    addedAt: str
    quantity: float | None = None
    unit: str | None = None


def iso_time(value):
    value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return value.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def inventory_payload(row):
    return {'id':row.id,'name':row.name,'addedAt':iso_time(row.added_at),
            'quantity':row.quantity,'unit':row.unit}


def inventory_amounts(session, owner):
    rows = session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == owner)
        .order_by(InventoryEntry.added_at, InventoryEntry.id))
    return tuple((row.name, row.quantity, row.unit) for row in rows if row.quantity is not None and row.quantity > 0)


def inventory_names(session, owner):
    return list(session.scalars(select(InventoryEntry.name).where(InventoryEntry.owner_id == owner,
        (InventoryEntry.quantity.is_(None)) | (InventoryEntry.quantity > 0))
        .order_by(InventoryEntry.added_at, InventoryEntry.id)))


def preference_lists(session, owner):
    # A single statement gives both lists one database snapshot and avoids the
    # parent lookup plus two lazy relationship reads on each profile request.
    queries = [select(literal(kind).label('kind'), model.position.label('position'),
        model.display_value.label('display_value')).where(model.owner_id == owner)
        for kind, model in [('dietary', DietaryPreference), ('allergens', AllergenExclusion)]]
    values = {'dietary': [], 'allergens': []}
    for kind, _position, value in session.execute(union_all(*queries).order_by('kind', 'position')):
        values[kind].append(value)
    return values['dietary'], values['allergens']


def create_core_app(*, database_url, jwt_secret, clock=utc_now, token_lifetime=3600):
    engine = make_engine(database_url)
    sessions = session_factory(engine)
    authentication = Authentication(sessions, jwt_secret, clock, token_lifetime)
    app = FastAPI(title='Fridgely API', version='0.4.0', docs_url=None, redoc_url=None,
        description='Accounts, owned fridge inventory, preferences, recipes and personal collections. '
            'Register and sign in, then authorize requests using the returned bearer token.',
        servers=[{'url':'/api'}], root_path_in_servers=False)
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

    @router.post('/accounts', status_code=201, response_model=AccountDTO, tags=['Accounts'])
    def register(command: Credentials):
        if len(command.password) < 8:
            raise HTTPException(400)
        row = Account(id=uuid4().hex, email=command.email,
            password_hash=hash_password(command.password), created_at=clock())
        try:
            with sessions.begin() as session:
                session.add(row)
                session.flush()
                session.add(Preferences(owner_id=row.id, dietary=[], allergens=[]))
        except IntegrityError:
            raise HTTPException(409) from None
        return {'id':row.id, 'email':row.email}

    @router.post('/sessions', response_model=SessionDTO, tags=['Accounts'])
    def sign_in(command: Credentials):
        with sessions() as session:
            row = session.scalar(select(Account).where(Account.email == command.email))
            valid = authentication.verify_password(row.password_hash if row else None, command.password)
            if not valid or row is None:
                raise HTTPException(401, headers={'WWW-Authenticate':'Bearer'})
            if PASSWORDS.check_needs_rehash(row.password_hash):
                row.password_hash = hash_password(command.password)
                session.commit()
            return {'token':authentication.issue(row.id)}

    @router.get('/profile/preferences', response_model=PreferenceCommand, tags=['Preferences'])
    def get_preferences(user: AccountPrincipal = Depends(principal)):
        with sessions() as session:
            dietary, allergens = preference_lists(session, user.account_id)
            return {'dietary':dietary, 'allergens':allergens}

    @router.put('/profile/preferences', response_model=PreferenceCommand, tags=['Preferences'])
    def put_preferences(command: PreferenceCommand, user: AccountPrincipal = Depends(principal)):
        with sessions.begin() as session:
            row = session.get(Preferences, user.account_id)
            row.dietary, row.allergens = list(command.dietary), list(command.allergens)
        return command.model_dump()

    @router.get('/inventory', response_model=list[InventoryDTO], tags=['Inventory'])
    def list_inventory(user: AccountPrincipal = Depends(principal)):
        with sessions() as session:
            rows = session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == user.account_id)
                .order_by(InventoryEntry.added_at, InventoryEntry.id))
            return [inventory_payload(row) for row in rows]

    @router.post('/inventory', status_code=201, response_model=InventoryDTO, tags=['Inventory'])
    def add_inventory(command: InventoryCommand, user: AccountPrincipal = Depends(principal)):
        name, _key = ingredient_name(command.name)
        row = InventoryEntry(id=uuid4().hex, owner_id=user.account_id, name=name, added_at=clock(),
            quantity=command.quantity, unit=command.unit)
        with sessions.begin() as session:
            session.add(row)
        return inventory_payload(row)

    @router.patch('/inventory/{item_id}', response_model=InventoryDTO, tags=['Inventory'])
    def update_inventory(item_id: str, command: InventoryUpdate, user: AccountPrincipal = Depends(principal)):
        with sessions.begin() as session:
            row = session.scalar(select(InventoryEntry).where(
                InventoryEntry.owner_id == user.account_id, InventoryEntry.id == item_id))
            if row is None:
                raise HTTPException(404)
            row.quantity, row.unit = command.quantity, command.unit
        return inventory_payload(row)

    @router.delete('/inventory/{item_id}', status_code=204, tags=['Inventory'])
    def remove_inventory(item_id: str, user: AccountPrincipal = Depends(principal)):
        with sessions.begin() as session:
            removed = session.execute(delete(InventoryEntry).where(
                InventoryEntry.owner_id == user.account_id, InventoryEntry.id == item_id)).rowcount
            if not removed:
                raise HTTPException(404)
        return Response(status_code=204)

    @router.get('/health', tags=['Operations'])
    def health():
        try:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
        except SQLAlchemyError:
            return JSONResponse({'status':'unavailable'}, status_code=503)
        return {'status':'ok'}

    app.include_router(router)
    return app

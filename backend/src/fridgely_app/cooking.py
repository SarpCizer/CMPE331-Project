"""Explicit, atomic and retry-safe manual confirmation of cooking."""
import hashlib
import json
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, model_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.errors import CollectionError
from .core import Command
from .models import CookingConfirmation, InventoryEntry


class UsedIngredient(Command):
    inventoryId: Annotated[str, Field(min_length=1, max_length=128)]
    quantity: Annotated[float, Field(gt=0, le=1000000, allow_inf_nan=False)]
    unit: Literal['pcs', 'kg', 'g', 'L', 'ml', 'pack', 'bunch']

    @model_validator(mode='after')
    def whole_counts(self):
        if self.unit in {'pcs', 'pack', 'bunch'} and not self.quantity.is_integer():
            raise ValueError('Count units require whole numbers')
        return self


class CookCommand(Command):
    requestId: Annotated[str, Field(min_length=16, max_length=64, pattern=r'^[a-zA-Z0-9-]+$')]
    items: Annotated[list[UsedIngredient], Field(min_length=1, max_length=100)]

    @model_validator(mode='after')
    def unique_items(self):
        if len({item.inventoryId for item in self.items}) != len(self.items):
            raise ValueError('Select each inventory entry once')
        return self


def cooking_router(sessions, require_account, recipes):
    router = APIRouter(route_class=CollectionsRoute)

    @router.post('/recipes/{recipe_id}/cook', tags=['Recipes'])
    def cook(recipe_id: str, command: CookCommand, user: AccountPrincipal = Depends(require_account)):
        owner = user.account_id
        digest = hashlib.sha256(json.dumps({'recipe': recipe_id, 'items': sorted(
            [item.model_dump() for item in command.items], key=lambda item: item['inventoryId'])},
            sort_keys=True, separators=(',', ':')).encode()).hexdigest()

        def replay(session):
            prior = session.get(CookingConfirmation, (owner, command.requestId))
            if prior is None:
                return False
            if prior.payload_hash != digest:
                raise CollectionError(409, 'This confirmation was already used for a different action.')
            return True

        try:
            with sessions.begin() as session:
                owned = recipes.find_owned(session, owner, recipe_id)
                if owned is None:
                    raise HTTPException(404)
                if replay(session):
                    return {'completed': True, 'replayed': True}
                session.add(CookingConfirmation(owner_id=owner, request_id=command.requestId,
                    recipe_id=recipe_id, payload_hash=digest))
                session.flush()
                allowed = {name.strip().casefold() for name in owned.recipe.ingredients}
                for used in command.items:
                    row = session.scalar(select(InventoryEntry).where(
                        InventoryEntry.owner_id == owner, InventoryEntry.id == used.inventoryId))
                    if row is None:
                        raise HTTPException(404)
                    if row.name.strip().casefold() not in allowed:
                        raise CollectionError(400, 'Only ingredients in this recipe can be deducted.')
                    if row.quantity is None or row.unit != used.unit or row.quantity < used.quantity:
                        raise CollectionError(409, 'Stock changed or is insufficient. Review the quantities again.')
                    remaining = float(Decimal(str(row.quantity)) - Decimal(str(used.quantity)))
                    changed = session.execute(update(InventoryEntry).where(
                        InventoryEntry.owner_id == owner, InventoryEntry.id == row.id,
                        InventoryEntry.unit == used.unit, InventoryEntry.quantity == row.quantity,
                        InventoryEntry.quantity >= used.quantity).values(quantity=remaining))
                    if changed.rowcount != 1:
                        raise CollectionError(409, 'Stock changed. Review the quantities again.')
            return {'completed': True, 'replayed': False}
        except IntegrityError:
            # A concurrent retry may have committed the same confirmation.
            with sessions() as session:
                if replay(session):
                    return {'completed': True, 'replayed': True}
            raise CollectionError(409, 'Stock changed. Review the quantities again.') from None

    return router

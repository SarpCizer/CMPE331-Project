"""Explicit purchased-to-fridge confirmation; one atomic purchase per list item."""
import hashlib
import json
from decimal import Decimal
from time import sleep
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import delete, select, update
from sqlalchemy.exc import OperationalError

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.errors import CollectionError
from fridgely_collections.models import ShoppingItem
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.repository import dialect_insert
from fridgely_collections.schemas import ShoppingQuantity, identifier, ingredient_name
from fridgely_collections.service import retryable_transaction_error
from .models import Account, InventoryEntry, PurchaseConfirmation

_UNITS = {'g': ('mass', Decimal(1)), 'kg': ('mass', Decimal(1000)),
          'ml': ('volume', Decimal(1)), 'L': ('volume', Decimal(1000)),
          **{u: (u, Decimal(1)) for u in ('pcs', 'pack', 'bunch')}}


class PurchaseCommand(ShoppingQuantity):
    quantity: Annotated[float, Field(gt=0, le=1000000, allow_inf_nan=False)]
    unit: Literal['pcs', 'kg', 'g', 'L', 'ml', 'pack', 'bunch']


def _receipt(session, owner, item_id, digest):
    prior = session.get(PurchaseConfirmation, (owner, item_id))
    if prior is None:
        return None
    if prior.payload_hash != digest:
        raise CollectionError(409, 'This item was already purchased with different quantities. Refresh your fridge.')
    return {'completed': True, 'replayed': True, 'inventoryId': prior.inventory_id}


def _purchase(session, owner, item_id, command, digest, clock):
    # Serialize purchases of this account on PostgreSQL. SQLite write conflicts
    # retry the whole transaction below; the unique receipt also claims the item.
    session.scalar(select(Account.id).where(Account.id == owner).with_for_update())
    prior = _receipt(session, owner, item_id, digest)
    if prior is not None:
        return prior
    item = session.scalar(select(ShoppingItem).where(
        ShoppingItem.owner_id == owner, ShoppingItem.id == item_id).with_for_update())
    if item is None:
        # On SQLite another purchase can commit between the two reads.
        prior = _receipt(session, owner, item_id, digest)
        if prior is not None:
            return prior
        raise CollectionError(404, 'Not found')
    dimension, scale = _UNITS[command.unit]
    rows = session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == owner)
        .order_by(InventoryEntry.added_at, InventoryEntry.id).with_for_update()).all()
    candidates = [row for row in rows if ingredient_name(row.name)[1] == item.name_key
        and row.quantity is not None and row.unit in _UNITS and _UNITS[row.unit][0] == dimension]
    row = next((row for row in candidates if row.unit == command.unit), next(iter(candidates), None))
    inventory_id = row.id if row is not None else uuid4().hex
    claimed = session.execute(dialect_insert(session, PurchaseConfirmation).values(
        owner_id=owner, item_id=item_id, payload_hash=digest, inventory_id=inventory_id
    ).on_conflict_do_nothing(index_elements=['owner_id', 'item_id']).returning(PurchaseConfirmation.item_id)).scalar_one_or_none()
    if claimed is None:
        prior = _receipt(session, owner, item_id, digest)
        if prior is None:
            raise CollectionError(409, 'Purchase changed. Refresh and try again.')
        return prior
    if row is None:
        session.add(InventoryEntry(id=inventory_id, owner_id=owner, name=item.name,
            quantity=command.quantity, unit=command.unit, added_at=clock()))
    else:
        amount = Decimal(str(command.quantity)) * scale / _UNITS[row.unit][1]
        total = Decimal(str(row.quantity)) + amount
        if total > 1000000:
            raise CollectionError(409, 'Fridge quantity would exceed its limit. Review the purchase amount.')
        session.execute(update(InventoryEntry).where(InventoryEntry.owner_id == owner,
            InventoryEntry.id == inventory_id).values(quantity=float(total)))
    removed = session.execute(delete(ShoppingItem).where(
        ShoppingItem.owner_id == owner, ShoppingItem.id == item_id))
    if removed.rowcount != 1:
        raise CollectionError(409, 'Shopping item changed. Refresh and try again.')
    return {'completed': True, 'replayed': False, 'inventoryId': inventory_id}


def purchase_router(sessions, require_account, clock):
    router = APIRouter(route_class=CollectionsRoute)

    @router.post('/shopping-items/{item_id}/purchase', tags=['Shopping'],
                 summary='Confirm bought quantity, add it to fridge and remove shopping item')
    def purchase(item_id: str, command: PurchaseCommand, user: AccountPrincipal = Depends(require_account)):
        owner = identifier(user.account_id)
        identifier(item_id)
        digest = hashlib.sha256(json.dumps(command.model_dump(), sort_keys=True).encode()).hexdigest()
        for attempt in range(4):
            try:
                with sessions.begin() as session:
                    result = _purchase(session, owner, item_id, command, digest, clock)
                return result  # The inventory, receipt and removal have committed.
            except OperationalError as error:
                if attempt == 3 or not retryable_transaction_error(error):
                    raise
                sleep(.01 * (attempt + 1))
        raise AssertionError('unreachable')

    return router

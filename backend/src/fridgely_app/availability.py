"""Read-only, recipe-aware stock comparison for the collection integration port."""
from collections import defaultdict
from decimal import Decimal
import re

from sqlalchemy import select

from fridgely_collections.schemas import ingredient_name
from .models import InventoryEntry

_UNITS = {'g': ('mass', Decimal(1)), 'kg': ('mass', Decimal(1000)),
          'ml': ('volume', Decimal(1)), 'l': ('volume', Decimal(1000)),
          **{u: (u, Decimal(1)) for u in ('pcs', 'pack', 'bunch')}}
_AMOUNT = re.compile(r'\s*(\d+(?:\.\d+)?)\s*(g|kg|ml|l|pcs|pack|bunch)?\s*', re.I)


def _amount(text):
    match = _AMOUNT.fullmatch(text or '')
    if not match:
        return None
    quantity = Decimal(match[1])
    unit = _UNITS.get((match[2] or 'pcs').lower())
    if unit is None:
        return None
    dimension, scale = unit
    if quantity <= 0 or (dimension in {'pcs', 'pack', 'bunch'} and quantity != quantity.to_integral_value()):
        return None
    return dimension, quantity * scale


def inventory_for_recipe(session, owner, recipe):
    """Return present names, except reliably measured shortages.

    Unknown quantities, legacy amounts and incompatible dimensions keep the old
    name-based behavior. We never infer ingredient density or mutate inventory.
    Duplicate compatible stock and recipe rows are summed using decimal units.
    """
    stock = defaultdict(list)
    for row in session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == owner)):
        if row.quantity is None or row.quantity > 0:
            stock[ingredient_name(row.name)[1]].append(row)
    required = defaultdict(list)
    for index, name in enumerate(recipe.ingredients):
        amount = recipe.ingredientAmounts[index] if recipe.ingredientAmounts else None
        required[ingredient_name(name)[1]].append(_amount(amount))
    available = set(stock)
    for name, amounts in required.items():
        rows = stock.get(name, [])
        # Any ambiguous component means that we cannot prove a shortage.
        if not rows or any(amount is None for amount in amounts):
            continue
        dimensions = {amount[0] for amount in amounts}
        if len(dimensions) != 1:
            continue
        dimension = next(iter(dimensions))
        if any(row.quantity is None or not row.unit or
               _UNITS.get(row.unit.lower(), (None,))[0] != dimension for row in rows):
            continue
        total = sum((Decimal(str(row.quantity)) * _UNITS[row.unit.lower()][1] for row in rows), Decimal(0))
        needed = sum((amount[1] for amount in amounts), Decimal(0))
        if total < needed:
            available.discard(name)
    return [stock[name][0].name for name in sorted(available)]

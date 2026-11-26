"""Read-only recipe stock comparison and measured shopping deficits."""
from collections import defaultdict
from decimal import Decimal
import re

from sqlalchemy import select

from fridgely_collections.schemas import ShoppingCommand, ingredient_name
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


def _snapshot(session, owner, recipe):
    stock, required, displays = defaultdict(list), defaultdict(list), {}
    for row in session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == owner)):
        if row.quantity is None or row.quantity > 0:
            stock[ingredient_name(row.name)[1]].append(row)
    for index, name in enumerate(recipe.ingredients):
        display, key = ingredient_name(name)
        displays.setdefault(key, display)
        measurement = recipe.ingredientAmounts[index] if recipe.ingredientAmounts else None
        required[key].append(_amount(measurement))
    return stock, required, displays


def _shortfall(amounts, rows):
    if any(amount is None for amount in amounts):
        return None
    dimensions = {amount[0] for amount in amounts}
    if len(dimensions) != 1:
        return None
    dimension = next(iter(dimensions))
    if any(row.quantity is None or not row.unit or
           _UNITS.get(row.unit.lower(), (None,))[0] != dimension for row in rows):
        return None
    needed = sum((amount[1] for amount in amounts), Decimal(0))
    available = sum((Decimal(str(row.quantity)) * _UNITS[row.unit.lower()][1] for row in rows), Decimal(0))
    return dimension, max(Decimal(0), needed - available)


def _shopping_amount(dimension, value):
    unit = {'mass': 'g', 'volume': 'ml'}.get(dimension, dimension)
    if value > 1000000 and dimension in {'mass', 'volume'}:
        value /= 1000
        unit = 'kg' if dimension == 'mass' else 'L'
    if not 0 < value <= 1000000:
        return {}  # Unsupported legacy extremes require a reviewed manual amount.
    return {'quantity': float(value), 'unit': unit}


def recipe_shopping_items(session, owner, recipe):
    """Report true deficits without changing stock or inventing legacy quantities."""
    stock, required, displays = _snapshot(session, owner, recipe)
    missing = []
    for key, amounts in required.items():
        rows = stock.get(key, [])
        measured = _shortfall(amounts, rows)
        if measured is not None and measured[1] > 0:
            missing.append(ShoppingCommand(name=displays[key], **_shopping_amount(*measured)))
        elif not rows and measured is None:
            missing.append(ShoppingCommand(name=displays[key]))
    return missing


def inventory_for_recipe(session, owner, recipe):
    """Compatibility names port: preserve display names and unknown-stock behavior."""
    stock, required, _displays = _snapshot(session, owner, recipe)
    available = set(stock)
    for key, amounts in required.items():
        measured = _shortfall(amounts, stock.get(key, []))
        if measured is not None and measured[1] > 0:
            available.discard(key)
    return [stock[key][0].name for key in sorted(available)]

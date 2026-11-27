"""Read-only recipe stock comparison and measured shopping deficits."""
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from math import ceil

from sqlalchemy import select

from fridgely_collections.schemas import ShoppingCommand, ingredient_name
from .models import InventoryEntry

_UNITS = {'g': ('mass', Decimal(1)), 'kg': ('mass', Decimal(1000)),
          'ml': ('volume', Decimal(1)), 'l': ('volume', Decimal(1000)),
          **{u: (u, Decimal(1)) for u in ('pcs', 'pack', 'bunch')}}


def _number_end(value):
    end = 0
    while end < len(value) and value[end].isdecimal():
        end += 1
    if end == 0:
        return None
    if end < len(value) and value[end] == '.':
        end += 1
        fraction_start = end
        while end < len(value) and value[end].isdecimal():
            end += 1
        if end == fraction_start:
            return None
    return end


def _measurement(text):
    """Parse the bounded metric/count grammar in linear time, without backtracking."""
    if not isinstance(text, str) or len(text) > 64:
        return None
    value = text.strip()
    end = _number_end(value)
    if end is None:
        return None
    quantity = Decimal(value[:end])
    source_unit = value[end:].strip().lower() or 'pcs'
    unit = _UNITS.get(source_unit)
    if unit is None:
        return None
    dimension, scale = unit
    if quantity <= 0 or (dimension in {'pcs', 'pack', 'bunch'} and quantity != quantity.to_integral_value()):
        return None
    return dimension, quantity * scale, source_unit


def _amount(text):
    measured = _measurement(text)
    return measured[:2] if measured is not None else None


def _requirements_snapshot(session, owner, measurements):
    stock, required, displays = defaultdict(list), defaultdict(list), {}
    for row in session.scalars(select(InventoryEntry).where(InventoryEntry.owner_id == owner)):
        if row.quantity is None or row.quantity > 0:
            stock[ingredient_name(row.name)[1]].append(row)
    for name, measurement in measurements:
        display, key = ingredient_name(name)
        displays.setdefault(key, display)
        required[key].append(measurement if isinstance(measurement, tuple) else _amount(measurement))
    return stock, required, displays


def _snapshot(session, owner, recipe):
    return _requirements_snapshot(session, owner, [(name,
        recipe.ingredientAmounts[index] if recipe.ingredientAmounts else None)
        for index, name in enumerate(recipe.ingredients)])


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
    needed = sum((Fraction(amount[1]) for amount in amounts), Fraction(0))
    available = sum((Fraction(Decimal(str(row.quantity))) * Fraction(_UNITS[row.unit.lower()][1]) for row in rows), Fraction(0))
    return dimension, max(Fraction(0), needed - available)


def _shopping_amount(dimension, value, round_for_purchase=False):
    unit = {'mass': 'g', 'volume': 'ml'}.get(dimension, dimension)
    if value > 1000000 and dimension in {'mass', 'volume'}:
        value /= 1000
        unit = 'kg' if dimension == 'mass' else 'L'
    if round_for_purchase:
        value = ceil(value) if dimension in {'pcs', 'pack', 'bunch'} else Fraction(ceil(value * 1000), 1000)
    if not 0 < value <= 1000000:
        return {}  # Unsupported legacy extremes require a reviewed manual amount.
    return {'quantity': float(value), 'unit': unit}


def requirements_shopping_items(session, owner, measurements, *, round_for_purchase=False):
    """Aggregate all requirements first and subtract each stock group once."""
    stock, required, displays = _requirements_snapshot(session, owner, measurements)
    missing, review = [], []
    for key, amounts in required.items():
        rows = stock.get(key, [])
        measured = _shortfall(amounts, rows)
        if measured is not None and measured[1] > 0:
            quantity = _shopping_amount(*measured, round_for_purchase=round_for_purchase)
            missing.append(ShoppingCommand(name=displays[key], **quantity))
            if not quantity:
                review.append(displays[key])
        elif measured is None:
            review.append(displays[key])
            if not rows:
                missing.append(ShoppingCommand(name=displays[key]))
    return missing, review


def recipe_shopping_items(session, owner, recipe):
    measurements = [(name, recipe.ingredientAmounts[index] if recipe.ingredientAmounts else None)
                    for index, name in enumerate(recipe.ingredients)]
    return requirements_shopping_items(session, owner, measurements)[0]


def inventory_for_recipe(session, owner, recipe):
    """Compatibility names port: preserve display names and unknown-stock behavior."""
    stock, required, _displays = _snapshot(session, owner, recipe)
    available = set(stock)
    for key, amounts in required.items():
        measured = _shortfall(amounts, stock.get(key, []))
        if measured is not None and measured[1] > 0:
            available.discard(key)
    return [stock[key][0].name for key in sorted(available)]

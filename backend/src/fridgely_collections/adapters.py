from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .schemas import RecipeDTO
from .errors import CollectionError


def recipe_from_zip_record(record: Mapping[str, Any], *, internal_id: str,
                           ingredient_names: list[str], steps: list[str],
                           cooking_minutes: float, calories_per_serving: float,
                           servings: int) -> RecipeDTO:
    """Adapt backend.zip/recipe_recommendation.zip's title to the approved DTO.

    Canonical names, ordered steps and missing estimate fields must be supplied
    by the recipe owner. Do not guess them from quantity-bearing ingredient_str,
    invent nutritional values, reuse a provider row ID as an owned application ID,
    or load the pickle in this module.
    """
    title = record.get("title", record.get("name", record.get("recipe")))
    return RecipeDTO(id=internal_id, title=title, ingredients=ingredient_names,
        steps=steps, cookingMinutes=cooking_minutes,
        caloriesPerServing=calories_per_serving, servings=servings)


def zip_inventory_reader(*, inventory_model, ingredient_model):
    """Read backend.zip's UserInventory/Ingredient mapping without importing main.

    The host owns the models and authentication. Use this only if these are the
    selected inventory tables; the reader never writes quantity/expiry or stock.
    """
    def read(session: Session, owner_id: str) -> Sequence[str]:
        # Uploaded UserInventory.user_id is Integer. Bind an integer on PostgreSQL
        # too; do not rely on SQLite's permissive string/integer comparison.
        key = owner_id
        if inventory_model.user_id.type.python_type is int:
            try:
                key = int(owner_id)
            except (ValueError, TypeError):
                raise CollectionError(503, "Inventory owner mapping is not configured") from None
            if str(key) != owner_id:
                raise CollectionError(503, "Inventory owner mapping is not configured")
        return list(session.scalars(select(ingredient_model.name)
            .join(inventory_model, inventory_model.ingredient_id == ingredient_model.id)
            .where(inventory_model.user_id == key)))
    return read

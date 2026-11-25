from typing import Annotated
import unicodedata

from pydantic import (
    BaseModel, ConfigDict, Field, FiniteFloat, StrictInt, StringConstraints,
    model_serializer, model_validator,
)

from .errors import CollectionError

Nonblank = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
Identifier = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=128)]
IngredientAmount = Annotated[str, StringConstraints(
    strict=True, strip_whitespace=True, min_length=1, max_length=64,
)]


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ShoppingCommand(DTO):
    name: str


class FavoriteCommand(DTO):
    recipeId: Identifier


class EmptyCommand(DTO):
    pass


class ShoppingItemDTO(DTO):
    id: Identifier
    name: Nonblank


class RecipeDTO(DTO):
    id: Identifier
    title: Nonblank
    ingredients: Annotated[list[Nonblank], Field(min_length=1)]
    ingredientAmounts: list[IngredientAmount] | None = None
    steps: Annotated[list[Nonblank], Field(min_length=1)]
    cookingMinutes: Annotated[FiniteFloat, Field(gt=0)]
    caloriesPerServing: Annotated[FiniteFloat, Field(ge=0)]
    servings: Annotated[StrictInt, Field(gt=0)]

    @model_validator(mode="after")
    def validate_amounts(self):
        amounts = self.ingredientAmounts
        if amounts is not None and (
            len(amounts) != len(self.ingredients)
            or any(unicodedata.category(char).startswith("C") for amount in amounts for char in amount)
        ):
            raise ValueError("Ingredient amounts must match the ingredient list in order.")
        return self

    @model_serializer(mode="wrap")
    def serialize_recipe(self, handler):
        payload = handler(self)
        if self.ingredientAmounts is None:
            payload.pop("ingredientAmounts", None)
        return payload


class HistoryDTO(DTO):
    recipe: RecipeDTO
    lastViewedAt: str


def identifier(value: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > 128
            or any(unicodedata.category(c).startswith("C") for c in value)):
        raise CollectionError(400, "Invalid resource identifier")
    return value


def ingredient_name(value: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise CollectionError(400, "Item name must be a string")
    display = value.strip()
    key = display.casefold()
    if (not display or len(display) > 256 or len(key) > 512
            or any(unicodedata.category(c).startswith("C") for c in display)):
        raise CollectionError(400, "Item name must be nonblank and at most 256 characters")
    return display, key

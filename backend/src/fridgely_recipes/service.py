import asyncio
import logging
from dataclasses import dataclass, replace
from typing import Callable, Protocol
from uuid import uuid4

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from fridgely_collections.errors import CollectionError
from fridgely_collections.schemas import RecipeDTO, ingredient_name
from .moods import Mood, MOOD_MAX_MINUTES
from .quality import RecipeQualityError, review_recipe

MAX_PROVIDER_SECONDS = 28


class RecipeError(Exception):
    def __init__(self, status: int, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.status, self.retryable = status, retryable


@dataclass(frozen=True)
class GenerationInput:
    ingredients: tuple[str, ...]
    dietary: tuple[str, ...]
    allergens: tuple[str, ...]
    amounts: tuple[tuple[str, float | None, str | None], ...] = ()
    requested_dish: str | None = None
    requested_servings: int | None = None
    mood: Mood | None = None


class RecipeProvider(Protocol):
    async def generate(self, data: GenerationInput) -> object: ...


def reviewed_batch(recipes, *, curate):
    reviewed = []
    for recipe in recipes:
        try:
            recipe = review_recipe(recipe)
        except ValueError as error:
            if not curate or not isinstance(error, RecipeQualityError):
                raise RecipeError(502, 'The recipe service returned an invalid response.') from None
            logging.getLogger(__name__).warning('Recipe candidate withheld code=%s', error.code)
            continue
        reviewed.append(recipe)
    if not reviewed:
        raise RecipeError(502, 'The recipe service returned no usable complete recipes. Please try again.')
    return reviewed


def validate_batch(candidates: object, allergens: tuple[str, ...], *, curate=False) -> list[RecipeDTO]:
    if not isinstance(candidates, list) or not candidates:
        raise RecipeError(502, "The recipe service returned an invalid response.")

    recipes = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise RecipeError(502, "The recipe service returned an invalid response.")
        fields = {key: candidate.get(key) for key in RecipeDTO.model_fields if key != "id"}
        try:
            recipe = RecipeDTO(id=uuid4().hex, **fields)
            for name in recipe.ingredients:
                ingredient_name(name)
            recipes.append(recipe)
        except (CollectionError, ValueError) as error:
            if isinstance(error, ValidationError):
                first = error.errors(include_input=False, include_context=False)[0]
                logging.getLogger(__name__).warning("Recipe validation rejected field=%s code=%s", first["loc"][0] if first["loc"] else "recipe", first["type"])
            raise RecipeError(502, "The recipe service returned an invalid response.") from None

    exclusions = {name.strip().casefold() for name in allergens}
    if any(name.strip().casefold() in exclusions for recipe in recipes for name in recipe.ingredients):
        raise RecipeError(422, "The recipe suggestions contain an excluded ingredient.")
    return reviewed_batch(recipes, curate=curate)


class RecipeGenerationService:
    def __init__(
        self,
        read_input: Callable[[str], GenerationInput],
        provider: RecipeProvider,
        insert_batch: Callable[[str, list[RecipeDTO]], None],
        timeout_seconds: float = MAX_PROVIDER_SECONDS,
    ):
        if not 0 < timeout_seconds <= MAX_PROVIDER_SECONDS:
            raise ValueError("Provider timeout must be positive and at most 28 seconds.")
        self.read_input = read_input
        self.provider = provider
        self.insert_batch = insert_batch
        self.timeout_seconds = timeout_seconds

    async def generate(self, owner_id: str, mood: Mood | None = None) -> list[RecipeDTO]:
        data = await run_in_threadpool(self.read_input, owner_id)
        if mood is not None:
            data = replace(data, mood=mood)
        if not data.ingredients:
            raise RecipeError(400, "Add an ingredient to your fridge before generating recipes.")

        try:
            async with asyncio.timeout(self.timeout_seconds):
                candidates = await self.provider.generate(data)
        except Exception:
            raise RecipeError(503, "The recipe service is temporarily unavailable.", retryable=True) from None

        recipes = validate_batch(candidates, data.allergens, curate=True)
        limit = MOOD_MAX_MINUTES.get(data.mood)
        if limit is not None and any(recipe.cookingMinutes > limit for recipe in recipes):
            raise RecipeError(502, 'The recipe suggestions exceed your selected time limit. Please try again.')
        await run_in_threadpool(self.insert_batch, owner_id, recipes)
        return recipes


async def requested_recipe(data: GenerationInput, provider, timeout_seconds):
    """Generate one measured requested dish; callers own the atomic save/plan transaction."""
    try:
        async with asyncio.timeout(timeout_seconds):
            candidates = await provider.generate(data)
    except Exception:
        raise RecipeError(503, 'The recipe service is temporarily unavailable. Try again or choose a saved recipe.', retryable=True) from None
    from .provider import recipe_batch
    recipes = validate_batch(recipe_batch({'recipes': candidates}), data.allergens)
    if len(recipes) != 1 or recipes[0].servings != data.requested_servings:
        raise RecipeError(502, 'The recipe service did not return the requested portions. Please try again.')
    return recipes[0]

import asyncio
from dataclasses import dataclass
from typing import Callable, Protocol
from uuid import uuid4

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from fridgely_collections.errors import CollectionError
from fridgely_collections.schemas import RecipeDTO, ingredient_name

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


class RecipeProvider(Protocol):
    async def generate(self, data: GenerationInput) -> object: ...


def validate_batch(candidates: object, allergens: tuple[str, ...]) -> list[RecipeDTO]:
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
        except (ValidationError, CollectionError):
            raise RecipeError(502, "The recipe service returned an invalid response.") from None

    exclusions = {name.strip().casefold() for name in allergens}
    if any(name.strip().casefold() in exclusions for recipe in recipes for name in recipe.ingredients):
        raise RecipeError(422, "The recipe suggestions contain an excluded ingredient.")
    return recipes


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

    async def generate(self, owner_id: str) -> list[RecipeDTO]:
        data = await run_in_threadpool(self.read_input, owner_id)
        if not data.ingredients:
            raise RecipeError(400, "Add an ingredient to your fridge before generating recipes.")

        try:
            async with asyncio.timeout(self.timeout_seconds):
                candidates = await self.provider.generate(data)
        except Exception:
            raise RecipeError(503, "The recipe service is temporarily unavailable.", retryable=True) from None

        recipes = validate_batch(candidates, data.allergens)
        await run_in_threadpool(self.insert_batch, owner_id, recipes)
        return recipes

from datetime import datetime, timezone
from collections.abc import Sequence
from time import sleep
from typing import Callable, TypeVar

from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .errors import CollectionError, not_found
from .ports import CoreData, OwnedRecipe
from .repository import CollectionRepository
from .schemas import HistoryDTO, RecipeDTO, ShoppingCommand, identifier, ingredient_name

T = TypeVar("T")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def retryable_transaction_error(error: OperationalError) -> bool:
    code = getattr(error.orig, "sqlstate", None) or getattr(error.orig, "pgcode", None)
    sqlite_code = getattr(error.orig, "sqlite_errorcode", 0)
    return code in {"40001", "40P01"} or (sqlite_code & 0xff) in {5, 6}


class CollectionsService:
    def __init__(self, session_factory: Callable[[], Session], core: CoreData,
                 clock: Callable[[], datetime] = utc_now):
        self.sessions, self.core, self.clock = session_factory, core, clock

    def _transaction(self, operation: Callable[[Session, CollectionRepository], T]) -> T:
        for attempt in range(4):
            try:
                with self.sessions() as session:
                    with session.begin():
                        result = operation(session, CollectionRepository(session))
                    # Commit has succeeded before a caller can send an HTTP success.
                    return result
            except OperationalError as error:
                if attempt == 3 or not retryable_transaction_error(error):
                    raise
                sleep(0.01 * (attempt + 1))
        raise AssertionError("unreachable")

    def _recipe(self, session: Session, owner: str, recipe_id: str) -> RecipeDTO:
        value = self.core.recipe(session, owner, recipe_id)
        if value is None:
            raise not_found()
        if not isinstance(value, OwnedRecipe):
            raise CollectionError(503, "Recipe integration returned invalid data")
        if value.owner_id != owner:
            raise not_found()
        try:
            recipe = RecipeDTO.model_validate(value.recipe.model_dump())
        except (ValidationError, AttributeError):
            raise CollectionError(503, "Recipe integration returned invalid data") from None
        if recipe.id != recipe_id:
            raise not_found()
        return recipe

    def add_item(self, owner: str, name: str, quantity=None, unit=None):
        identifier(owner)
        display, key = ingredient_name(name)
        try:
            amount = ShoppingCommand(name=display, quantity=quantity, unit=unit)
        except ValidationError:
            raise CollectionError(400, 'Invalid shopping quantity') from None
        return self._transaction(lambda session, repo: repo.add_item(owner, display, key, amount.quantity, amount.unit))

    def items(self, owner: str):
        identifier(owner)
        return self._transaction(lambda session, repo: repo.items(owner))

    def delete_item(self, owner: str, item_id: str) -> None:
        identifier(owner), identifier(item_id)
        def remove(session, repo):
            if not repo.delete_item(owner, item_id):
                raise not_found()
        self._transaction(remove)

    def _missing_items(self, session, owner, recipe):
        reader = getattr(self.core, 'shopping_shortages', None)
        supplied = reader(session, owner, recipe) if callable(reader) else None
        if supplied is not None:
            if not isinstance(supplied, Sequence) or isinstance(supplied, (str, bytes)):
                raise TypeError('Shortage port must return a sequence')
            return [ShoppingCommand.model_validate(item) for item in supplied]
        reader = getattr(self.core, 'inventory_for_recipe', None)
        names = reader(session, owner, recipe) if callable(reader) else self.core.inventory_names(session, owner)
        if not isinstance(names, Sequence) or isinstance(names, (str, bytes)):
            raise TypeError('Inventory port must return a sequence of names')
        fridge = {ingredient_name(name)[1] for name in names}
        return [ShoppingCommand(name=name) for name in recipe.ingredients if ingredient_name(name)[1] not in fridge]

    def add_missing(self, owner: str, recipe_id: str):
        identifier(owner), identifier(recipe_id)
        def add(session, repo):
            recipe = self._recipe(session, owner, recipe_id)
            try:
                missing = {}
                for item in self._missing_items(session, owner, recipe):
                    display, key = ingredient_name(item.name)
                    missing.setdefault(key, (display, item))
            except (CollectionError, ValidationError, TypeError):
                raise CollectionError(503, 'Ingredient integration returned invalid data') from None
            for key, (display, item) in missing.items():
                repo.add_item(owner, display, key, item.quantity, item.unit, minimum=True)
            return repo.items(owner)
        return self._transaction(add)

    def save_favorite(self, owner: str, recipe_id: str) -> RecipeDTO:
        identifier(owner), identifier(recipe_id)
        def save(session, repo):
            recipe = self._recipe(session, owner, recipe_id)
            repo.save_favorite(owner, recipe_id)
            return recipe
        return self._transaction(save)

    def favorites(self, owner: str) -> list[RecipeDTO]:
        identifier(owner)
        return self._transaction(lambda session, repo: [
            self._recipe(session, owner, rid) for rid in repo.favorite_ids(owner)])

    def delete_favorite(self, owner: str, recipe_id: str) -> None:
        identifier(owner), identifier(recipe_id)
        def remove(session, repo):
            if not repo.delete_favorite(owner, recipe_id):
                raise not_found()
        self._transaction(remove)

    def open_recipe(self, owner: str, recipe_id: str) -> RecipeDTO:
        identifier(owner), identifier(recipe_id)
        def record(session, repo):
            recipe = self._recipe(session, owner, recipe_id)
            # Resolve ownership first: an unavailable clock cannot mask a 404 or
            # be invoked at all for a missing/foreign recipe (issues #30/#34).
            try:
                at = self.clock()
                if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
                    raise ValueError("Clock must return an aware datetime")
                at = at.astimezone(timezone.utc)
            except Exception:
                raise CollectionError(503, "View timestamp temporarily unavailable") from None
            repo.record_view(owner, recipe_id, at)
            return recipe
        return self._transaction(record)

    def history(self, owner: str) -> list[HistoryDTO]:
        identifier(owner)
        def read(session, repo):
            result = []
            for rid, at in repo.views(owner):
                # SQLite returns naive datetimes; stored instants are always UTC.
                at = at.replace(tzinfo=timezone.utc) if at.tzinfo is None else at.astimezone(timezone.utc)
                result.append(HistoryDTO(recipe=self._recipe(session, owner, rid),
                    lastViewedAt=at.isoformat(timespec="milliseconds").replace("+00:00", "Z")))
            return result
        return self._transaction(read)

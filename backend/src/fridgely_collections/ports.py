from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from sqlalchemy.orm import Session

from .schemas import RecipeDTO, identifier


@dataclass(frozen=True)
class AccountPrincipal:
    """Created by the host's verified-JWT dependency, never from request owner fields."""

    account_id: str

    def __post_init__(self):
        identifier(self.account_id)


@dataclass(frozen=True)
class OwnedRecipe:
    owner_id: str
    recipe: RecipeDTO


class CoreData(Protocol):
    """Read-only access to teammates' data using the caller's transaction/session.

    Implementations must scope queries to owner_id, avoid commit/rollback and
    return accepted, persisted recipes. They must not call AI or mutate inventory.
    """

    def recipe(self, session: Session, owner_id: str, recipe_id: str) -> OwnedRecipe | None: ...

    def inventory_names(self, session: Session, owner_id: str) -> Sequence[str]: ...


@dataclass(frozen=True)
class CoreCallbacks:
    """Small adapter for an existing backend; no imports of its global main.py."""

    recipe_lookup: Callable[[Session, str, str], OwnedRecipe | None]
    inventory_lookup: Callable[[Session, str], Sequence[str]]

    def recipe(self, session: Session, owner_id: str, recipe_id: str) -> OwnedRecipe | None:
        return self.recipe_lookup(session, owner_id, recipe_id)

    def inventory_names(self, session: Session, owner_id: str) -> Sequence[str]:
        return self.inventory_lookup(session, owner_id)

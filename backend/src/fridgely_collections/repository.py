from datetime import datetime
from uuid import uuid4

from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .models import Favorite, RecipeView, ShoppingItem
from .schemas import ShoppingItemDTO


def dialect_insert(session: Session, model):
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        return sqlite_insert(model)
    if dialect == "postgresql":
        return pg_insert(model)
    raise ValueError("Collections supports SQLite and PostgreSQL")


class CollectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_item(self, owner: str, name: str, key: str) -> tuple[ShoppingItemDTO, bool]:
        stmt = dialect_insert(self.session, ShoppingItem).values(
            id=uuid4().hex, owner_id=owner, name=name, name_key=key)
        created = self.session.execute(stmt.on_conflict_do_nothing(
            index_elements=[ShoppingItem.owner_id, ShoppingItem.name_key]
        ).returning(ShoppingItem.id)).scalar_one_or_none() is not None
        row = self.session.scalars(select(ShoppingItem).where(
            ShoppingItem.owner_id == owner, ShoppingItem.name_key == key)).one()
        return ShoppingItemDTO(id=row.id, name=row.name), created

    def items(self, owner: str) -> list[ShoppingItemDTO]:
        rows = self.session.scalars(select(ShoppingItem).where(
            ShoppingItem.owner_id == owner).order_by(ShoppingItem.id)).all()
        return [ShoppingItemDTO(id=row.id, name=row.name) for row in rows]

    def delete_item(self, owner: str, item_id: str) -> bool:
        return self.session.execute(delete(ShoppingItem).where(
            ShoppingItem.owner_id == owner, ShoppingItem.id == item_id)).rowcount == 1

    def save_favorite(self, owner: str, recipe_id: str) -> None:
        stmt = dialect_insert(self.session, Favorite).values(owner_id=owner, recipe_id=recipe_id)
        self.session.execute(stmt.on_conflict_do_nothing(
            index_elements=[Favorite.owner_id, Favorite.recipe_id]))

    def favorite_ids(self, owner: str) -> list[str]:
        return list(self.session.scalars(select(Favorite.recipe_id).where(
            Favorite.owner_id == owner).order_by(Favorite.recipe_id)))

    def delete_favorite(self, owner: str, recipe_id: str) -> bool:
        return self.session.execute(delete(Favorite).where(
            Favorite.owner_id == owner, Favorite.recipe_id == recipe_id)).rowcount == 1

    def record_view(self, owner: str, recipe_id: str, at: datetime) -> None:
        stmt = dialect_insert(self.session, RecipeView).values(
            owner_id=owner, recipe_id=recipe_id, last_viewed_at=at)
        # Preserve a newer view if concurrent/late requests have an older timestamp.
        self.session.execute(stmt.on_conflict_do_update(
            index_elements=[RecipeView.owner_id, RecipeView.recipe_id],
            set_={"last_viewed_at": case(
                (RecipeView.last_viewed_at < stmt.excluded.last_viewed_at, stmt.excluded.last_viewed_at),
                else_=RecipeView.last_viewed_at)},
        ))

    def views(self, owner: str) -> list[tuple[str, datetime]]:
        return list(self.session.execute(select(RecipeView.recipe_id, RecipeView.last_viewed_at)
            .where(RecipeView.owner_id == owner)
            .order_by(RecipeView.last_viewed_at.desc(), RecipeView.recipe_id.asc())).all())

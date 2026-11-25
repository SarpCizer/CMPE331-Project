from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, UniqueConstraint
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CollectionsBase(DeclarativeBase):
    """Only Sarp's three tables; does not create or modify the shared core schema."""


class ShoppingItem(CollectionsBase):
    __tablename__ = "shopping_items"
    __table_args__ = (
        UniqueConstraint("owner_id", "name_key", name="uq_shopping_owner_name"),
        CheckConstraint("length(name) > 0", name="ck_shopping_name"),
    )
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_key: Mapped[str] = mapped_column(String(512), nullable=False)


class Favorite(CollectionsBase):
    __tablename__ = "favorites"
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(128), primary_key=True)


class RecipeView(CollectionsBase):
    __tablename__ = "recipe_views"
    __table_args__ = (Index("ix_recipe_views_owner_recent", "owner_id", "last_viewed_at"),)
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def create_schema(engine: Engine) -> None:
    """Explicit local setup. Production migrations remain the DB owner's responsibility."""
    if engine.dialect.name not in {"sqlite", "postgresql"}:
        raise ValueError("Collections supports SQLite and PostgreSQL")
    CollectionsBase.metadata.create_all(engine)

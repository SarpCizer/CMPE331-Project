from typing import Callable

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, Text, UniqueConstraint, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload

from fridgely_collections.ports import OwnedRecipe
from fridgely_collections.schemas import RecipeDTO


class RecipeBase(DeclarativeBase):
    """Tables for the generated recipe aggregate. The host owns account migrations."""


class Recipe(RecipeBase):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_recipes_owner_id"),
        CheckConstraint("cooking_minutes > 0", name="ck_recipes_cooking_minutes"),
        CheckConstraint("calories_per_serving >= 0", name="ck_recipes_calories"),
        CheckConstraint("servings > 0", name="ck_recipes_servings"),
    )
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text)
    cooking_minutes: Mapped[float] = mapped_column(Float)
    calories_per_serving: Mapped[float] = mapped_column(Float)
    servings: Mapped[int]
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        order_by="RecipeIngredient.position", cascade="all, delete-orphan"
    )
    steps: Mapped[list["RecipeStep"]] = relationship(
        order_by="RecipeStep.position", cascade="all, delete-orphan"
    )


class RecipeIngredient(RecipeBase):
    __tablename__ = "recipe_ingredients"
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    name_key: Mapped[str] = mapped_column(Text)
    amount: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RecipeStep(RecipeBase):
    __tablename__ = "recipe_steps"
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(primary_key=True)
    instruction: Mapped[str] = mapped_column(Text)


def create_recipe_schema(engine: Engine) -> None:
    """Explicit setup for local/integration tests. Use reviewed migrations for deployment."""
    RecipeBase.metadata.create_all(engine)


class SqlRecipeStore:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def insert_batch(self, owner_id: str, recipes: list[RecipeDTO]) -> None:
        with self.session_factory() as session, session.begin():
            self.insert_in_session(session, owner_id, recipes)

    def insert_in_session(self, session, owner_id, recipes):
        for recipe in recipes:
            session.add(Recipe(
                id=recipe.id,
                owner_id=owner_id,
                title=recipe.title,
                cooking_minutes=recipe.cookingMinutes,
                calories_per_serving=recipe.caloriesPerServing,
                servings=recipe.servings,
                ingredients=[
                    RecipeIngredient(
                        position=i, name=name, name_key=name.casefold(),
                        amount=recipe.ingredientAmounts[i] if recipe.ingredientAmounts is not None else None,
                    )
                    for i, name in enumerate(recipe.ingredients)
                ],
                steps=[RecipeStep(position=i, instruction=step) for i, step in enumerate(recipe.steps)],
            ))

    def find_owned(self, session: Session, owner_id: str, recipe_id: str) -> OwnedRecipe | None:
        # Collections owns this session and performs the history/shopping commit.
        row = session.scalar(
            select(Recipe)
            .where(Recipe.owner_id == owner_id, Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients), selectinload(Recipe.steps))
        )
        if row is None:
            return None

        return self._owned(row)

    def list_owned(self, session, owner_id):
        rows = session.scalars(select(Recipe).where(Recipe.owner_id == owner_id)
            .options(selectinload(Recipe.ingredients), selectinload(Recipe.steps))
            .order_by(Recipe.title, Recipe.id).limit(100)).all()
        return [self._owned(row).recipe for row in rows]

    @staticmethod
    def _owned(row):
        amounts = [ingredient.amount for ingredient in row.ingredients]
        recipe = RecipeDTO(
            id=row.id,
            title=row.title,
            ingredients=[ingredient.name for ingredient in row.ingredients],
            ingredientAmounts=amounts if all(amount is not None for amount in amounts) else None,
            steps=[step.instruction for step in row.steps],
            cookingMinutes=row.cooking_minutes,
            caloriesPerServing=row.calories_per_serving,
            servings=row.servings,
        )
        return OwnedRecipe(row.owner_id, recipe)

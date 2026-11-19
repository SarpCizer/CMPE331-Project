from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import ForeignKey, Integer, JSON, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from fridgely_collections import (
    AccountPrincipal, CoreCallbacks, OwnedRecipe, RecipeDTO, create_app, create_schema,
)


class CoreBase(DeclarativeBase):
    """Test-only teammates' tables, not an implementation of their services."""


class AcceptedRecipe(CoreBase):
    __tablename__ = "test_accepted_recipes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)


class Ingredient(CoreBase):
    __tablename__ = "test_ingredients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)


class UserInventory(CoreBase):
    __tablename__ = "test_user_inventory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("test_ingredients.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    expiry_date: Mapped[str] = mapped_column(String)


def make_recipe(recipe_id="recipe-a", title="Rice meal", ingredients=None):
    return RecipeDTO(id=recipe_id, title=title, ingredients=ingredients or ["rice", "tomato", "onion"],
                     steps=["Combine ingredients", "Cook"], cookingMinutes=20,
                     caloriesPerServing=220, servings=2)


@dataclass
class TestClock:
    __test__ = False
    now: datetime = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


@pytest.fixture
def h(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path/'collections.db').as_posix()}",
                          connect_args={"check_same_thread": False, "timeout": 15})
    CoreBase.metadata.create_all(engine)
    create_schema(engine)
    sessions = sessionmaker(engine)
    recipes = [make_recipe(), make_recipe("recipe-b", "Soup", ["rice", "carrot"]),
               make_recipe("bob-recipe", "Bob's meal", ["pepper"])]
    with sessions.begin() as s:
        s.add_all([AcceptedRecipe(id=r.id, owner_id="2" if r.id=="bob-recipe" else "1",
                                 payload=r.model_dump()) for r in recipes])
        s.add_all([Ingredient(id=1, name=" RICE "), Ingredient(id=2, name="pepper")])
        s.add_all([UserInventory(id=1, user_id=1, ingredient_id=1, quantity=5, expiry_date="2030-01-01"),
                   UserInventory(id=2, user_id=2, ingredient_id=2, quantity=2, expiry_date="2030-02-01")])

    def recipe_lookup(session, owner_id, recipe_id):
        row = session.scalar(select(AcceptedRecipe).where(
            AcceptedRecipe.owner_id == owner_id, AcceptedRecipe.id == recipe_id))
        return None if row is None else OwnedRecipe(row.owner_id, RecipeDTO.model_validate(row.payload))

    def inventory_lookup(session, owner_id):
        return list(session.scalars(select(Ingredient.name).join(
            UserInventory, UserInventory.ingredient_id == Ingredient.id).where(
            UserInventory.user_id == int(owner_id))))

    # This is a test double for Berfin's verified-JWT dependency. It is not shipped
    # as an authentication implementation, and never trusts an owner header/body.
    def require_account(authorization: str | None = Header(default=None)):
        principal = {"Bearer alice-test": "1", "Bearer bob-test": "2"}.get(authorization)
        if principal is None:
            raise HTTPException(401, "TEST_SECRET must not be echoed",
                                headers={"WWW-Authenticate": "Bearer"})
        return AccountPrincipal(principal)

    clock = TestClock()
    core = CoreCallbacks(recipe_lookup, inventory_lookup)
    app = create_app(session_factory=sessions, core=core, require_account=require_account, clock=clock)
    def snapshot():
        with sessions() as s:
            return [tuple(row) for row in s.execute(select(UserInventory.id, UserInventory.user_id,
                UserInventory.ingredient_id, UserInventory.quantity, UserInventory.expiry_date))]
    with TestClient(app) as client:
        yield SimpleNamespace(engine=engine, sessions=sessions, core=core, clock=clock,
            app=app, client=client, alice={"Authorization": "Bearer alice-test"},
            bob={"Authorization": "Bearer bob-test"}, snapshot=snapshot,
            auth=require_account, recipes=recipes)
    engine.dispose()

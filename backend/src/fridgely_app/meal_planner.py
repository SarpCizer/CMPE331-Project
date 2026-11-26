"""Owned weekly slots and one aggregate, non-reserving shopping calculation."""
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path
from pydantic import Field, StringConstraints, field_validator
from sqlalchemy import Date, Integer, String, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.errors import CollectionError
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.repository import dialect_insert
from fridgely_collections.schemas import DTO, Identifier, RecipeDTO, ShoppingItemDTO, ingredient_name
from .availability import requirements_shopping_items
from .models import Account

Meal = Literal['breakfast', 'lunch', 'dinner']
_MEAL_ORDER = {'breakfast': 0, 'lunch': 1, 'dinner': 2}


class PlannerBase(DeclarativeBase):
    """The host's migration owns composite recipe FK and slot constraints."""


class WeeklyMeal(PlannerBase):
    __tablename__ = 'weekly_meals'
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    day: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal: Mapped[str] = mapped_column(String(12), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(128))


def monday(value):
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value or result.weekday() != 0:
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise CollectionError(400, 'Choose the Monday of the week in YYYY-MM-DD format.') from None


class WeekCommand(DTO):
    weekStart: Annotated[str, StringConstraints(strict=True, min_length=10, max_length=10)]

    @field_validator('weekStart')
    @classmethod
    def valid_week(cls, value):
        monday(value)
        return value


class SlotCommand(WeekCommand):
    recipeId: Identifier


class PlannedMeal(DTO):
    day: Annotated[int, Field(ge=0, le=6)]
    meal: Meal
    recipe: RecipeDTO


class WeekPlan(DTO):
    weekStart: str
    entries: list[PlannedMeal]


class WeeklyShopping(DTO):
    weekStart: str
    plannedMeals: int
    shopping: list[ShoppingItemDTO]
    needsReview: list[str]


def _entries(session, owner, week, recipe_lookup):
    rows = session.scalars(select(WeeklyMeal).where(
        WeeklyMeal.owner_id == owner, WeeklyMeal.week_start == week)).all()
    cache = {}
    entries = []
    for row in sorted(rows, key=lambda value: (value.day, _MEAL_ORDER[value.meal])):
        if row.recipe_id not in cache:
            cache[row.recipe_id] = recipe_lookup(session, owner, row.recipe_id)
        entries.append(PlannedMeal(day=row.day, meal=row.meal, recipe=cache[row.recipe_id]))
    return entries


def planner_router(require_account, transact, recipe_lookup, clock):
    router = APIRouter(route_class=CollectionsRoute, tags=['Weekly meal planner'])

    def week_date(value):
        today = clock().date()
        return monday(value) if value is not None else today - timedelta(days=today.weekday())

    def lock_owner(session, owner):
        session.scalar(select(Account.id).where(Account.id == owner).with_for_update())

    @router.get('/weekly-plan', response_model=WeekPlan)
    def load(weekStart: str | None = None, user: AccountPrincipal = Depends(require_account)):
        week = week_date(weekStart)
        return transact(lambda session, _repo: WeekPlan(
            weekStart=week.isoformat(), entries=_entries(session, user.account_id, week, recipe_lookup)))

    @router.put('/weekly-plan/{day}/{meal}', response_model=WeekPlan)
    def save(command: SlotCommand, day: Annotated[int, Path(ge=0, le=6)], meal: Meal,
             user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, monday(command.weekStart)
        def update_slot(session, _repo):
            lock_owner(session, owner)
            recipe_lookup(session, owner, command.recipeId)
            stmt = dialect_insert(session, WeeklyMeal).values(owner_id=owner, week_start=week,
                day=day, meal=meal, recipe_id=command.recipeId)
            session.execute(stmt.on_conflict_do_update(index_elements=['owner_id','week_start','day','meal'],
                set_={'recipe_id': command.recipeId}))
            return WeekPlan(weekStart=week.isoformat(), entries=_entries(session, owner, week, recipe_lookup))
        return transact(update_slot)

    @router.delete('/weekly-plan/{day}/{meal}', response_model=WeekPlan)
    def remove(day: Annotated[int, Path(ge=0, le=6)], meal: Meal, weekStart: str | None = None,
               user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, week_date(weekStart)
        def delete_slot(session, _repo):
            lock_owner(session, owner)
            removed = session.execute(delete(WeeklyMeal).where(WeeklyMeal.owner_id == owner,
                WeeklyMeal.week_start == week, WeeklyMeal.day == day, WeeklyMeal.meal == meal))
            if removed.rowcount != 1:
                raise CollectionError(404, 'Planned meal not found')
            return WeekPlan(weekStart=week.isoformat(), entries=_entries(session, owner, week, recipe_lookup))
        return transact(delete_slot)

    @router.post('/weekly-plan/shopping-items', response_model=WeeklyShopping,
                 summary='Aggregate the whole week and subtract current fridge stock once')
    def shopping(command: WeekCommand, user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, monday(command.weekStart)
        def add_week(session, repo):
            lock_owner(session, owner)
            entries = _entries(session, owner, week, recipe_lookup)
            if not entries:
                raise CollectionError(400, 'Choose at least one meal for this week first.')
            measurements = [(name, entry.recipe.ingredientAmounts[index] if entry.recipe.ingredientAmounts else None)
                for entry in entries for index, name in enumerate(entry.recipe.ingredients)]
            missing, review = requirements_shopping_items(session, owner, measurements)
            for item in missing:
                display, key = ingredient_name(item.name)
                repo.add_item(owner, display, key, item.quantity, item.unit, minimum=True)
            return WeeklyShopping(weekStart=week.isoformat(), plannedMeals=len(entries),
                shopping=repo.items(owner), needsReview=review)
        return transact(add_week)

    return router

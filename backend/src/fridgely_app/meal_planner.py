"""Owned weekly slots, requested dishes and portion-scaled shopping."""
from dataclasses import replace
from datetime import date, timedelta
from fractions import Fraction
from typing import Annotated
import unicodedata
from uuid import uuid4

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from pydantic import Field, StringConstraints, field_validator
from sqlalchemy import Date, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.concurrency import run_in_threadpool

from fridgely_collections.api import CollectionsRoute
from fridgely_collections.errors import CollectionError
from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.repository import dialect_insert
from fridgely_collections.schemas import DTO, Identifier, RecipeDTO, ShoppingItemDTO, ingredient_name
from fridgely_recipes.service import RecipeError, requested_recipe
from .availability import _measurement, _UNITS, requirements_shopping_items
from .models import Account

Meal = Annotated[str, StringConstraints(strict=True, pattern=r'^dish-(?:[1-9]|1[0-9]|20)$')]
Portions = Annotated[int, Field(ge=1, le=20)]


class PlannerBase(DeclarativeBase):
    """The host migration owns FK and slot constraints."""


class WeeklyMeal(PlannerBase):
    __tablename__ = 'weekly_meals'
    owner_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    day: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal: Mapped[str] = mapped_column(String(12), primary_key=True)
    recipe_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revision: Mapped[str] = mapped_column(String(32))


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
    servings: Portions | None = None


class DishCommand(WeekCommand):
    dish: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=120)]
    servings: Portions

    @field_validator('dish')
    @classmethod
    def visible_dish(cls, value):
        if any(unicodedata.category(char).startswith('C') for char in value):
            raise ValueError('Dish name must contain visible text')
        return value


def scaled_measurements(recipe, servings):
    result, display = [], []
    ratio = Fraction(servings, recipe.servings)
    for index, name in enumerate(recipe.ingredients):
        text = recipe.ingredientAmounts[index] if recipe.ingredientAmounts else None
        parsed = _measurement(text)
        if parsed is None:
            result.append((name, None)); display.append(None)
            continue
        dimension, amount, raw_unit = parsed
        amount = Fraction(amount) * ratio
        result.append((name, (dimension, amount)))
        number = amount / Fraction(_UNITS[raw_unit][1])
        unit = 'L' if raw_unit == 'l' else raw_unit
        display.append(f'{float(number):.6g} {unit}')
    return result, display


class PlannedMeal(DTO):
    day: Annotated[int, Field(ge=0, le=6)]
    meal: Meal
    servings: Portions
    recipe: RecipeDTO
    scaledAmounts: list[str | None]


class WeekPlan(DTO):
    weekStart: str
    entries: list[PlannedMeal]


class WeeklyShopping(DTO):
    weekStart: str
    plannedMeals: int
    shopping: list[ShoppingItemDTO]
    needsReview: list[str]


def _entries(session, owner, week, lookup):
    rows = session.scalars(select(WeeklyMeal).where(WeeklyMeal.owner_id == owner,
        WeeklyMeal.week_start == week, WeeklyMeal.recipe_id.is_not(None))).all()
    cache, entries = {}, []
    for row in sorted(rows, key=lambda value: (value.day, int(value.meal[5:]))):
        if row.recipe_id not in cache:
            cache[row.recipe_id] = lookup(session, owner, row.recipe_id)
        recipe = cache[row.recipe_id]
        entries.append(PlannedMeal(day=row.day, meal=row.meal, servings=row.servings,
            recipe=recipe, scaledAmounts=scaled_measurements(recipe, row.servings)[1]))
    return entries


def _slot_query(owner, week, day, meal):
    return select(WeeklyMeal).where(WeeklyMeal.owner_id == owner, WeeklyMeal.week_start == week,
        WeeklyMeal.day == day, WeeklyMeal.meal == meal)


def _save_slot(session, owner, week, day, meal, recipe_id, servings):
    if not 1 <= servings <= 20:
        raise CollectionError(400, 'Choose between 1 and 20 portions for this dish.')
    stmt = dialect_insert(session, WeeklyMeal).values(owner_id=owner, week_start=week,
        day=day, meal=meal, recipe_id=recipe_id, servings=servings, revision=uuid4().hex)
    session.execute(stmt.on_conflict_do_update(index_elements=['owner_id','week_start','day','meal'],
        set_={'recipe_id':recipe_id,'servings':servings,'revision':stmt.excluded.revision}))


def planner_router(require_account, transact, recipe_lookup, clock, store, generation):
    router = APIRouter(route_class=CollectionsRoute, tags=['Weekly meal planner'])

    def week_date(value):
        today = clock().date()
        return monday(value) if value is not None else today - timedelta(days=today.weekday())

    def lock_owner(session, owner):
        session.scalar(select(Account.id).where(Account.id == owner).with_for_update())

    def rendered(session, owner, week):
        return WeekPlan(weekStart=week.isoformat(), entries=_entries(session, owner, week, recipe_lookup))

    @router.get('/weekly-plan', response_model=WeekPlan)
    def load(weekStart: str | None = None, user: AccountPrincipal = Depends(require_account)):
        week = week_date(weekStart)
        return transact(lambda session, _repo: rendered(session, user.account_id, week))

    @router.get('/weekly-plan/recipes', response_model=list[RecipeDTO])
    def saved(user: AccountPrincipal = Depends(require_account)):
        return transact(lambda session, _repo: store.list_owned(session, user.account_id))

    @router.put('/weekly-plan/{day}/{meal}', response_model=WeekPlan)
    def save(command: SlotCommand, day: Annotated[int, Path(ge=0, le=6)], meal: Meal,
             user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, monday(command.weekStart)
        def update_slot(session, _repo):
            lock_owner(session, owner)
            recipe = recipe_lookup(session, owner, command.recipeId)
            _save_slot(session, owner, week, day, meal, recipe.id, command.servings or recipe.servings)
            return rendered(session, owner, week)
        return transact(update_slot)

    @router.delete('/weekly-plan/{day}/{meal}', response_model=WeekPlan)
    def remove(day: Annotated[int, Path(ge=0, le=6)], meal: Meal, weekStart: str | None = None,
               user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, week_date(weekStart)
        def delete_slot(session, _repo):
            lock_owner(session, owner)
            row = session.scalar(_slot_query(owner, week, day, meal))
            if row is None or row.recipe_id is None:
                raise CollectionError(404, 'Planned meal not found')
            # A revisioned empty slot prevents a late AI result resurrecting it.
            row.recipe_id, row.servings, row.revision = None, None, uuid4().hex
            session.flush()
            return rendered(session, owner, week)
        return transact(delete_slot)

    @router.post('/weekly-plan/{day}/{meal}/generate', response_model=WeekPlan)
    async def create_dish(command: DishCommand, day: Annotated[int, Path(ge=0, le=6)], meal: Meal,
                          user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, monday(command.weekStart)
        def revision(session, _repo):
            row = session.scalar(_slot_query(owner, week, day, meal))
            return row.revision if row is not None else None
        prior = await run_in_threadpool(transact, revision)
        try:
            data = await run_in_threadpool(generation.read_input, owner)
            data = replace(data, requested_dish=command.dish, requested_servings=command.servings)
            recipe = await requested_recipe(data, generation.provider, generation.timeout_seconds)
        except RecipeError as error:
            return JSONResponse({'error':str(error), **({'retryable':True} if error.retryable else {})}, status_code=error.status)
        def commit_dish(session, _repo):
            lock_owner(session, owner)
            if revision(session, _repo) != prior:
                raise CollectionError(409, 'This meal changed while its recipe was being created. Refresh the week and try again.')
            store.insert_in_session(session, owner, [recipe])
            session.flush()
            _save_slot(session, owner, week, day, meal, recipe.id, command.servings)
            return rendered(session, owner, week)
        return await run_in_threadpool(transact, commit_dish)

    @router.post('/weekly-plan/shopping-items', response_model=WeeklyShopping,
                 summary='Scale every planned dish, aggregate the week and subtract stock once')
    def shopping(command: WeekCommand, user: AccountPrincipal = Depends(require_account)):
        owner, week = user.account_id, monday(command.weekStart)
        def add_week(session, repo):
            lock_owner(session, owner)
            entries = _entries(session, owner, week, recipe_lookup)
            if not entries:
                raise CollectionError(400, 'Choose at least one meal for this week first.')
            measurements = [measurement for entry in entries
                for measurement in scaled_measurements(entry.recipe, entry.servings)[0]]
            missing, review = requirements_shopping_items(session, owner, measurements, round_for_purchase=True)
            for item in missing:
                display, key = ingredient_name(item.name)
                repo.add_item(owner, display, key, item.quantity, item.unit, minimum=True)
            return WeeklyShopping(weekStart=week.isoformat(), plannedMeals=len(entries),
                shopping=repo.items(owner), needsReview=review)
        return transact(add_week)
    return router

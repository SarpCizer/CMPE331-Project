from dataclasses import dataclass
from typing import Annotated, Callable, Sequence

from fastapi import APIRouter, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from fridgely_collections.ports import AccountPrincipal
from fridgely_collections.schemas import EmptyCommand, RecipeDTO

from .service import GenerationInput, MAX_PROVIDER_SECONDS, RecipeError, RecipeGenerationService, RecipeProvider
from .storage import SqlRecipeStore


class RecipeRoute(APIRoute):
    def get_route_handler(self):
        handle = super().get_route_handler()

        async def protected_handler(request):
            try:
                return await handle(request)
            except RequestValidationError:
                return JSONResponse({"error": "Invalid request"}, status_code=400)
            except RecipeError as error:
                body = {"error": str(error)}
                if error.retryable:
                    body["retryable"] = True
                return JSONResponse(body, status_code=error.status)
            except HTTPException as error:
                message = "Authentication required" if error.status_code == 401 else "Request denied"
                return JSONResponse({"error": message}, status_code=error.status_code, headers=error.headers)
            except SQLAlchemyError:
                return JSONResponse({"error": "Storage temporarily unavailable"}, status_code=503)
            except Exception:
                return JSONResponse({"error": "Internal server error"}, status_code=500)

        return protected_handler


@dataclass(frozen=True)
class RecipesModule:
    router: APIRouter
    store: SqlRecipeStore


def build_recipes(
    *,
    session_factory: Callable[[], Session],
    require_account: Callable,
    inventory_lookup: Callable[[Session, str], Sequence[str]],
    preferences_lookup: Callable[[Session, str], tuple[Sequence[str], Sequence[str]]],
    provider: RecipeProvider,
    timeout_seconds: float = MAX_PROVIDER_SECONDS,
    amounts_lookup: Callable | None = None,
) -> RecipesModule:
    """Build the recipe module using the verified account and core readers from the host."""
    store = SqlRecipeStore(session_factory)

    def read_input(owner_id: str) -> GenerationInput:
        with session_factory() as session:
            if session.get_bind().dialect.name == "postgresql":
                session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
            ingredients = tuple(inventory_lookup(session, owner_id))
            dietary, allergens = preferences_lookup(session, owner_id)
            amounts = tuple(amounts_lookup(session, owner_id)) if amounts_lookup else ()
            return GenerationInput(ingredients, tuple(dietary), tuple(allergens), amounts)

    service = RecipeGenerationService(read_input, provider, store.insert_batch, timeout_seconds)
    router = APIRouter(route_class=RecipeRoute, tags=["Recipe generation"])

    @router.post("/recipes/generate", response_model=list[RecipeDTO])
    async def generate(
        principal: Annotated[AccountPrincipal, Depends(require_account)],
        command: EmptyCommand | None = None,
    ):
        if not isinstance(principal, AccountPrincipal):
            raise RecipeError(503, "Authentication integration must return AccountPrincipal.")
        return await service.generate(principal.account_id)

    return RecipesModule(router, store)

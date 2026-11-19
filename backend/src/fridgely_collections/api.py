from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from fastapi import APIRouter, Body, Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from .errors import CollectionError
from .ports import AccountPrincipal, CoreData
from .schemas import EmptyCommand, FavoriteCommand, HistoryDTO, RecipeDTO, ShoppingCommand, ShoppingItemDTO
from .service import CollectionsService, utc_now


class CollectionsRoute(APIRoute):
    """Keep the approved error envelope local to this module's routes."""

    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError:
                return JSONResponse(status_code=400, content={"error": "Invalid request"})
            except CollectionError as error:
                return JSONResponse(status_code=error.status, content={"error": error.message})
            except HTTPException as error:
                # Preserve the host's auth status/headers without echoing its internal detail.
                message = "Authentication required" if error.status_code == 401 else "Request denied"
                return JSONResponse(status_code=error.status_code,
                    content={"error": message}, headers=error.headers)
            except SQLAlchemyError:
                return JSONResponse(status_code=503, content={"error": "Storage temporarily unavailable"})
            except Exception:
                return JSONResponse(status_code=500, content={"error": "Internal server error"})
        return handler


@dataclass(frozen=True)
class CollectionsModule:
    router: APIRouter
    service: CollectionsService


def build_collections(*, session_factory: Callable[[], Session], core: CoreData,
                      require_account: Callable, clock: Callable[[], datetime] = utc_now,
                      include_recipe_details: bool = True) -> CollectionsModule:
    """Mountable feature module. Authentication/core data have no insecure defaults."""
    if not callable(require_account):
        raise TypeError("A verified-account dependency is required")
    service = CollectionsService(session_factory, core, clock)
    router = APIRouter(route_class=CollectionsRoute, tags=["Sarp - personal collections"])

    def owner(principal: AccountPrincipal = Depends(require_account)) -> str:
        if not isinstance(principal, AccountPrincipal):
            raise CollectionError(503, "Authentication integration must return AccountPrincipal")
        return principal.account_id

    @router.get("/shopping-items", response_model=list[ShoppingItemDTO])
    def items(account: str = Depends(owner)):
        return service.items(account)

    @router.post("/shopping-items", response_model=ShoppingItemDTO, status_code=201,
                 responses={200: {"model": ShoppingItemDTO}})
    def add_item(command: ShoppingCommand, response: Response, account: str = Depends(owner)):
        item, created = service.add_item(account, command.name)
        response.status_code = 201 if created else 200
        return item

    @router.delete("/shopping-items/{item_id}", status_code=204)
    def delete_item(item_id: str, account: str = Depends(owner)):
        service.delete_item(account, item_id)
        return Response(status_code=204)

    @router.post("/recipes/{recipe_id}/shopping-items", response_model=list[ShoppingItemDTO])
    def add_missing(recipe_id: str, command: EmptyCommand | None = Body(default=None),
                    account: str = Depends(owner)):
        return service.add_missing(account, recipe_id)

    @router.post("/favorites", response_model=RecipeDTO)
    def save_favorite(command: FavoriteCommand, account: str = Depends(owner)):
        return service.save_favorite(account, command.recipeId)

    @router.get("/favorites", response_model=list[RecipeDTO])
    def favorites(account: str = Depends(owner)):
        return service.favorites(account)

    @router.delete("/favorites/{recipe_id}", status_code=204)
    def delete_favorite(recipe_id: str, account: str = Depends(owner)):
        service.delete_favorite(account, recipe_id)
        return Response(status_code=204)

    @router.get("/history", response_model=list[HistoryDTO])
    def history(account: str = Depends(owner)):
        return service.history(account)

    if include_recipe_details:
        @router.get("/recipes/{recipe_id}", response_model=RecipeDTO)
        def details(recipe_id: str, account: str = Depends(owner)):
            return service.open_recipe(account, recipe_id)

    return CollectionsModule(router, service)


def create_app(**dependencies) -> FastAPI:
    """Optional host for this feature; deliberately has no auth/inventory/AI routes."""
    module = build_collections(**dependencies)
    app = FastAPI(title="Fridgely - personal collections")
    app.include_router(module.router)
    app.state.collections = module.service
    return app

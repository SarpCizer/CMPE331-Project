"""Compose the existing feature routers with real accounts and SQL data."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from fridgely_collections import CoreCallbacks, build_collections
from fridgely_recipes.api import build_recipes
from fridgely_recipes.provider import configured_recipe_provider
from .availability import inventory_for_recipe, recipe_shopping_items
from .core import create_core_app, inventory_names, inventory_amounts, preference_lists
from .documentation import install_documentation
from .security import utc_now
from .cooking import cooking_router
from .purchases import purchase_router


def create_app(*, database_url=None, jwt_secret=None, clock=utc_now, recipe_provider=None,
               provider_timeout=28, token_lifetime=3600, frontend_dir=None):
    api = create_core_app(
        database_url=database_url or os.getenv('DATABASE_URL','sqlite:///./fridgely.db'),
        jwt_secret=jwt_secret if jwt_secret is not None else os.getenv('JWT_SECRET',''),
        clock=clock, token_lifetime=token_lifetime)
    wire = httpx.AsyncClient(timeout=httpx.Timeout(28, connect=5), follow_redirects=False)
    provider = recipe_provider
    if provider is None:
        provider = configured_recipe_provider(wire)
    recipes = build_recipes(session_factory=api.state.sessions,
        require_account=api.state.authentication.require_account,
        inventory_lookup=inventory_names, preferences_lookup=preference_lists,
        provider=provider, timeout_seconds=provider_timeout, amounts_lookup=inventory_amounts)
    collections = build_collections(session_factory=api.state.sessions,
        require_account=api.state.authentication.require_account,
        core=CoreCallbacks(recipes.store.find_owned, inventory_names, inventory_for_recipe, recipe_shopping_items), clock=clock)
    api.include_router(recipes.router)
    api.include_router(collections.router)
    api.include_router(purchase_router(api.state.sessions, api.state.authentication.require_account, clock))
    api.include_router(cooking_router(api.state.sessions, api.state.authentication.require_account, recipes.store))

    @asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            await wire.aclose()
            api.state.engine.dispose()

    app = FastAPI(title='Fridgely', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.engine, app.state.sessions = api.state.engine, api.state.sessions
    app.state.authentication = api.state.authentication

    @app.middleware('http')
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if request.url.path.rstrip('/') in {'/docs','/api/docs'}:
            # Swagger UI sets element styles; scripts remain limited to our origin.
            response.headers['Content-Security-Policy'] = response.headers['Content-Security-Policy'].replace(
                "style-src 'self'", "style-src 'self' 'unsafe-inline'")
        return response

    built = Path(frontend_dir or os.getenv('FRONTEND_DIST',
        str(Path(__file__).resolve().parents[3] / 'frontend' / 'dist')))
    install_documentation(api, built)
    if (built / 'index.html').is_file():
        if (built / 'assets').is_dir():
            api.mount('/assets', StaticFiles(directory=built / 'assets'), name='assets')

        @api.get('/{path:path}', include_in_schema=False)
        def frontend(path: str):
            if path not in {'','fridge','recipes','shopping','favorites','history','preferences'}:
                return JSONResponse({'error':'Not found'},status_code=404)
            return FileResponse(built / 'index.html')

    # Same HTTP application is available at the approved root contract and /api.
    # The browser uses /api, allowing the production build and API to share an origin.
    app.mount('/api', api)
    app.mount('/', api)
    return app

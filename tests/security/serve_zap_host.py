"""Instrumented disposable host used only by the authenticated ZAP job."""
from contextlib import asynccontextmanager
import os
from pathlib import Path
import secrets
import sys
import tempfile

from fastapi import FastAPI
import uvicorn

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend/tests'))
from serve_web_test import FixtureProvider


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='fridgely-zap-') as directory:
        url = os.getenv('TEST_DATABASE_URL', f'sqlite:///{Path(directory) / "scan.db"}')
        engine = make_engine(url)
        migrate(engine)
        engine.dispose()
        application = create_app(database_url=url, jwt_secret=secrets.token_hex(32),
            recipe_provider=FixtureProvider(), frontend_dir=directory)
        counts = {'authenticated_successful_requests': 0, 'total_requests': 0}

        @asynccontextmanager
        async def lifespan(_app):
            async with application.router.lifespan_context(application):
                yield

        host = FastAPI(lifespan=lifespan, docs_url=None, openapi_url=None)

        @host.middleware('http')
        async def observed(request, call_next):
            response = await call_next(request)
            if not request.url.path.startswith('/__security_probe__'):
                counts['total_requests'] += 1
                if (request.url.path.startswith('/api/') and request.headers.get('Authorization', '').startswith('Bearer ')
                        and request.url.path not in {'/api/accounts', '/api/sessions', '/api/health'} and response.status_code < 300):
                    counts['authenticated_successful_requests'] += 1
            return response

        @host.get('/__security_probe__/metrics', include_in_schema=False)
        async def metrics():
            return {**counts, 'environment': 'disposable-zap-fixture'}

        host.mount('/', application)
        uvicorn.run(host, host='127.0.0.1', port=int(os.getenv('FRIDGELY_TEST_PORT', '8094')), access_log=False)

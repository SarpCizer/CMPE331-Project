from pathlib import Path

from fastapi.testclient import TestClient

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app


def test_openapi_describes_real_routes_authentication_and_errors(tmp_path):
    url = f'sqlite:///{tmp_path / "docs.db"}'
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    app = create_app(database_url=url, jwt_secret='documentation-test-signing-key-at-least-32-bytes',
        frontend_dir=tmp_path)
    with TestClient(app) as client:
        schema = client.get('/api/openapi.json').json()
        assert schema == client.get('/openapi.json').json()
        assert schema['info']['title'] == 'Fridgely API'
        assert schema['servers'] == [{'url':'/api'}]
        assert set(schema['paths']) == {'/accounts','/sessions','/profile/preferences','/inventory',
            '/inventory/{item_id}','/health','/recipes/generate','/recipes/{recipe_id}',
            '/recipes/{recipe_id}/shopping-items','/shopping-items','/shopping-items/{item_id}',
            '/favorites','/favorites/{recipe_id}','/history'}
        bearer = schema['components']['securitySchemes']['BearerAuth']
        assert bearer == {'type':'http','scheme':'bearer','bearerFormat':'JWT'}
        inventory = schema['paths']['/inventory']['get']
        assert inventory['security'] == [{'BearerAuth':[]}]
        assert inventory['responses']['200']['content']['application/json']['schema']['items']['$ref'].endswith('InventoryDTO')
        assert '401' in inventory['responses'] and '422' not in inventory['responses']
        assert '409' in schema['paths']['/accounts']['post']['responses']
        generation = schema['paths']['/recipes/generate']['post']['responses']
        assert {'400','401','422','502','503'} <= generation.keys()
        assert client.get('/api/docs').status_code == 503


def test_documentation_serves_only_local_assets_and_does_not_persist_tokens(tmp_path):
    (tmp_path / 'api-docs').mkdir()
    (tmp_path / 'api-docs' / 'swagger-ui.css').write_text('body {margin: 0}')
    app = create_app(database_url=f'sqlite:///{tmp_path / "assets.db"}',
        jwt_secret='documentation-test-signing-key-at-least-32-bytes',frontend_dir=tmp_path)
    with TestClient(app) as client:
        response = client.get('/api/docs')
        assert response.status_code == 200
        assert 'https://' not in response.text
        assert "script-src 'self';" in response.headers['content-security-policy']
        assert 'unsafe-inline' not in client.get('/api/openapi.json').headers['content-security-policy']
        assert 'persistAuthorization: false' in client.get('/api/docs/init.js').text
        assert client.get('/api/docs/assets/swagger-ui.css').status_code == 200

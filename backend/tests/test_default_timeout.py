import asyncio
import json
from pathlib import Path
import time

from fastapi.testclient import TestClient

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app


def test_production_timeout_cancels_stalled_provider_within_thirty_seconds(tmp_path):
    state={'cancelled':False}
    class StalledProvider:
        async def generate(self,_data):
            try:
                await asyncio.sleep(60)
            finally:
                state['cancelled']=True
    url=f'sqlite:///{tmp_path / "timeout.db"}'
    engine=make_engine(url);migrate(engine);engine.dispose()
    app=create_app(database_url=url,jwt_secret='test-only-timeout-signing-secret-at-least-32-bytes',
        recipe_provider=StalledProvider())
    with TestClient(app) as client:
        credentials={'email':'timeout@example.test','password':'Timeout-fixture-password!'}
        assert client.post('/accounts',json=credentials).status_code==201
        signed=client.post('/sessions',json=credentials)
        assert signed.status_code==200
        headers={'Authorization':f'Bearer {signed.json()["token"]}'}
        assert client.post('/inventory',headers=headers,json={'name':'rice'}).status_code==201
        paths=['/inventory','/profile/preferences','/shopping-items','/favorites','/history']
        before=[client.get(path,headers=headers).json() for path in paths]
        start=time.perf_counter()
        response=client.post('/recipes/generate',headers=headers,json={})
        elapsed=time.perf_counter()-start
        assert response.status_code==503 and response.json()['retryable'] is True
        assert elapsed<30 and state['cancelled']
        assert [client.get(path,headers=headers).json() for path in paths]==before
    destination=Path('test-results/provider-timeout.json');destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps({'configured_seconds':28,'observed_seconds':elapsed,
        'provider_cancelled':state['cancelled'],'five_collections_unchanged':True,'passed':True},indent=2)+'\n')

"""Two-process persistence probe against the real application and selected SQL engine."""
import json
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app

PATHS=['/inventory','/profile/preferences','/shopping-items','/favorites','/history']
PASSWORD='Persistence-fixture-password!'


class Provider:
    async def generate(self,_data):
        return [{'title':'Rice meal','ingredients':['rice','tomato'],
            'steps':['Cook rice','Add tomato'],'cookingMinutes':20,'caloriesPerServing':300,'servings':2}]


def main():
    phase,destination,run_id=sys.argv[1:]
    url=os.environ['PROBE_DATABASE_URL']
    engine=make_engine(url)
    migrate(engine)
    engine.dispose()
    app=create_app(database_url=url,jwt_secret='test-only-persistence-signing-secret-32-bytes',recipe_provider=Provider())
    state={}
    with TestClient(app) as client:
        for name in ['alice','bob']:
            credentials={'email':f'{name}-{run_id}@example.test','password':PASSWORD}
            if phase=='write':
                assert client.post('/accounts',json=credentials).status_code==201
            response=client.post('/sessions',json=credentials)
            assert response.status_code==200
            headers={'Authorization':f'Bearer {response.json()["token"]}'}
            if phase=='write':
                assert client.post('/inventory',headers=headers,json={'name':f'{name}-rice'}).status_code==201
                assert client.put('/profile/preferences',headers=headers,json={'dietary':[name],'allergens':['peanut']}).status_code==200
                generated=client.post('/recipes/generate',headers=headers,json={})
                assert generated.status_code==200
                recipe=generated.json()[0]
                assert client.get(f'/recipes/{recipe["id"]}',headers=headers).status_code==200
                assert client.post('/favorites',headers=headers,json={'recipeId':recipe['id']}).status_code==200
                assert client.post('/shopping-items',headers=headers,json={'name':f'{name}-onion'}).status_code==201
            snapshot=[]
            for path in PATHS:
                response=client.get(path,headers=headers)
                assert response.status_code==200
                snapshot.append(response.json())
            state[name]=snapshot
            other='bob' if name=='alice' else 'alice'
            assert all(other not in item['name'] for item in snapshot[0])
        if phase=='write':
            Path(destination).write_text(json.dumps(state))
        else:
            assert state==json.loads(Path(destination).read_text())
    print(json.dumps({'phase':phase,'passed':True,'pid':os.getpid(),'accounts':2,'collections_per_account':5}))


if __name__=='__main__':
    main()

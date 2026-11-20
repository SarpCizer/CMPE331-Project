"""Isolated browser/load-test host: real app/SQL, controlled external provider."""
from pathlib import Path
import os
import secrets
import tempfile

import uvicorn

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app


class FixtureProvider:
    async def generate(self,data):
        if 'provider-failure' in data.ingredients:
            raise RuntimeError('Controlled provider outage')
        return [
            {'title':'Tomato rice','ingredients':['rice','tomato','onion'],
             'steps':['Cook the rice.','Simmer tomato and onion.','Combine and serve.'],
             'cookingMinutes':25,'caloriesPerServing':320,'servings':2},
            {'title':'Tomato salad','ingredients':['tomato','olive oil'],
             'steps':['Slice the tomato.','Dress with olive oil.'],
             'cookingMinutes':5,'caloriesPerServing':120,'servings':1},
        ]


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='fridgely-web-test-') as directory:
        url=os.getenv('TEST_DATABASE_URL',f'sqlite:///{Path(directory) / "web.db"}')
        engine=make_engine(url)
        migrate(engine)
        engine.dispose()
        app=create_app(database_url=url,jwt_secret=secrets.token_hex(32),recipe_provider=FixtureProvider())
        uvicorn.run(app,host='127.0.0.1',port=int(os.getenv('FRIDGELY_TEST_PORT','8000')),access_log=False)

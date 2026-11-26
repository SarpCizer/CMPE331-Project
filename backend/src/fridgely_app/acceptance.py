"""Test-only JSON-lines bridge to the actual FastAPI host and SQL database.

Only provider output and the clock are controlled by the existing Node fixtures.
No fake implementation of accounts, routing, authorization or persistence exists.
"""
import asyncio
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import secrets
import sys
import tempfile

from fastapi.testclient import TestClient

from .database import make_engine, migrate
from .host import create_app


def emit(value):
    print(json.dumps(value), flush=True)


class NodeProvider:
    async def generate(self, data):
        emit({'kind':'provider', 'input':{key:value for key,value in asdict(data).items()
            if value is not None or (key != 'mood' and not key.startswith('requested_'))}})
        message = json.loads(await asyncio.to_thread(sys.stdin.readline))
        if message.get('kind') != 'provider-result' or not message.get('ok'):
            raise RuntimeError('Controlled provider failure')
        return message.get('value')


def main():
    with tempfile.TemporaryDirectory(prefix='fridgely-acceptance-') as directory:
        url = f'sqlite:///{Path(directory) / "acceptance.db"}'
        engine = make_engine(url)
        migrate(engine)
        engine.dispose()
        state = {'now':datetime.fromisoformat('2026-11-20T12:00:00+00:00')}
        app = create_app(database_url=url, jwt_secret=secrets.token_hex(32),
            clock=lambda:state['now'], recipe_provider=NodeProvider())
        with TestClient(app) as client:
            emit({'kind':'ready'})
            for line in sys.stdin:
                message = json.loads(line)
                if message.get('kind') == 'close':
                    break
                state['now'] = datetime.fromisoformat(message['now'].replace('Z','+00:00'))
                request = message['request']
                headers = {'Authorization':f'Bearer {request["token"]}'} if request.get('token') else {}
                options = {'json':request['body']} if 'body' in request else {}
                response = client.request(request['method'], request['path'], headers=headers, **options)
                emit({'kind':'response','id':message['id'],'status':response.status_code,
                    'body':response.json() if response.content else None})


if __name__ == '__main__':
    main()

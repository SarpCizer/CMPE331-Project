"""Real HTTP concurrency with controlled inference; never contacts a model service."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
import platform
from pathlib import Path
import secrets
import socket
import tempfile
import time
import sys

import httpx
import uvicorn
from sqlalchemy import func, select

from fridgely_app.database import make_engine, migrate
from fridgely_app.host import create_app
from fridgely_recipes.storage import Recipe
from non_ai_http import statistics
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'helpers'))
from measured_source import verified_revision


class ControlledProvider:
    def __init__(self):
        self.timeout_mode, self.calls, self.cancelled = False, 0, 0

    async def generate(self, _data):
        self.calls += 1
        try:
            await asyncio.sleep(60 if self.timeout_mode else .2)
        except asyncio.CancelledError:
            self.cancelled += 1
            raise
        return [{'title': 'Controlled banana shake', 'ingredients': ['banana', 'milk', 'sugar'],
            'ingredientAmounts': ['2 pcs', '200 ml', '20 g'], 'steps': ['Blend.'],
            'cookingMinutes': 3, 'caloriesPerServing': 100, 'servings': 1}]


async def measure(args, directory):
    started_utc = datetime.now(timezone.utc).isoformat()
    url = os.getenv('TEST_DATABASE_URL', f'sqlite:///{Path(directory) / "generation.db"}')
    engine = make_engine(url)
    migrate(engine)
    engine.dispose()
    provider = ControlledProvider()
    app = create_app(database_url=url, jwt_secret=secrets.token_hex(32), recipe_provider=provider,
                     frontend_dir=directory)
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port,
        log_level='error', access_log=False))
    running = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(600):
            if server.started:
                break
            if running.done():
                await running
                raise RuntimeError('Isolated host did not start')
            await asyncio.sleep(.05)
        if not server.started:
            raise RuntimeError('Isolated host startup timed out')
        async with httpx.AsyncClient(base_url=f'http://127.0.0.1:{port}', timeout=35,
                                      trust_env=False, follow_redirects=False) as client:
            password, suffix = secrets.token_urlsafe(28), secrets.token_hex(8)
            users, owners = [], []
            for number in range(args.users):
                credentials = {'email': f'generation-load-{suffix}-{number}@example.test', 'password': password}
                response = await client.post('/accounts', json=credentials)
                response.raise_for_status()
                owners.append(response.json()['id'])
                session = await client.post('/sessions', json=credentials)
                session.raise_for_status()
                headers = {'Authorization': 'Bearer ' + session.json()['token']}
                for name, quantity, unit in [('banana', 2, 'pcs'), ('milk', 200, 'ml'), ('sugar', 20, 'g')]:
                    added = await client.post('/inventory', headers=headers, json={'name': name, 'quantity': quantity, 'unit': unit})
                    added.raise_for_status()
                inventory = await client.get('/inventory', headers=headers)
                users.append((headers, inventory.json()))
            samples, malformed = [], []
            start = time.perf_counter()
            deadline = start + args.duration

            async def user(headers):
                while time.perf_counter() < deadline:
                    before = time.perf_counter()
                    try:
                        response = await client.post('/recipes/generate', headers=headers, json={'mood': 'quick'})
                        status = response.status_code
                        if status == 200:
                            body = response.json()
                            if not isinstance(body, list) or len(body) != 1 or not body[0].get('id'):
                                malformed.append(True)
                    except httpx.HTTPError:
                        status = 0
                    samples.append(((time.perf_counter() - before) * 1000, status))
                    await asyncio.sleep(1)

            await asyncio.gather(*(user(headers) for headers, _stock in users))
            elapsed = time.perf_counter() - start
            steady = statistics(samples)
            unchanged = all([(await client.get('/inventory', headers=headers)).json() == stock for headers, stock in users])
            with app.state.sessions() as session:
                saved_before_timeout = session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id.in_(owners)))
            provider.timeout_mode = True
            timeout_results = []
            cancellations_before = provider.cancelled

            async def stalled(headers):
                before = time.perf_counter()
                response = await client.post('/recipes/generate', headers=headers, json={})
                duration = time.perf_counter() - before
                timeout_results.append({'status': response.status_code, 'seconds': duration,
                    'retryable': response.json().get('retryable') is True})

            await asyncio.gather(*(stalled(headers) for headers, _ in users[:args.timeout_users]))
            timeout_passed = all(row['status'] == 503 and row['retryable'] and row['seconds'] <= 30 for row in timeout_results)
            cancelled = provider.cancelled - cancellations_before
            unchanged_after_timeout = all([(await client.get('/inventory', headers=headers)).json() == stock for headers, stock in users])
            with app.state.sessions() as session:
                saved_after_timeout = session.scalar(select(func.count()).select_from(Recipe).where(Recipe.owner_id.in_(owners)))
            persisted = saved_before_timeout == steady['requests'] - steady['errors'] and saved_after_timeout == saved_before_timeout
            passed = steady['p95_ms'] <= 2000 and steady['error_rate'] < .01 and not malformed and unchanged and timeout_passed and cancelled == args.timeout_users and unchanged_after_timeout and persisted
            result = {'revision': args.revision, 'started_utc': started_utc,
                'completed_utc': datetime.now(timezone.utc).isoformat(),
                'client': {'system': platform.system(), 'architecture': platform.machine(),
                    'python': platform.python_version(), 'cpu_count': os.cpu_count()},
                'environment': args.environment, 'database': 'PostgreSQL' if url.startswith('postgres') else 'SQLite',
                'scenario': {'users': args.users, 'configured_seconds': args.duration, 'measured_seconds': elapsed,
                    'think_seconds': 1, 'provider': 'controlled 200 ms response; no external inference',
                    'requests_use_real_http_host': True},
                'steady': steady, 'steady_thresholds': {'p95_ms_max': 2000, 'error_rate_exclusive_max': .01},
                'concurrent_timeouts': {'users': args.timeout_users, 'deadline_seconds': 28,
                    'maximum_seconds': 30, 'results': timeout_results, 'provider_cancellations': cancelled,
                    'passed': timeout_passed and cancelled == args.timeout_users},
                'inventory_unchanged': unchanged and unchanged_after_timeout,
                'successful_recipes_persisted': saved_before_timeout, 'no_partial_recipe_on_timeout': persisted,
                'malformed_success_responses': len(malformed), 'external_model_calls': 0, 'passed': passed}
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'passed': passed, 'requests': steady['requests'], 'p95_ms': steady['p95_ms'],
                              'concurrent_timeouts_passed': result['concurrent_timeouts']['passed']}))
            return passed
    finally:
        server.should_exit = True
        await running
        sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', type=int, default=10)
    parser.add_argument('--duration', type=int, default=60)
    parser.add_argument('--timeout-users', type=int, default=5)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--environment', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    args.revision = verified_revision(Path(__file__).resolve().parents[2], args.revision)
    if not (1 <= args.users <= 50 and 1 <= args.timeout_users <= args.users and 1 <= args.duration <= 300):
        parser.error('Use 1-50 users, 1-300 seconds and a bounded concurrent timeout cohort')
    with tempfile.TemporaryDirectory(prefix='fridgely-generation-load-') as directory:
        raise SystemExit(0 if asyncio.run(measure(args, directory)) else 1)

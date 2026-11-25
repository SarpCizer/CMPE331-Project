"""50 real signed-in users, 100 owned inventory entries each, five-minute load.

Use only an isolated test database. No tokens or credentials are exported.
"""
import argparse
import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import secrets
import time

import httpx

ROUTES = {'inventory':'/inventory','profile':'/profile/preferences',
          'shopping':'/shopping-items','favorites':'/favorites'}


def statistics(samples):
    times=sorted(duration for duration,status in samples)
    errors=sum(status!=200 for _duration,status in samples)
    return {'requests':len(samples),'errors':errors,'error_rate':errors/len(samples),
        'p95_ms':times[math.ceil(len(times)*0.95)-1], 'max_ms':times[-1],
        'mean_ms':sum(times)/len(times),'statuses':dict(Counter(str(status) for _duration,status in samples))}


async def run(args):
    started=datetime.now(timezone.utc).isoformat()
    run_id=secrets.token_hex(8)
    password=secrets.token_urlsafe(24)
    tokens=[]
    semaphore=asyncio.Semaphore(5)
    limits=httpx.Limits(max_connections=100,max_keepalive_connections=100)
    async with httpx.AsyncClient(base_url=args.base.rstrip('/'),timeout=10,limits=limits,
                                 follow_redirects=False,trust_env=False) as client:
        async def required(method,path,body=None,token=None,expected=200):
            response=await client.request(method,path,json=body,
                headers={'Authorization':f'Bearer {token}'} if token else {})
            if response.status_code!=expected:
                raise RuntimeError(f'Setup failed: {method} {path}: {response.status_code}')
            return response.json()

        async def seed(index):
            async with semaphore:
                credentials={'email':f'load-{run_id}-{index}@example.test','password':password}
                await required('POST','/accounts',credentials,expected=201)
                token=(await required('POST','/sessions',credentials))['token']
                for item in range(args.entries):
                    await required('POST','/inventory',{'name':f'ingredient-{item}'},token,201)
                if len(await required('GET','/inventory',token=token))!=args.entries:
                    raise RuntimeError('Setup inventory count does not match scenario')
                return token
        tokens=await asyncio.gather(*(seed(index) for index in range(args.users)))
        print(f'Seeded {len(tokens)} real accounts and {args.users*args.entries} inventory entries.',flush=True)
        observations=defaultdict(list)
        start=time.perf_counter()
        deadline=start+args.duration

        async def user(token):
            while time.perf_counter()<deadline:
                for route,path in ROUTES.items():
                    before=time.perf_counter()
                    try:
                        response=await client.get(path,headers={'Authorization':f'Bearer {token}'})
                        status=response.status_code
                    except httpx.HTTPError:
                        status=0
                    observations[route].append(((time.perf_counter()-before)*1000,status))
                await asyncio.sleep(1)
        await asyncio.gather(*(user(token) for token in tokens))
        elapsed=time.perf_counter()-start
    by_route={route:statistics(samples) for route,samples in observations.items()}
    total=statistics([sample for samples in observations.values() for sample in samples])
    passed=total['p95_ms']<=500 and total['error_rate']<0.01 and all(
        value['p95_ms']<=500 and value['error_rate']<0.01 for value in by_route.values())
    result={'started_utc':started,'revision':args.revision,'environment':args.environment,
        'client':{'system':platform.system(),'architecture':platform.machine(),
                  'python':platform.python_version(),'cpu_count':os.cpu_count()},
        'scenario':{'users':args.users,'inventory_per_user':args.entries,
                    'configured_seconds':args.duration,'measured_seconds':elapsed,
                    'think_seconds':1,'shopping_and_favorites':'empty owned collections',
                    'provider':'not called in measured loop'},
        'thresholds':{'p95_ms_max':500,'error_rate_exclusive_max':0.01},
        'overall':total,'routes':by_route,'passed':passed,
        'interpretation':'Evidence for this named environment only; not a production or live-provider benchmark.'}
    destination=Path(args.output);destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':passed,'requests':total['requests'],'p95_ms':total['p95_ms'],
                      'error_rate':total['error_rate'],'output':str(destination)}),flush=True)
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:8000')
    parser.add_argument('--users',type=int,default=50)
    parser.add_argument('--entries',type=int,default=100)
    parser.add_argument('--duration',type=int,default=300)
    parser.add_argument('--revision',required=True)
    parser.add_argument('--environment',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    if not (1<=args.users<=50 and 1<=args.entries<=100 and 1<=args.duration<=3600):
        parser.error('Users 1-50, entries 1-100 and duration 1-3600 are required')
    raise SystemExit(0 if asyncio.run(run(args)) else 1)

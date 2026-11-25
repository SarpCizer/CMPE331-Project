"""Exercise the deployable host with disposable accounts, never export credentials."""
import argparse
import json
from pathlib import Path
import secrets
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--restart-container')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    results = []

    def request(method, path, body=None, token=None, expected=200):
        headers = {'Content-Type':'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
            method=method, headers=headers)
        try:
            with urlopen(req,timeout=90) as response:
                status, raw = response.status, response.read()
        except HTTPError as error:
            status, raw = error.code, error.read()
        assert status == expected, f'{method} {path}: expected {expected}, received {status}'
        results.append({'method':method,'path':path,'status':status})
        return json.loads(raw) if raw and raw[:1] in (b'{', b'[') else raw

    def ready():
        for _ in range(90):
            try:
                return request('GET','/api/health')
            except (AssertionError,URLError):
                time.sleep(2)
        raise RuntimeError('Host did not become ready')

    ready()
    request('GET','/')
    request('GET','/api/docs')
    request('GET','/api/docs/assets/swagger-ui-bundle.js')
    schema = request('GET','/api/openapi.json')
    assert schema['components']['securitySchemes']['BearerAuth']['bearerFormat'] == 'JWT'
    users = []
    for _ in range(2):
        credentials = {'email':f'cloud-smoke-{secrets.token_hex(12)}@example.test',
            'password':secrets.token_urlsafe(24)}
        request('POST','/api/accounts',credentials,expected=201)
        login = request('POST','/api/sessions',credentials)
        users.append((credentials,login['token']))
    credentials, alice = users[0]
    bob = users[1][1]
    item = request('POST','/api/inventory',{'name':'rice'},alice,201)
    preferences = {'dietary':['vegan'],'allergens':['peanut']}
    request('PUT','/api/profile/preferences',preferences,alice)
    request('POST','/api/shopping-items',{'name':'tomato'},alice,201)
    assert request('GET','/api/inventory',token=bob) == []
    request('DELETE',f'/api/inventory/{item["id"]}',token=bob,expected=404)
    assert request('GET','/api/profile/preferences',token=bob) == {'dietary':[],'allergens':[]}
    assert request('GET','/api/shopping-items',token=bob) == []
    before = [request('GET',path,token=alice) for path in
        ['/api/inventory','/api/profile/preferences','/api/shopping-items']]
    if args.restart_container:
        subprocess.run(['docker','restart',args.restart_container],check=True,capture_output=True)
        ready()
    login = request('POST','/api/sessions',credentials)
    after = [request('GET',path,token=login['token']) for path in
        ['/api/inventory','/api/profile/preferences','/api/shopping-items']]
    assert after == before
    assert request('GET','/api/inventory',token=alice) == before[0]
    # There is deliberately no OpenAI credential or fixture provider in the image test.
    if args.restart_container:
        request('POST','/api/recipes/generate',{},alice,503)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'base_url':base,'passed':True,'requests':results,
        'two_account_isolation':True,'relogin_persistence':True,
        'container_restart_persistence':bool(args.restart_container),
        'live_provider_tested':False},indent=2)+'\n')
    print(f'Cloud host smoke passed ({len(results)} requests); credentials were not exported')


if __name__ == '__main__':
    main()

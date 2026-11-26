"""Bounded OWASP ZAP API active scan against an isolated loopback test host.

Uses ZAP's official authentication-header environment variables. Scanner output
and reports are sanitized before publication. No alert is silently suppressed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from urllib.parse import urlparse

import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'helpers'))
from measured_source import verified_revision

IMAGE = 'ghcr.io/zaproxy/zaproxy:2.17.0'


def scan(args):
    if urlparse(args.base).hostname not in {'127.0.0.1', 'localhost'}:
        raise ValueError('ZAP is restricted to the disposable loopback test host')
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Use an empty output directory; preserve previous scan reports separately')
    suffix = secrets.token_hex(8)
    credentials = {'email': f'zap-{suffix}@example.test', 'password': secrets.token_urlsafe(28)}
    with httpx.Client(base_url=args.base, timeout=15, trust_env=False) as client:
        probe = client.get('/__security_probe__/metrics')
        if probe.status_code != 200 or probe.json().get('environment') != 'disposable-zap-fixture':
            raise ValueError('Target must be the disposable instrumented ZAP test host')
        client.post('/api/accounts', json=credentials).raise_for_status()
        session = client.post('/api/sessions', json=credentials)
        session.raise_for_status()
        token = session.json()['token']
        client.headers['Authorization'] = 'Bearer ' + token
        for name, quantity, unit in [('banana', 2, 'pcs'), ('milk', 200, 'ml'), ('sugar', 20, 'g')]:
            client.post('/api/inventory', json={'name': name, 'quantity': quantity, 'unit': unit}).raise_for_status()
        client.post('/api/recipes/generate', json={}).raise_for_status()
        before = client.get('/__security_probe__/metrics').json()
        if os.getenv('GITHUB_ACTIONS') == 'true':
            print('::add-mask::' + token, flush=True)
            print('::add-mask::' + credentials['password'], flush=True)
        environment = {**os.environ, 'ZAP_AUTH_HEADER': 'Authorization',
            'ZAP_AUTH_HEADER_VALUE': 'Bearer ' + token, 'ZAP_AUTH_HEADER_SITE': urlparse(args.base).hostname}
        container = 'fridgely-zap-' + suffix
        command = ['docker', 'run', '--name', container, '--network', 'host',
            '-e', 'ZAP_AUTH_HEADER', '-e', 'ZAP_AUTH_HEADER_VALUE',
            '-e', 'ZAP_AUTH_HEADER_SITE', IMAGE, 'sh', '-c',
            'mkdir -p /zap/wrk && exec zap-api-scan.py "$@"', 'zap-api-scan.py', '-t', args.base + '/api/openapi.json',
            '-f', 'openapi', '-J', 'zap-report.json', '-r', 'zap-report.html', '-I', '-T', '5', '-P', '8095',
            '-z', '-host 127.0.0.1 -config api.addrs.addr.name=127.0.0.1 -config api.addrs.addr.regex=false -config ascan.maxScanDurationInMins=4']
        code, scanner_log = 3, ''
        try:
            completed = subprocess.run(command, env=environment, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, timeout=600)
            code, scanner_log = completed.returncode, completed.stdout
        finally:
            # Copy only scanner output; the container never mounts the source checkout.
            for name in ('zap-report.json', 'zap-report.html'):
                subprocess.run(['docker', 'cp', container + ':/zap/wrk/' + name, str(output / name)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['docker', 'rm', '--force', container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for secret in (token, credentials['password']):
            scanner_log = scanner_log.replace(secret, '[REDACTED_TEST_CREDENTIAL]')
        (output / 'scanner.log').write_text(scanner_log, encoding='utf-8')
        for name in ('zap-report.json', 'zap-report.html'):
            path = output / name
            if path.exists():
                text = path.read_text(encoding='utf-8')
                for secret in (token, credentials['password']):
                    text = text.replace(secret, '[REDACTED_TEST_CREDENTIAL]')
                path.write_text(text, encoding='utf-8')
        after = client.get('/__security_probe__/metrics').json()
        authenticated = after['authenticated_successful_requests'] - before['authenticated_successful_requests']
        total = after['total_requests'] - before['total_requests']
        path = output / 'zap-report.json'
        report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        alerts = [alert for site in report.get('site', []) for alert in site.get('alerts', [])]
        risk = Counter(int(alert['riskcode']) for alert in alerts)
        digest = subprocess.run(['docker', 'image', 'inspect', IMAGE, '--format', '{{json .RepoDigests}}'],
            capture_output=True, text=True)
        passed = code in {0, 2} and path.is_file() and authenticated > 0 and total > 0 and not risk[3] and not risk[2]
        summary = {'revision': args.revision, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'tool': 'OWASP ZAP', 'image': IMAGE, 'image_digest': digest.stdout.strip(),
            'scan_type': 'authenticated OpenAPI API active scan, four-minute active budget',
            'target': args.base, 'scanner_exit_code': code, 'http_requests_observed': total,
            'authenticated_successful_requests_observed': authenticated,
            'alerts_by_risk': {'high': risk[3], 'medium': risk[2], 'low': risk[1], 'informational': risk[0]},
            'alert_rules': [{'rule': alert.get('pluginid'), 'name': alert.get('name'),
                'risk': alert.get('riskdesc'), 'confidence': alert.get('confidence'),
                'instances': len(alert.get('instances', []))} for alert in alerts],
            'policy': 'No untriaged high or medium alerts; retain low/informational findings for review.',
            'tokens_and_passwords_redacted': True, 'production_target': False, 'passed': passed}
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'passed': passed, 'alerts': summary['alerts_by_risk'], 'authenticated_requests': authenticated}))
        return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8094')
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', default='test-results/zap')
    args = parser.parse_args()
    args.revision = verified_revision(Path(__file__).resolve().parents[2], args.revision)
    raise SystemExit(0 if scan(args) else 1)

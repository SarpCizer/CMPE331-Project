"""Initialize an ephemeral local SonarQube and export actual analysis evidence."""
import json
import math
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.parse import urlparse

import requests

BASE=os.getenv('SONAR_HOST_URL','http://127.0.0.1:9000').rstrip('/')
if urlparse(BASE).hostname not in {'127.0.0.1','localhost'}:
    raise ValueError('This helper only initializes the isolated local CI analysis server')


def save(path,value):
    destination=Path('test-results/sonarqube')/path
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(value,indent=2)+'\n')


def initialize():
    password='Fridgely-'+secrets.token_urlsafe(24)+'-7!'
    response=requests.post(BASE+'/api/users/change_password',auth=('admin','admin'),
        data={'login':'admin','previousPassword':'admin','password':password},timeout=15)
    response.raise_for_status()
    session=requests.Session()
    session.auth=('admin',password)
    response=session.post(BASE+'/api/projects/create',data={'project':'fridgely','name':'Fridgely'},timeout=15)
    response.raise_for_status()
    response=session.post(BASE+'/api/user_tokens/generate',data={'name':'ephemeral-ci-analysis'},timeout=15)
    response.raise_for_status()
    token=response.json()['token']
    print(f'::add-mask::{token}',flush=True)
    with open(os.environ['GITHUB_ENV'],'a') as target:
        target.write(f'SONAR_TOKEN={token}\n')
    save('server.json',{'version':session.get(BASE+'/api/server/version',timeout=15).text,
        'scope':'ephemeral loopback-only CI server','project':'fridgely'})


def enforce_quality(gate, metrics):
    status = gate.get('projectStatus', {})
    conditions = status.get('conditions', [])
    failures = []
    if status.get('status') != 'OK':
        failures.append('Server quality gate is not OK')
    if status.get('ignoredConditions') or any(row.get('status') != 'OK' for row in conditions):
        failures.append('Server quality gate has ignored or unsuccessful conditions')
    measures = {row['metric']: row.get('value') for row in metrics.get('component', {}).get('measures', [])}
    checks = {}
    for metric in ('bugs', 'vulnerabilities', 'security_hotspots'):
        raw = measures.get(metric)
        try:
            value = float(raw)
            passed = math.isfinite(value) and value == 0
        except (TypeError, ValueError):
            passed = False
        checks[metric] = {'actual': raw, 'maximum': 0, 'passed': passed}
        if not passed:
            failures.append(f'{metric} must be present, numeric and zero')
    policy = {'passed': not failures, 'reported_gate': status.get('status'),
        'server_conditions_evaluated': bool(conditions) and not status.get('ignoredConditions', False),
        'security_measures': checks, 'failures': failures,
        'scope': 'Exported source metrics; zero hotspots does not assert manual hotspot review'}
    save('quality-policy.json', policy)
    if failures:
        raise RuntimeError('SonarQube quality policy failed; see retained quality-policy.json')


def export():
    session=requests.Session()
    session.headers['Authorization']='Bearer '+os.environ['SONAR_TOKEN']
    task_file=Path('.scannerwork/report-task.txt')
    properties=dict(line.split('=',1) for line in task_file.read_text().splitlines() if '=' in line)
    task_url=properties['ceTaskUrl']
    if not task_url.startswith(BASE+'/'):
        raise ValueError('Unexpected analysis task destination')
    task=None
    for _ in range(120):
        response=session.get(task_url,timeout=15);response.raise_for_status()
        task=response.json()['task']
        if task['status'] in {'SUCCESS','FAILED','CANCELED'}:
            break
        time.sleep(2)
    save('compute-task.json',task)
    if task['status']!='SUCCESS':
        raise RuntimeError('SonarQube analysis did not complete successfully')
    endpoints={
        'quality-gate.json':('/api/qualitygates/project_status',{'analysisId':task['analysisId']}),
        'metrics.json':('/api/measures/component',{'component':'fridgely','metricKeys':
            'bugs,vulnerabilities,code_smells,security_hotspots,coverage,line_coverage,branch_coverage,duplicated_lines_density,ncloc'}),
    }
    for name,(endpoint,params) in endpoints.items():
        response=session.get(BASE+endpoint,params=params,timeout=15);response.raise_for_status()
        save(name,response.json())
    issues=[]
    page=1
    while True:
        response=session.get(BASE+'/api/issues/search',params={'componentKeys':'fridgely','ps':500,'p':page},timeout=15)
        response.raise_for_status();data=response.json();issues.extend(data['issues'])
        if len(issues)>=data['paging']['total']:
            break
        page+=1
    save('issues.json',{'issues':issues,'total':len(issues),'revision':os.getenv('TESTED_REVISION','')})
    # Hotspot pagination limits differ between server editions/versions. Export
    # mandatory issues/metrics first; retain an explicit unsupported-API result
    # instead of losing completed analysis evidence.
    response=session.get(BASE+'/api/hotspots/search',params={'projectKey':'fridgely','ps':100},timeout=15)
    if response.ok:
        save('security-hotspots.json',response.json())
    else:
        save('security-hotspots.json',{'status':'API_UNAVAILABLE','http_status':response.status_code,
            'meaning':'Use security_hotspots in metrics.json; detailed hotspot review is not inferred.'})
    evidence = Path('test-results/sonarqube')
    gate = json.loads((evidence / 'quality-gate.json').read_text())
    metrics = json.loads((evidence / 'metrics.json').read_text())
    enforce_quality(gate, metrics)
    print(json.dumps({'analysis':'SUCCESS','quality_gate':gate['projectStatus']['status'],
        'security_policy':'PASS','issues':len(issues)}))


if __name__=='__main__':
    {'init':initialize,'export':export}[sys.argv[1]]()

"""Initialize an ephemeral local SonarQube and export actual analysis evidence."""
import json
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
        'security-hotspots.json':('/api/hotspots/search',{'projectKey':'fridgely','ps':500}),
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
    gate=json.loads((Path('test-results/sonarqube/quality-gate.json')).read_text())['projectStatus']['status']
    print(json.dumps({'analysis':'SUCCESS','quality_gate':gate,'issues':len(issues)}))
    # Analysis completion and gate result are distinct evidence. The report records
    # any remaining gate conditions; the server and its credentials are disposable.


if __name__=='__main__':
    {'init':initialize,'export':export}[sys.argv[1]]()

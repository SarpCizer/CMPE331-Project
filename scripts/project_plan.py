"""Calculate the proposed PERT/CPM network from the shared activity data."""
import json
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 10, 7)
DEADLINE = date(2026, 11, 30)

def calculate():
    items = json.loads((ROOT/'docs/plans/activities.json').read_text(encoding='utf-8'))
    nodes = {a['id']:dict(a) for a in items}
    if len(nodes) != len(items): raise ValueError('Duplicate activity ID')
    ordered=[]; pending=list(nodes)
    while pending:
        ready=[key for key in pending if all(p in ordered for p in nodes[key]['predecessors'])]
        if not ready: raise ValueError('Unknown predecessor or dependency cycle')
        for key in ready:
            a=nodes[key]
            o,m,p=a['optimistic'],a['most_likely'],a['pessimistic']
            if not 0<o<=m<=p: raise ValueError('Invalid estimates: '+key)
            expected=(o+4*m+p)/6
            if expected != int(expected): raise ValueError('This calendar baseline requires whole-day expected values')
            a['duration']=int(expected)
            a['variance']=((p-o)/6)**2
            a['es']=max((nodes[parent]['ef'] for parent in a['predecessors']),default=0)
            a['ef']=a['es']+a['duration']
            a['successors']=[other for other in nodes if key in nodes[other]['predecessors']]
            ordered.append(key); pending.remove(key)
    finish=max(a['ef'] for a in nodes.values())
    for key in reversed(ordered):
        a=nodes[key]
        a['lf']=min((nodes[s]['ls'] for s in a['successors']),default=finish)
        a['ls']=a['lf']-a['duration']; a['slack']=a['ls']-a['es']
        a['start']=(START+timedelta(days=a['es'])).isoformat()
        a['finish']=(START+timedelta(days=a['ef']-1)).isoformat()
        assert a['slack']>=0 and a['lf']>=a['ef']
    paths=[]
    def visit(key,path):
        a=nodes[key]
        if not a['successors']:
            if a['ef']==finish: paths.append(path)
            return
        for s in a['successors']:
            if nodes[s]['slack']==0 and a['ef']==nodes[s]['es']: visit(s,path+[s])
    for key in ordered:
        if not nodes[key]['predecessors'] and nodes[key]['slack']==0: visit(key,[key])
    return [nodes[key] for key in ordered],finish,paths

def cpm_table():
    rows,finish,paths=calculate()
    return '| ID | Days | ES | EF | LS | LF | Slack |\n|---|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(
        '| '+a['id']+' | '+' | '.join(str(a[k]) for k in ('duration','es','ef','ls','lf','slack'))+' |' for a in rows)

if __name__=='__main__':
    rows,finish,paths=calculate()
    print(cpm_table())
    print('Critical paths:',paths)
    print('Expected duration:',finish,'calendar days')
    print('Planned finish:',START+timedelta(days=finish-1))
    print('Deadline reserve:',(DEADLINE-(START+timedelta(days=finish-1))).days,'calendar day(s)')

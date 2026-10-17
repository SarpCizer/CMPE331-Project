"""Validate DFD structure, criterion fidelity, model hashes and report completeness."""
from pathlib import Path
from urllib.parse import unquote,urlparse
import hashlib,json,re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'docs/analysis'
coverage=json.loads((A/'coverage.json').read_text(encoding='utf-8'))
assert coverage['baseline']=='4839cdfdf7f53f226373380f41c307886d08906a'
assert {s['story'] for s in coverage['stories']}=={f'US-{n:02d}' for n in range(1,16)}
er=(A/'data/er-model.mmd').read_text(encoding='utf-8')
entities=set(re.findall(r'^    ([A-Z_]+) \{',er,re.M))
assert len(entities)==10
assert 'string value_key PK' not in er
assert er.count('integer position PK')==4
count=0
for story in coverage['stories']:
    sid=story['story']
    criteria=re.findall(r'^\d+\. (.+)$',(ROOT/f'docs/requirements/{sid}.md').read_text(encoding='utf-8'),re.M)
    assert len(criteria)==len(story['criteria'])
    for i,(text,mapping) in enumerate(zip(criteria,story['criteria']),1):
        assert mapping['id']==f'{sid}-AC-{i}' and mapping['text']==text
        assert mapping['model_type']=='DFD'
        for model in [mapping['behavior']]+mapping['supporting_behavior']:assert (A/model).is_file(),model
        assert set(mapping['data'])<=entities
        assert mapping['frontend']
    count+=len(criteria)
assert count==48
lookup={c['id']:c for s in coverage['stories'] for c in s['criteria']}
assert {'behavior/US-07.md','behavior/US-09.md'}<=set(lookup['US-08-AC-2']['supporting_behavior'])
assert {'behavior/US-08.md','behavior/US-12.md'}<=set(lookup['US-06-AC-3']['supporting_behavior'])
assert 'behavior/US-07.md' in lookup['US-03-AC-3']['supporting_behavior']

dfds=list((A/'behavior').glob('*.dfd.json'))
assert len(dfds)==17
assert not list((A/'behavior').glob('*.mmd')),'Superseded flowchart sources remain'
model_by_name={}
for source in dfds:
    model=json.loads(source.read_text(encoding='utf-8'))
    assert model['notation']=='Yourdon-DeMarco DFD'
    nodes={n['id']:n for n in model['nodes']}
    assert len(nodes)==len(model['nodes'])
    assert all(n['kind'] in ('process','external','store') and n['label'] for n in nodes.values())
    assert model['rules']
    for flow in model['flows']:
        assert flow['from'] in nodes and flow['to'] in nodes
        assert nodes[flow['from']]['kind']=='process' or nodes[flow['to']]['kind']=='process',flow
        assert flow['from']!=flow['to'] and flow['label'].strip().lower() not in ('yes','no','next','success','failure')
    for id,n in nodes.items():
        if n['kind']=='process':
            assert any(f['to']==id for f in model['flows']),('Process has no input',source,id)
            assert any(f['from']==id for f in model['flows']),('Process has no output',source,id)
    if source.name=='US-09.dfd.json':assert not any(nodes[f['to']]['kind']=='store' for f in model['flows'])
    if source.name in [f'US-{i:02d}.dfd.json' for i in (7,8,10,11,12,13,14)]:
        assert not any(f['to']=='D3' for f in model['flows']),('Unauthorized inventory write',source)
    md=source.with_name(source.name.replace('.dfd.json','.md')).read_text(encoding='utf-8')
    assert source.name in md
    for flow in model['flows']:assert flow['label'] in md
    for rule in model['rules']:assert rule in md
    model_by_name[source.name]=model
interfaces=lambda m:{f.get('interface') for f in m['flows'] if f.get('interface')}
assert interfaces(model_by_name['context-dfd.dfd.json'])==interfaces(model_by_name['level-1-dfd.dfd.json'])=={'AUTH_IN','AUTH_OUT','PERSONAL_IN','PERSONAL_OUT','AI_IN','AI_OUT'}

sources=list((A/'data').glob('*.mmd'))+dfds
assert len(sources)==19
manifest=json.loads((A/'render-manifest.json').read_text(encoding='utf-8'))['diagrams']
assert {item['source'] for item in manifest}=={p.relative_to(ROOT).as_posix() for p in sources}
for source in (A/'data').glob('*.mmd'):
    block=re.search(r'```mermaid\n(.*?)\n```',source.with_suffix('.md').read_text(encoding='utf-8'),re.S)
    assert block and block.group(1).strip()==source.read_text(encoding='utf-8').strip()
for item in manifest:
    source=ROOT/item['source'];image=ROOT/item['svg']
    for path,key in [(source,'source_sha256'),(image,'svg_sha256')]:
        assert hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()==item[key],path
    svg=ET.fromstring(image.read_text(encoding='utf-8'))
    if item['kind']=='DFD':
        stores=len([n for n in json.loads(source.read_text(encoding='utf-8'))['nodes'] if n['kind']=='store'])
        assert len([e for e in svg.iter() if e.get('data-dfd-kind')=='store'])==stores,image
report=ROOT/'docs/analysis-report.md'
report_text=report.read_text(encoding='utf-8')
embedded={str((report.parent/path).resolve()) for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',report_text)}
assert all(str((ROOT/item['svg']).resolve()) in embedded for item in manifest),'Report omits a diagram'
broken=[]
for md in list(A.rglob('*.md'))+[report,ROOT/'scripts/analysis/README.md']:
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if urlparse(link).scheme or link.startswith('#'):continue
        if not (md.parent/unquote(link.split('#')[0])).exists():broken.append((md.relative_to(ROOT).as_posix(),link))
assert not broken,broken
print('Validated 15 stories / 48 exact criteria; 17 typed DFDs; balanced external interfaces; 10 E-R entities; 19 rendered-source pairs; all report diagrams and local links.')

"""Check analysis coverage and artifact integrity, without application dependencies."""
from pathlib import Path
from urllib.parse import unquote, urlparse
import hashlib, json, re

ROOT=Path(__file__).resolve().parents[2]
ANALYSIS=ROOT/'docs/analysis'
coverage=json.loads((ANALYSIS/'coverage.json').read_text(encoding='utf-8'))
assert coverage['baseline']=='4839cdfdf7f53f226373380f41c307886d08906a'
stories=coverage['stories']
assert {story['story'] for story in stories}=={f'US-{n:02d}' for n in range(1,16)}
er=(ANALYSIS/'data/er-model.mmd').read_text(encoding='utf-8')
entities=set(re.findall(r'^    ([A-Z_]+) \{',er,re.M))
assert len(entities)==10,entities
count=0
for story in stories:
    sid=story['story']
    text=(ROOT/f'docs/requirements/{sid}.md').read_text(encoding='utf-8')
    criteria=re.findall(r'^\d+\. (.+)$',text,re.M)
    assert len(criteria)==len(story['criteria']),sid
    for index,(criterion,mapping) in enumerate(zip(criteria,story['criteria']),1):
        assert mapping['id']==f'{sid}-AC-{index}'
        assert mapping['text']==criterion,(sid,index,'criterion drift')
        assert (ANALYSIS/mapping['behavior']).is_file()
        assert set(mapping['data'])<=entities
        assert mapping['frontend']
    behavior=(ANALYSIS/f'behavior/{sid}.mmd').read_text(encoding='utf-8')
    if int(sid[-2:])>=3 and sid not in ('US-09','US-15'): assert 'US-15 authentication and owner gate' in behavior,sid
    if sid=='US-09': assert 'Authenticated US-07 generation' in behavior,sid
    count+=len(criteria)
assert count==48,count
sources=list((ANALYSIS/'data').glob('*.mmd'))+list((ANALYSIS/'behavior').glob('*.mmd'))
assert len(sources)==20,len(sources)
manifest=json.loads((ANALYSIS/'render-manifest.json').read_text(encoding='utf-8'))['diagrams']
assert {item['source'] for item in manifest}=={path.relative_to(ROOT).as_posix() for path in sources}
for path in sources:
    source=path.read_text(encoding='utf-8').strip()
    md=path.with_suffix('.md').read_text(encoding='utf-8')
    block=re.search(r'```mermaid\n(.*?)\n```',md,re.S)
    assert block and block.group(1).strip()==source,(path,'Markdown/source mismatch')
for item in manifest:
    source=ROOT/item['source'];image=ROOT/item['svg']
    assert hashlib.sha256(source.read_text(encoding='utf-8').encode()).hexdigest()==item['source_sha256'],source
    assert hashlib.sha256(image.read_text(encoding='utf-8').encode()).hexdigest()==item['svg_sha256'],image
    svg=image.read_text(encoding='utf-8')
    assert '<svg' in svg and '</svg>' in svg
broken=[]
for path in list(ANALYSIS.rglob('*.md'))+[ROOT/'docs/analysis-report.md',ROOT/'scripts/analysis/README.md']:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if urlparse(target).scheme or target.startswith('#'):continue
        target=unquote(target.split('#')[0])
        if not (path.parent/target).exists():broken.append((path.relative_to(ROOT).as_posix(),target))
assert not broken,broken
html=(ANALYSIS/'frontend/index.html').read_text(encoding='utf-8')
assert 'app.js' in html and 'styles.css' in html
print('Validated 15 stories, 48 exact acceptance criteria, 10 E-R entities, 20 source/SVG pairs and all local analysis Markdown links.')

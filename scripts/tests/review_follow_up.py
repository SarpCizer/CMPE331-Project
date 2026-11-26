"""Validate and append measured instructor-review evidence to the historical report."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.platypus import Image, Spacer

REPO='https://github.com/SarpCizer/CMPE331-Project'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load(base):
    config=read(base/'review-follow-up.json')
    revision=config['source_revision']
    if not re.fullmatch('[0-9a-f]{40}',revision): raise ValueError('Invalid follow-up source')
    root=(base/config['evidence_root']).resolve()
    if not root.is_relative_to(base.resolve()): raise ValueError('Unsafe follow-up evidence root')
    index=read(root/'evidence-index.json')
    if index['source_revision']!=revision or index['ci_run_id']!=config['ci_run_id']:
        raise ValueError('Follow-up evidence source/run mismatch')
    required={'ci-jobs.json','integrated/postgresql-load.json','integrated/recipe-generation-load.json',
        'integrated/backend-junit.xml','integrated/browser-junit.xml','integrated/backend-coverage.json',
        'integrated/acceptance.log','integrated/http-security.log',
        'local/non-ai-load.json','local/recipe-generation-load.json','zap/summary.json',
        'sonar/source-identity.json','sonar/quality-gate.json','sonar/metrics.json',
        'sonar/dashboard-capture.json','sonar/dashboard.png','coverage/coverage-gate.json','traceability/traceability.json'}
    if not required.issubset(index['files']): raise ValueError('Required follow-up evidence is not indexed')
    for name, metadata in index['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root): raise ValueError('Unsafe follow-up evidence path')
        data=path.read_bytes()
        if len(data)!=metadata['bytes'] or hashlib.sha256(data).hexdigest()!=metadata['sha256']:
            raise ValueError('Follow-up evidence digest mismatch: '+name)
    if read(root/'traceability/traceability.json')!=read(base/'coverage/traceability.json'):
        raise ValueError('Follow-up assertion mapping differs from indexed evidence')
    jobs=read(root/'ci-jobs.json')
    if jobs['head_sha']!=revision or jobs['run_id']!=config['ci_run_id'] or len(jobs['jobs'])!=8 or any(j['conclusion']!='success' for j in jobs['jobs']):
        raise ValueError('Follow-up CI is incomplete')
    for path in ['integrated/postgresql-load.json','integrated/recipe-generation-load.json','local/non-ai-load.json','local/recipe-generation-load.json','zap/summary.json']:
        value=read(root/path)
        if value['revision']!=revision or (not path.startswith('local/') and value['passed'] is not True):
            raise ValueError('Follow-up measurement source/result mismatch: '+path)
    zap=read(root/'zap/summary.json')
    if zap['authenticated_successful_requests_observed']<=0 or zap['alerts_by_risk']['high'] or zap['alerts_by_risk']['medium']:
        raise ValueError('Follow-up ZAP policy or authentication failed')
    sonar=read(root/'sonar/source-identity.json')
    if sonar['analysis_revision']!=revision or sonar['test_revision']!=revision or sonar['test_artifacts_reused']:
        raise ValueError('Follow-up Sonar source mismatch')
    gate=read(root/'sonar/quality-gate.json')['projectStatus']
    expected={'bugs':('GT',0),'vulnerabilities':('GT',0),
        'coverage':('LT',90),'blocker_violations':('GT',0),'critical_violations':('GT',0)}
    conditions={c['metricKey']:c for c in gate.get('conditions',[])}
    if gate.get('status')!='OK' or set(conditions)!=set(expected) or len(gate.get('conditions',[]))!=len(expected):
        raise ValueError('Follow-up Sonar conditions are incomplete')
    for name,(operator,threshold) in expected.items():
        item=conditions[name]
        value=float(item['actualValue'])
        if item['status']!='OK' or item['comparator']!=operator or float(item['errorThreshold'])!=threshold or not (threshold<=value<=100 if name=='coverage' else value==0):
            raise ValueError('Follow-up Sonar condition failed: '+name)
    metrics={item['metric']:item['value'] for item in read(root/'sonar/metrics.json')['component']['measures']}
    if float(metrics['security_hotspots'])!=0: raise ValueError('Unreviewed follow-up security hotspots')
    capture=read(root/'sonar/dashboard-capture.json')
    if capture['revision']!=revision or capture['credential_fields_present'] or not (root/'sonar/dashboard.png').is_file():
        raise ValueError('Missing actual follow-up dashboard')
    return config,root


def bars(title, labels, values, maximum, suffix='%', threshold=None):
    drawing=Drawing(499,58+len(labels)*31)
    drawing.add(String(0,drawing.height-15,title,fontName='ReportBold',fontSize=10,fillColor=colors.HexColor('#173f2f')))
    left,width=190,240
    for index,(label,value) in enumerate(zip(labels,values)):
        y=drawing.height-43-index*31
        drawing.add(String(0,y+4,label,fontName='Report',fontSize=8))
        drawing.add(Rect(left,y,width,16,fillColor=colors.HexColor('#e9f1e7'),strokeColor=None))
        drawing.add(Rect(left,y,width*value/maximum,16,fillColor=colors.HexColor('#387559'),strokeColor=None))
        drawing.add(String(left+width+6,y+4,f'{value:.2f}{suffix}',fontName='Report',fontSize=8))
    if threshold is not None:
        x=left+width*threshold/maximum
        drawing.add(Line(x,22,x,drawing.height-26,strokeColor=colors.HexColor('#b74f33'),strokeWidth=1))
        drawing.add(String(x-35,6,f'Limit {threshold:g}{suffix}',fontName='Report',fontSize=7))
    return drawing


def append(base, story, markdown, heading, paragraph, table, page, config, root):
    revision,run=config['source_revision'],config['ci_run_id']
    short=revision[:7]
    coverage=read(root/'coverage/coverage-gate.json')['actual_percent']
    load_result=read(root/'integrated/postgresql-load.json')
    generation=read(root/'integrated/recipe-generation-load.json')
    local=read(root/'local/non-ai-load.json')
    local_generation=read(root/'local/recipe-generation-load.json')
    zap=read(root/'zap/summary.json')
    mapping=read(root/'traceability/traceability.json')
    backend=ET.parse(root/'integrated/backend-junit.xml').getroot()
    browser=ET.parse(root/'integrated/browser-junit.xml').getroot()
    def junit_count(element):
        suites=[element] if element.tag=='testsuite' else list(element.iter('testsuite'))
        return (sum(int(s.get('tests',0))-int(s.get('skipped',0)) for s in suites),
            sum(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites),
            sum(int(s.get('skipped',0)) for s in suites))
    backend_count,backend_bad,backend_skipped=junit_count(backend)
    browser_count,browser_bad,browser_skipped=junit_count(browser)
    if backend_bad or browser_bad: raise ValueError('Follow-up tests have failures/errors/skips')
    skipped=[case for case in backend.iter('testcase') if case.find('skipped') is not None]
    if backend_skipped!=3 or browser_skipped or any('test_planner_sqlite_race' not in case.get('classname','') for case in skipped):
        raise ValueError('Unexpected skipped follow-up tests')
    def node_count(name):
        text=(root/'integrated'/name).read_text(encoding='utf-8')
        result={key:int(value) for key,value in re.findall(r'^[#\u2139] (tests|pass|fail|cancelled|skipped) (\d+)',text,re.MULTILINE)}
        if result.get('tests',0)<=0 or result.get('pass')!=result['tests'] or any(result.get(k,1) for k in ['fail','cancelled','skipped']):
            raise ValueError('Incomplete Node evidence: '+name)
        return result['tests']
    acceptance_count,http_count=node_count('acceptance.log'),node_count('http-security.log')
    figures=base/'figures';figures.mkdir(exist_ok=True)
    def figure(name,drawing):
        renderSVG.drawToFile(drawing,str(figures/name))
        story.extend([drawing,Spacer(1,10)])
        markdown.extend([f'![{name}](figures/{name})',''])

    page();heading('Instructor review follow-up',True)
    paragraph(f'Corrections by Sarp Çizer with Codex assistance. Historical pages retain their a59556e measurements; the following pages use the separately measured source {revision}. This branch has not been merged or deployed by this correction.')
    paragraph(f'[Follow-up CI run {run}]({REPO}/actions/runs/{run}) | [Source {short}]({REPO}/commit/{revision}) | [Review corrections PR #94]({REPO}/pull/94)')
    table(['Review item','Concrete correction'],[
        ['Rebuild / inventory / versions','Create absent parent folders; UTF-8 and raw-byte guards; immutable browser inventory; every load value keeps its source/environment.'],
        ['AC and NFR traceability','48 AC and 9 NFR rows name concrete assertions with immutable line links; physical IDs validated unique.'],
        ['Security / generation load','Bound login guesses; authenticated bounded ZAP plus original probes; real HTTP concurrency and five simultaneous provider deadlines.'],
        ['Sonar / interpretation / figures','Five evaluated server conditions and independent zero-hotspot policy; twelve S2970 false positives labelled; actual dashboard and coverage/performance plots embedded.'],
    ],[133,366])
    table(['Actual follow-up evidence','Result'],[
        ['PostgreSQL/backend JUnit',f'{backend_count} passed; {backend_skipped} SQLite-only interleaving cases skipped in PostgreSQL'],
        ['Browser JUnit',f'{browser_count} passed'],
        ['Acceptance / real HTTP checks',f'{acceptance_count} / {http_count} passed'],
        ['CI delivery and analysis','All eight jobs successful; no earlier failed attempt counted as a pass'],
        ['ZAP authenticated requests',str(zap['authenticated_successful_requests_observed'])],
        ['ZAP high / medium',f'{zap["alerts_by_risk"]["high"]} / {zap["alerts_by_risk"]["medium"]}'],
    ],[245,254])
    paragraph('Test-first history is retained: the missing sign-in limit and incomplete Sonar conditions failed before their implementation commits. Added display assertions verify the actual saved addition date, estimate labels, calories and servings. Tests use disposable databases and controlled providers; no production attack or load was performed.','small')

    page();heading('Coverage: results and missed branches',True)
    figure('review-coverage.svg',bars(f'Follow-up coverage | {short}',
        ['Backend statements','Backend branches','Frontend lines','Frontend branches','Frontend functions'],
        [coverage[k] for k in ['backend_statements','backend_branches','frontend_lines','frontend_branches','frontend_functions']],100))
    paragraph('Executing a line does not exercise every branch leaving it. A valid recipe can execute a validation line while leaving its malformed-output exit untested. The older local summary records 933/1016 statements (91.83%) and 136/184 branches (73.91%); the a59556e CI snapshot records 941/1026 statements (91.72%) and 143/188 branches (76.06%). These are different snapshots, not one combined result.')
    paragraph('At a59556e the raw branch report identifies 45 missed exits. Seven are in provider parsing/initialization, including missing outputs, malformed content, missing credentials and explicit failed status; five in frontend host routing with/without built assets; five in ordered-preference migration paths for different pre-existing schemas. Three security exits include invalid signing-key length, out-of-range token lifetime and an excessive-length token. The fixtures did not exercise every input shape or error exit. Exact source arcs are preserved; high statement coverage does not make these branches tested.')
    raw=read(root/'integrated/backend-coverage.json')
    missed=sorted(raw['files'].items(),key=lambda item:item[1]['summary']['missing_branches'],reverse=True)[:5]
    table(['Current file','Missed exits / example source arcs'],[
        [name.replace('backend/src/',''),f'{item["summary"]["missing_branches"]} / '+', '.join(f'{a}->{b}' for a,b in item.get('missing_branches',[])[:4])]
        for name,item in missed
    ],[293,206])
    paragraph('A positive exit number is a source line; a negative number denotes function exit. Statement and branch denominators come directly from coverage.py, not test counts. Current missed arcs are diagnostic follow-up work; passing the unchanged coverage floor is not a claim of complete branch coverage.','small')

    page();heading('Performance: version-qualified comparison',True)
    figure('review-non-ai-performance.svg',bars('Non-AI HTTP p95 | 50 users, 100 rows each, five minutes',
        ['Historical local 9f43e3a','Historical CI 25c111a','Report CI a59556e',f'Local {short}',f'CI {short}'],
        [44.353917,371.467618,204.055576,local['overall']['p95_ms'],load_result['overall']['p95_ms']],
        max(550,local['overall']['p95_ms']*1.15,load_result['overall']['p95_ms']*1.15),suffix=' ms',threshold=500))
    paragraph(f'The follow-up local and CI runs both identify {revision}; the source guard rejects guessed SHAs or uncommitted application/test changes. Local environment: {local["environment"]}. CI environment: {load_result["environment"]}. Both run the same non-AI profile; database/CPU/OS still differ, so their difference does not isolate a cause.')
    paragraph('The older 371.47ms CI p95 was 8.38 times the 44.35ms local p95 and only 128.53ms below the 500ms limit. Those runs also used different application revisions. Database/runner contention and intervening code are plausible explanations, not established causes; no CPU/SQL trace from those old runs exists. The a59556e result was 204.06ms. All historical observations, including errors/outliers, remain retained.')
    table(['Same-source environment','Requests / errors','p95 / margin to 500ms'],[
        ['Local SQLite',f'{local["overall"]["requests"]} / {local["overall"]["errors"]}',f'{local["overall"]["p95_ms"]:.2f} / {500-local["overall"]["p95_ms"]:.2f} ms'],
        ['CI PostgreSQL',f'{load_result["overall"]["requests"]} / {load_result["overall"]["errors"]}',f'{load_result["overall"]["p95_ms"]:.2f} / {500-load_result["overall"]["p95_ms"]:.2f} ms'],
    ],[175,140,184])
    paragraph(f'Local NFR-03 profile: {"PASS" if local["passed"] else "FAIL"}; CI profile: {"PASS" if load_result["passed"] else "FAIL"}. A negative margin means that environment exceeded the limit. Failed local measurements are retained and do not become CI passes. This is an isolated agreed CI-environment assessment; neither row is a production SLA. Each route must also satisfy p95 <=500ms and errors<1%. Provider calls are excluded from this measurement.','small')

    page();heading('Generation load and security results',True)
    figure('review-generation-performance.svg',bars(f'Controlled generation HTTP p95 | {short}',
        ['Local SQLite, ten users','CI PostgreSQL, ten users'],
        [local_generation['steady']['p95_ms'],generation['steady']['p95_ms']],
        max(2200,local_generation['steady']['p95_ms']*1.15,generation['steady']['p95_ms']*1.15),suffix=' ms',threshold=2000))
    paragraph(f'Ten users, one-second think time, 60 measured seconds, controlled 200ms provider: CI completed {generation["steady"]["requests"]} HTTP requests with {generation["steady"]["errors"]} errors. The experimental 2,000ms p95 gate is separate from the non-AI 500ms NFR. Accepted recipes persisted and inventory remained unchanged.')
    times=[row['seconds'] for row in generation['concurrent_timeouts']['results']]
    paragraph(f'Five simultaneous stalled-provider requests returned retryable 503 in {min(times):.2f}–{max(times):.2f}s, within the 30s requirement. All five providers were cancelled at the configured 28s deadline; no partial recipe rows or stock changes occurred. External model calls: zero.')
    paragraph('Login guessing is now bounded before expensive hashing: five failed attempts per account/transport-client per minute, plus 200 total attempts per transport client. HTTP 429 includes Retry-After. Known/unknown account, expiry, spoofed header, parallel reservation and memory-cap regressions pass. This process-local control resets on restart and needs shared atomic storage before deploying multiple workers/replicas.')
    risk=zap['alerts_by_risk']
    paragraph(f'OWASP ZAP {zap["image"]} completed an authenticated OpenAPI active scan with a four-minute active budget against a disposable loopback host: {zap["http_requests_observed"]} observed requests, including {zap["authenticated_successful_requests_observed"]} protected successful requests. Alerts: {risk["high"]} high, {risk["medium"]} medium, {risk["low"]} low and {risk["informational"]} informational. The raw report retains every rule and its instances; no failed setup attempt is treated as a clean scan.')
    for alert in zap['alert_rules']:
        paragraph(f'ZAP {alert["rule"]}: {alert["name"]} — {alert["risk"]}; {alert["instances"]} instances. '+config.get('zap_triage',{}).get(str(alert['rule']),'See retained alert evidence and review scope.'),'small')
    paragraph('The scanner complements four targeted probes, the owner/method JWT matrix and dependency/secret checks. Bounded active scanning is not a complete penetration audit. Synthetic credentials are redacted; no production host, paid resource or live inference was used.','small')

    page();heading('Sonar: actual evaluated dashboard',True)
    paragraph(f'Actual ephemeral server UI, captured after analysis of {short}. The screenshot is not a recreated dashboard. Its durable raw metrics, configured gate and observed condition values are retained with the same source identity. The temporary loopback URL is not a public persistent service.','small')
    image=Image(str(root/'sonar/dashboard.png'))
    scale=min(499/image.imageWidth,420/image.imageHeight)
    image.drawWidth,image.drawHeight=image.imageWidth*scale,image.imageHeight*scale
    image.hAlign='CENTER';story.extend([image,Spacer(1,9)])
    markdown.extend([f'![Actual Sonar dashboard]({config["evidence_root"]}/sonar/dashboard.png)',''])
    gate=read(root/'sonar/quality-gate.json')['projectStatus']
    table(['Evaluated metric','Error condition','Observed'],[
        [item['metricKey'],item['comparator']+' '+item['errorThreshold'],item['actualValue']]
        for item in gate['conditions']
    ],[235,120,144])
    paragraph('The historical twelve javascript:S2970 BLOCKER alerts were false positives: the custom HTTP helper already called Node assert.equal, but its name expect triggered Jest matcher analysis. Renaming it assertResponse corrected framework detection while retaining assertions. It did not fix twelve security vulnerabilities. Original exports and the mitigation register remain preserved.','small')

    page();heading('Traceability and reproducible review',True)
    paragraph(f'All 48 approved acceptance criteria and nine NFRs map to concrete assertion locations. The {mapping["unique_physical_acceptance_ids"]} physical US-xx-Txx IDs are unique. Assertions are pinned to {mapping["assertion_revision"]}; the validation run verifies that the mapped test files are unchanged in the follow-up source. A shared scenario is acceptable when each row names its relevant verification, rather than repeating a whole-case ID as coverage proof.')
    paragraph(f'[Detailed AC/NFR matrix]({REPO}/blob/{revision}/docs/tests/coverage/traceability.md) contains the criterion, case, exact assertion, immutable source link, purpose and scope. The CSV and JSON preserve all 57 rows. Mapping completeness is not an assertion of 100% code coverage or live-provider safety.')
    if config.get('evidence_revision'):
        paragraph(f'[Retained raw evidence index]({REPO}/blob/{config["evidence_revision"]}/docs/tests/{config["evidence_root"]}/evidence-index.json) records SHA-256 and byte lengths for this follow-up bundle. Raw results remain separate from historical a59556e evidence.','small')
    table(['Requirement group','Specific evidence'],[
        ['US-01–03 / NFR-01–02','Account/JWT/preferences assertions; every personal method and foreign owner IDs; salted hashes/seeded secret inspection; bounded login windows.'],
        ['US-04–06 / NFR-05–07','Addition timestamp and date display; empty/owned inventory; isolated deletion; widths/keyboard/axe; two-process persistence.'],
        ['US-07–09 / NFR-04,08','Current provider inputs, allergen/malformed batch rejection, complete labelled details, unchanged collections and concurrent deadlines.'],
        ['US-10–15 / NFR-01,03,09','Missing-only/idempotent shopping, favorites/history, JWT/owner guards, source-qualified load, container/CI and historical HTTPS evidence.'],
    ],[157,342])
    heading('Rebuild and review status')
    paragraph('Install scripts/tests/requirements-report.txt, then run python scripts/tests/export_report.py. The exporter validates every indexed raw file, source/run identity, complete CI outcomes and evaluated Sonar conditions before publishing. It creates build/reports automatically; FRIDGELY_REPORT_OUTPUT can name a new nested folder. Follow-up figure data and dashboard images are embedded directly in this PDF.')
    paragraph('The retained failed initial ZAP setup is diagnostic evidence, not a passed test. Original course ZIP/PDF on the frozen delivery branch is unchanged. This corrected review copy requires independent review; no instructor approval, merge, production deployment or learn.bilgi upload is inferred from these results.')

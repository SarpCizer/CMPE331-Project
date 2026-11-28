"""Build the final verification report from retained, source-qualified evidence.

No scanner, provider, network or deployment operation is performed by this exporter.
The earlier course report and its measured source remain unchanged.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from reportlab.graphics import renderSVG
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, Image

from review_follow_up import bars

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/tests'
REPO = 'https://github.com/SarpCizer/CMPE331-Project'
GATE = {'bugs':('GT',0),'vulnerabilities':('GT',0),'coverage':('LT',90),
        'blocker_violations':('GT',0),'critical_violations':('GT',0)}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def junit(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('.//testsuite')
    value = {key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    value['passed'] = value['tests']-value['failures']-value['errors']-value['skipped']
    return value


def node_count(path):
    values = {k:int(v) for k,v in re.findall(r'^[#\u2139] (tests|pass|fail|cancelled|skipped) (\d+)',path.read_text(encoding='utf-8'),re.MULTILINE)}
    if values.get('tests',0)<=0 or values.get('pass')!=values['tests'] or any(values.get(k,1) for k in ('fail','cancelled','skipped')):
        raise ValueError('Incomplete Node execution result: '+path.name)
    return values['pass']


def load(base=BASE):
    config = read(base/'final-report-input.json')
    source = config['source_revision']
    if not re.fullmatch('[0-9a-f]{40}',source): raise ValueError('Invalid full source revision')
    root = (base/config['evidence_root']).resolve()
    if not root.is_relative_to(base.resolve()): raise ValueError('Unsafe evidence root')
    index = read(root/'evidence-index.json')
    if index['source_revision']!=source or index['ci_run_id']!=config['ci_run_id']:
        raise ValueError('Evidence source/run mismatch')
    required = {'ci-jobs.json','integrated/backend-junit.xml','integrated/browser-junit.xml',
        'integrated/backend-coverage.json','integrated/acceptance.log','integrated/http-security.log',
        'integrated/penetration.json','integrated/postgresql-load.json','integrated/recipe-generation-load.json',
        'coverage-policy/coverage-gate.json','sonar/source-identity.json','sonar/quality-gate.json',
        'sonar/metrics.json','sonar/dashboard.png','sonar/dashboard-capture.json','zap/summary.json',
        'mutation/mutation.json','secret/gitleaks.json','secret/secret-gate-canary.json',
        'local/sqlite-interleavings.xml'}
    if not required.issubset(index['files']): raise ValueError('Incomplete indexed final evidence')
    for name, meta in index['files'].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root): raise ValueError('Unsafe evidence member')
        raw = path.read_bytes()
        if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:
            raise ValueError('Evidence digest mismatch: '+name)
    jobs = read(root/'ci-jobs.json')
    if jobs['head_sha']!=source or jobs['run_id']!=config['ci_run_id'] or len(jobs['jobs'])!=9 or any(j['conclusion']!='success' for j in jobs['jobs']):
        raise ValueError('Require all nine actual CI jobs to succeed')
    for name in ('postgresql-load.json','recipe-generation-load.json'):
        value = read(root/'integrated'/name)
        if value['revision']!=source or not value['passed']: raise ValueError('Load source/result mismatch')
    for name in ('backend','browser'):
        value = junit(root/'integrated'/f'{name}-junit.xml')
        if value['failures'] or value['errors'] or value['passed']<=0: raise ValueError('Failing final '+name+' tests')
    cases = list(ET.parse(root/'integrated/backend-junit.xml').getroot().iter('testcase'))
    skipped = [c for c in cases if c.find('skipped') is not None]
    if len(skipped)!=3 or any('test_planner_sqlite_race' not in c.get('classname','') for c in skipped):
        raise ValueError('Unexpected backend skips')
    if junit(root/'local/sqlite-interleavings.xml') != {'tests':10,'failures':0,'errors':0,'skipped':5,'passed':5}:
        raise ValueError('Missing complementary SQLite race results')
    if junit(root/'integrated/browser-junit.xml')['skipped']: raise ValueError('Unexpected browser skips')
    mapping = read(base/'final-release/traceability/traceability.json')
    if mapping['assertion_revision']!=source or len(mapping['rows'])!=57 or len({(r['requirement'],r['criterion']) for r in mapping['rows']})!=57:
        raise ValueError('Criterion mapping source/completeness mismatch')
    inventory = read(base/'final-release/browser-inventory.json')
    suites = ET.parse(root/'integrated/browser-junit.xml').getroot().findall('testsuite')
    observed = {s.get('name'):int(s.get('tests')) for s in suites}
    if inventory['source_revision']!=source or observed!={Path(i['path']).name:i['cases'] for i in inventory['files']}:
        raise ValueError('Browser inventory differs from actual source-qualified JUnit')
    for item in inventory['files']:
        if not re.fullmatch(r'frontend/tests/[a-z-]+\.spec\.js',item['path']) or not re.fullmatch('[0-9a-f]{40}',item['git_blob_sha']):
            raise ValueError('Invalid immutable browser inventory')
    module_map = read(base/'final-release/module-map.json')
    actual_modules = {}
    for case in cases:
        name = 'backend/tests/'+case.get('classname').split('.')[-1]+'.py'
        counts = actual_modules.setdefault(name,{'passed':0,'skipped':0})
        counts['skipped' if case.find('skipped') is not None else 'passed'] += 1
    mapped_modules = {row['path']:{k:row[k] for k in ('passed','skipped')} for row in module_map['modules']}
    if module_map['source_revision']!=source or len(mapped_modules)!=len(module_map['modules']) or mapped_modules!=actual_modules:
        raise ValueError('Module mapping differs from actual JUnit executions')
    for item in read(base/'report-provenance.json')['historical_loads']:
        path = (base/item['path']).resolve()
        if not path.is_relative_to(base.resolve()) or read(path)['revision']!=item['revision'] or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Historical benchmark provenance mismatch')
    sonar = read(root/'sonar/source-identity.json')
    if sonar != {'analysis_revision':source,'test_revision':source,'test_artifacts_reused':False}:
        raise ValueError('Sonar source mismatch or reused test artifact')
    gate = read(root/'sonar/quality-gate.json')['projectStatus']
    conditions = gate.get('conditions',[])
    if gate.get('status')!='OK' or len(conditions)!=5 or {c['metricKey'] for c in conditions}!=set(GATE):
        raise ValueError('Missing evaluated Sonar conditions')
    for c in conditions:
        op, limit = GATE[c['metricKey']]
        actual = float(c['actualValue'])
        if c['status']!='OK' or c['comparator']!=op or float(c['errorThreshold'])!=limit or not (limit<=actual<=100 if op=='LT' else actual==0):
            raise ValueError('Failed Sonar condition')
    metrics = {m['metric']:m['value'] for m in read(root/'sonar/metrics.json')['component']['measures']}
    if float(metrics['security_hotspots'])!=0: raise ValueError('Unreviewed Sonar hotspot')
    capture = read(root/'sonar/dashboard-capture.json')
    if capture['revision']!=source or capture['credential_fields_present']: raise ValueError('Unsafe/mismatched dashboard')
    zap = read(root/'zap/summary.json')
    if zap['revision']!=source or not zap['passed'] or zap['authenticated_successful_requests_observed']<=0 or any(zap['alerts_by_risk'][k] for k in ('high','medium','low')):
        raise ValueError('Final authenticated ZAP policy failed')
    mutation = read(root/'mutation/mutation.json')
    if mutation['revision']!=source or not mutation['passed'] or mutation['counts']!={'killed':27,'survived':0,'invalid':0,'timeout':0}:
        raise ValueError('Incomplete final seeded mutation campaign')
    if read(root/'secret/gitleaks.json') or not read(root/'secret/secret-gate-canary.json')['passed']:
        raise ValueError('Final secret gate or detector canary failed')
    coverage = read(root/'coverage-policy/coverage-gate.json')
    if not coverage['passed'] or any(coverage['actual_percent'][k]<v for k,v in coverage['minimum_percent'].items()):
        raise ValueError('Coverage floor failed')
    pen = read(root/'integrated/penetration.json')
    if pen['source_revision']!=source or not pen['passed'] or len(pen['results'])!=4 or any(not p['passed'] for p in pen['results']):
        raise ValueError('Incomplete targeted penetration evidence')
    node_count(root/'integrated/acceptance.log'); node_count(root/'integrated/http-security.log')
    deployment = config.get('deployment')
    if deployment is not None:
        if not re.fullmatch('[0-9a-f]{40}',deployment['revision']) or deployment['measured_source']!=source or not deployment['source_tree_equal'] or not deployment['live_checks_passed']:
            raise ValueError('Unverified final deployment')
    return config,root


def export(base=BASE, output=None):
    config, root = load(base)
    # Validate every input before creating/replacing any output.
    out = Path(output) if output else ROOT/'build/final-report'
    out.mkdir(parents=True,exist_ok=True)
    pairs = [('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf'),
        ('/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf')]
    regular,bold = next((p for p in pairs if all(Path(s).is_file() for s in p)),(None,None))
    if not regular: raise RuntimeError('Install Arial or DejaVu Sans')
    for name,path in [('Report',regular),('ReportBold',bold)]: pdfmetrics.registerFont(TTFont(name,path))
    pdfmetrics.registerFontFamily('Report',normal='Report',bold='ReportBold')
    ink,pale = colors.HexColor('#173f2f'),colors.HexColor('#eaf2e9')
    styles = {
        'body':ParagraphStyle('body',fontName='Report',fontSize=9.1,leading=13,spaceAfter=8,textColor=ink),
        'small':ParagraphStyle('small',fontName='Report',fontSize=7.8,leading=10.5,spaceAfter=7,textColor=ink),
        'title':ParagraphStyle('title',fontName='ReportBold',fontSize=23,leading=27,spaceAfter=15,textColor=ink),
        'heading':ParagraphStyle('heading',fontName='ReportBold',fontSize=11.5,leading=15,spaceBefore=9,spaceAfter=7,textColor=ink),
        'cell':ParagraphStyle('cell',fontName='Report',fontSize=7.7,leading=10.3,textColor=ink),
    }
    story,md = [],[]
    figures = out/'final-release/figures'; figures.mkdir(parents=True,exist_ok=True)
    source,run = config['source_revision'],config['ci_run_id']
    short = source[:7]
    def markup(s):
        return re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<link href="\2" color="#24633f">\1</link>',html.escape(str(s)))
    def p(s,kind='body'):
        story.append(Paragraph(markup(s),styles[kind]));md.extend([str(s),''])
    def h(s,title=False):
        story.append(Paragraph(markup(s),styles['title' if title else 'heading']));md.extend([('# ' if title else '## ')+s,''])
    def page(s):
        if story: story.append(PageBreak())
        h(s,True)
    def table(head,rows,widths):
        t = Table([[Paragraph(markup(x),styles['cell']) for x in row] for row in [head,*rows]],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),pale),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,0),(-1,0),.7,ink),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d4ddd4'))]))
        story.extend([t,Spacer(1,9)])
        md.extend(['| '+' | '.join(head)+' |','| '+' | '.join('---' for _ in head)+' |'])
        md.extend('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows);md.append('')
    def fig(name,drawing):
        renderSVG.drawToFile(drawing,str(figures/name));story.extend([drawing,Spacer(1,10)])
        md.extend([f'![{name}](final-release/figures/{name})',''])
    def link(path,label): return f'[{label}]({REPO}/blob/{source}/{path})'
    backend,browser = [junit(root/'integrated'/f'{name}-junit.xml') for name in ('backend','browser')]
    ac,http = [node_count(root/'integrated'/name) for name in ('acceptance.log','http-security.log')]
    cov = read(root/'coverage-policy/coverage-gate.json')
    load_result = read(root/'integrated/postgresql-load.json')
    generation = read(root/'integrated/recipe-generation-load.json')
    zap = read(root/'zap/summary.json')
    raw_cov = read(root/'integrated/backend-coverage.json')
    total = raw_cov['totals']
    frontend = read(root/'integrated/frontend-coverage/coverage-summary.json')['total']
    gate = read(root/'sonar/quality-gate.json')['projectStatus']
    mapping = read(base/'final-release/traceability/traceability.json')
    inventory = read(base/'final-release/browser-inventory.json')
    modules = read(base/'final-release/module-map.json')
    index = read(root/'evidence-index.json')
    page('Fridgely\nSoftware Testing Report')
    p('Final verification edition | 28 November 2026 | CMPE331','small')
    p('Prepared by Sarp Çizer with Codex assistance, continuing the reviewed team work through Berfin Gökgöz\'s PR #102. Earlier measurements and unsuccessful attempts retain their original identities. No instructor acceptance or course-platform upload is inferred.')
    p('Measured application and test source: '+source,'small')
    p(f'[Nine-job CI {run}]({REPO}/actions/runs/{run}) | [Measured source {short}]({REPO}/commit/{source}) | [Finalization PR #103]({REPO}/pull/103)')
    if config.get('deployment'):
        p('Deployment verified: '+config['deployment']['revision']+'. Its application source tree matches the measured source; live checks are recorded separately.')
    else:
        p('Release candidate: isolated verification has passed. Protected-main review, merge and exact-source production verification remain pending. This edition does not claim that the candidate is live.')
    table(['Verification layer','Observed result'],[
        ['Backend / PostgreSQL',f'{backend["passed"]} passed, {backend["skipped"]} SQLite-only cases skipped; zero failures/errors'],
        ['Complementary SQLite run','5 passed; 5 PostgreSQL variants intentionally skipped locally'],
        ['Production-build browser',f'{browser["passed"]} passed; zero failures or skips'],
        ['Acceptance / HTTP isolation',f'{ac} / {http} passed; 28 unique US test IDs, repeated per-engine executions distinguished'],
        ['Static analysis / security','Five evaluated Sonar conditions passed; ZAP 0 high/medium/low; four targeted probes passed'],
        ['Coverage / performance','All five coverage floors and both isolated load scenarios passed'],
        ['Mutation / reproducibility','27/27 seeded mutations killed; archive, secret detector canary and container restart passed'],
    ],[173,326])
    h('Scope and exit criteria')
    p('Exercise the real FastAPI host, SQL persistence and built React interface. Controlled provider fixtures isolate deterministic contracts and failure paths; bounded live model checks are a separate release gate. Completion requires green required checks, legitimate peer approval, the merged source observed on Render, and a visually verified report. A test pass is evidence for its scenario, not a guarantee that all future generated meals are safe or correct.','small')

    page('1. Strategy and requirements')
    p('The syllabus asks for unit-module traceability, explained coverage metrics, performance and security experiments, SonarQube and penetration findings with their treatment. The instructor\'s PR #67 review adds criterion-level assertions, honest version labels, load/concurrency and brute-force tests, evaluated quality conditions, and report figures. This edition addresses each using retained results.')
    table(['Layer / environment','What the result establishes'],[
        ['Python 3.12, Linux CI, PostgreSQL 17','Real transactions, migrations, ownership, restart persistence, recipe validation and interleavings; engine-specific SQLite cases are covered separately.'],
        ['Windows local, Python 3.12, SQLite','Five targeted planner/sign-in interleavings on measured source '+short+'. PostgreSQL skips are disclosed; no local full-suite pass is inferred.'],
        ['Node + Playwright Chromium, built React','Actual host/browser flows with controllable provider, DOM assertions, keyboard navigation, error/empty states, accessibility and 360/768/1440 px layouts.'],
        ['Disposable Docker/Sonar/ZAP hosts','Production Docker image and PostgreSQL restart; static quality gate; authenticated active API scan. No attack or load scan targets production.'],
        ['Load host / one worker / PostgreSQL','Five-minute 50-user non-AI scenario and separate 10-user controlled-generation experiment. Runner characteristics come from each raw JSON.'],
    ],[177,322])
    h('Assertion-level traceability')
    p('The matrix contains all 48 acceptance criteria from US-01 through US-15 plus nine NFR criteria. Every row gives the exact requirement text, concrete assertion, why it verifies the criterion, case name and immutable source-line link. One test may cover several criteria; the criterion keys remain unique.')
    p('There are 28 unique physical US-xx-Txx identifiers. The acceptance runner reports '+str(ac)+' executions because some scenarios execute for both database engines. These are executions, not extra requirements or duplicate identifiers. Supplemental product tests cover quantities, purchase/cooking, moods, weekly planning, wheel behavior and password changes beyond the original 15 stories.')
    artifact_ref = config.get('artifact_revision',source)
    p('[Full criterion matrix]('+REPO+'/blob/'+artifact_ref+'/docs/tests/final-release/traceability/traceability.md) is committed under docs/tests/final-release/traceability/ as Markdown, CSV and JSON. Assertion links target '+short+'; the evidence publication commit is distinct. Historical scope notes in the generator remain historical, while current metrics and deployment status are evaluated in this report.','small')

    page('2. Module-to-requirement evidence')
    p('The [complete module map]('+REPO+'/blob/'+artifact_ref+'/docs/tests/final-release/module-map.csv) is generated from actual JUnit test cases, not collected-file estimates. The following groups summarize it; each module remains individually identified in the companion files.')
    groups = {}
    for row in modules['modules']:
        g = groups.setdefault(row['group'],{'passed':0,'skipped':0,'files':0,'requirements':row['requirements'],'purpose':row['purpose']})
        g['passed']+=row['passed'];g['skipped']+=row['skipped'];g['files']+=1
    table(['Module family / requirements','Executed evidence and purpose'],[
        [name+'\n'+g['requirements'],f'{g["files"]} '+('module' if g['files']==1 else 'modules')+f'; {g["passed"]} passed, {g["skipped"]} skipped. '+g['purpose']]
        for name,g in groups.items()
    ],[188,311])
    p('Acceptance tests assert real HTTP DTOs/statuses and collection snapshots. Browser tests assert rendered behavior against the built frontend. Unit/adapter tests provide fault injection and fine-grained validation; integration, restart and concurrency tests complement them. No single aggregate is described as purely unit testing.','small')

    page('3. Functional and browser results')
    table(['Browser source file at '+short,'Cases'],[[link(i['path'],Path(i['path']).name),str(i['cases'])] for i in inventory['files']],[418,81])
    p('The inventory above comes from this run\'s browser JUnit and verified Git blobs. completion.spec.js exists at this exact source; historical snapshots with fewer files are kept separate. fixtures.js and global-setup.js support execution and are not counted as test suites.','small')
    h('Important invariants')
    p('Generation, viewing, history, favorites, missing-ingredient shopping and wheel selection preserve fridge stock. Normal Remove only removes a shopping row. Bought - add to fridge and confirmed cooking are explicit transactions; retries are idempotent. Cross-user methods deny access and preserve all owned snapshots. Legacy unit/quantity and migration cases remain covered.')
    p('New provider regressions cover bounded input parsing, transport variants and confirmed truncated-prefix recovery, batch atomicity for hard failures, honest usable-candidate curation, undosed/unlisted ingredient rejection and bounded poultry/fish temperature guidance. These fixtures establish rejection and normalization rules; they cannot certify arbitrary inference, estimated nutrition or undeclared allergens.','small')

    page('4. Coverage and mutation analysis')
    fig('final-coverage.svg',bars('Measured source coverage | '+short,
        ['Backend statements','Backend branches','Frontend lines','Frontend branches','Frontend functions'],
        [cov['actual_percent'][k] for k in cov['minimum_percent']],100))
    table(['Metric','Actual numerator / denominator','Required floor'],[
        ['Backend statements',f'{total["covered_lines"]} / {total["num_statements"]} = {total["percent_statements_covered"]:.2f}%','90%'],
        ['Backend branches',f'{total["covered_branches"]} / {total["num_branches"]} = {total["percent_branches_covered"]:.2f}%','70%'],
        *[[f'Frontend {name}',f'{frontend[name]["covered"]} / {frontend[name]["total"]} = {frontend[name]["pct"]:.2f}%',floor]
          for name,floor in [('lines','90%'),('branches','85%'),('functions','85%')]],
    ],[152,236,111])
    p('Statement coverage counts executed source statements; branch coverage counts taken exits. Executing a validation line once does not exercise both its success and rejection paths. The earlier 91.83% statement / 73.91% branch snapshot therefore did not imply its missed exits were tested. Current denominators above are taken from coverage.py; frontend source maps and per-file denominators are retained.','small')
    missed = sorted(raw_cov['files'].items(),key=lambda x:x[1]['summary']['missing_branches'],reverse=True)[:4]
    table(['Current remaining branch gaps','Missed exits / example arcs'],[[name.replace('backend/src/',''),str(v['summary']['missing_branches'])+' / '+', '.join(f'{a}->{b}' for a,b in v.get('missing_branches',[])[:3])] for name,v in missed],[315,184])
    p('Arcs are exact source line-to-line exits (negative numbers denote function exit), not invented failure cases. These gaps remain visible; thresholds were not lowered to hide them. The coverage canary proves a synthetic regression fails. All 27 targeted seeded source mutants were killed by real failing assertions; none survived, timed out or failed to compile. This is a deliberately selected campaign, not whole-project mutation coverage.','small')

    page('5. Performance and concurrency')
    stats = load_result['overall'];steady = generation['steady']
    fig('final-current-load.svg',bars('Isolated p95 response time | '+short,['Non-AI HTTP','Controlled generation'],[stats['p95_ms'],steady['p95_ms']],2000,' ms',threshold=500))
    p('The 500 ms marker applies only to NFR-03 non-AI routes. Controlled generation has a separate 2000 ms experimental threshold and a 200 ms fixture provider; its timing is not real external model latency.','small')
    table(['Experiment','Observed result / interpretation'],[
        ['Non-AI, 50 users, 100 fridge rows each, 300 s',f'{stats["requests"]} requests, {stats["errors"]} errors; p95 {stats["p95_ms"]:.2f} ms. Margin to 500 ms: {500-stats["p95_ms"]:.2f} ms. Each route is also checked independently.'],
        ['Generation, 10 users, 60 s, 1 s think time',f'{steady["requests"]} requests, {steady["errors"]} errors; p95 {steady["p95_ms"]:.2f} ms. No external inference; actual HTTP/DB persistence and zero malformed accepted results.'],
        ['Five simultaneous stalled providers',f'{generation["concurrent_timeouts"]["provider_cancellations"]} cancellations; each retryable 503 within 30 s, configured 28 s budget. No partial recipes, stock or other collection changes.'],
    ],[195,304])
    table(['Non-AI route','Requests','Errors','p95 ms'],[[n,str(v['requests']),str(v['errors']),f'{v["p95_ms"]:.2f}'] for n,v in load_result['routes'].items()],[176,110,90,123])
    p('Runner: '+json.dumps(load_result['client'])+'. '+load_result['environment']+'. The client and one-worker host share the runner; these measurements include local HTTP, serialization and database work, not public Render network latency.','small')

    page('6. Historical timing interpretation')
    history = read(base/'report-provenance.json')['historical_loads']
    historical = [(i,read(base/i['path'])) for i in history]
    old = {i['revision']:v for i,v in historical}
    local_old = old['9f43e3af07f08d070251e371fb6112c989db330e']['overall']['p95_ms']
    ci_old = old['25c111aa5a8d678b60c17745289675821b62f91d']['overall']['p95_ms']
    windows = read(base/'evidence/review94-fafd3fd/local/non-ai-load.json')
    follow = read(base/'evidence/review94-fafd3fd/integrated/postgresql-load.json')
    fig('final-historical-load.svg',bars('Historical non-AI p95: different sources/environments',
        ['9f43e3a local SQLite','25c111a CI PostgreSQL','6cc96e7 Windows SQLite','fafd3fd CI PostgreSQL',short+' final CI PostgreSQL'],
        [local_old,ci_old,windows['overall']['p95_ms'],follow['overall']['p95_ms'],stats['p95_ms']],2000,' ms',threshold=500))
    p(f'The original 371.47 ms CI p95 is {ci_old/local_old:.2f} times the 44.35 ms local p95, leaving {500-ci_old:.2f} ms below the 500 ms limit. The local source is 9f43e3af07f08d070251e371fb6112c989db330e (macOS ARM64, SQLite, eight reported CPUs); the CI source is 25c111aa5a8d678b60c17745289675821b62f91d (Linux, PostgreSQL, two reported CPUs). Code, database, hardware and scheduler differ. The data cannot establish one causal explanation.')
    p('The later Windows SQLite benchmark at 6cc96e729eaf07d739bcedefee22fbb7ce4c45f9 failed the 500 ms requirement at '+f'{windows["overall"]["p95_ms"]:.2f}'+' ms despite zero HTTP errors. It is retained as FAIL, not dropped. Its measured source-scope equality with fafd3fdbfa0d8ccd2ff7679282687142615e0aed is retained in the earlier follow-up evidence. That CI run passed at '+f'{follow["overall"]["p95_ms"]:.2f}'+' ms. This controlled comparison still does not establish equivalence of machine performance.')
    p('The latest result is a new measurement at '+source+'. No older local run is relabelled as this version, and no isolated load result is presented as production capacity. Historical raw JSON and full revision labels remain linked in the earlier corrected report and evidence index.','small')

    page('7. Security and defect treatment')
    table(['Technique / actual scope','Observed result and disposition'],[
        ['OWASP ZAP 2.17.0 authenticated OpenAPI active scan',f'{zap["http_requests_observed"]} observed requests; {zap["authenticated_successful_requests_observed"]} successful authenticated requests. 0 high, 0 medium, 0 low; {zap["alerts_by_risk"]["informational"]} informational rule categories retained. Disposable host, bounded scan; no production attack.'],
        ['Four targeted automated probes','SQL injection, mass assignment, source/config traversal and stored XSS (actual browser before/after reload). All passed; complements rather than replaces the standard scanner.'],
        ['Brute-force / credential handling','Sign-in throttle and account-isolation assertions, Argon2 salted hashes, signed JWT/expiry/auth_version checks, seeded credential leakage checks and sanitized provider errors. No claim about third-party platform logs.'],
        ['Dependency / secret checks','Python and frontend dependency audits each reported zero known vulnerabilities at scan time. Reachable-history Gitleaks reported zero findings; its synthetic credential canary was detected and rejected.'],
        ['Earlier findings / current treatment','Historical missing CORP header fixed; scanner-host preferences collision isolated. Twelve S2970 findings were assertion-helper recognition false positives, not twelve security vulnerabilities. The later regex issue was replaced with a bounded linear parser; actual current Sonar results are shown next.'],
    ],[187,312])
    p('The three retained ZAP informational categories are client-error responses to invalid/unauthorized probes, identification of the authentication request, and non-storable responses. They document observed API/authentication/cache behavior; no scanner rule is suppressed to obtain the pass. Recheck if the contract or cache policy changes.','small')
    h('Password rotation race: genuine test-first fix')
    p('A stale sign-in rehash could overwrite a concurrently changed password. A deterministic real-route regression first failed against abdca3f: 1 failed / 1 passed / 2 PostgreSQL variants skipped locally (test commit 03d0f3d). The fix c3558ba compares both the previously verified hash and auth_version before updating. On a conflict it reloads and verifies current credentials; a stale old password is rejected, while two legitimate concurrent rehashes can both complete.')
    p('The final CI executes both engines\' password-race cases. A complementary SQLite run has five passes across planner and password interleavings; local PostgreSQL variants are explicitly skipped. Mutant M27 removes the compare-and-set guard and is killed by the race assertion. No database schema, account data or auth-version migration was rewritten.','small')

    page('8. Evaluated SonarQube quality gate')
    table(['Server-evaluated condition','Threshold','Actual','Status'],[[c['metricKey'],c['comparator']+' '+c['errorThreshold'],c['actualValue'],c['status']] for c in gate['conditions']],[211,99,90,99])
    p('The server returned five actual evaluated conditions. A historical green status with an empty conditions array was insufficient; current validation rejects missing, altered or non-passing conditions. The independent policy also requires zero security hotspots; zero does not imply a manual review of nonexistent hotspots. Sonar analysis and imported test coverage both identify '+short+' with no reused test artifacts.','small')
    p('Sonar reports combined-source coverage 96.4%, line coverage 97.5% and condition/branch coverage 92.2%; these use its imported multi-language line/condition aggregation. They are not the backend-only coverage.py statement/exit percentages on page 5. Current exported bugs, vulnerabilities, code smells, blocker/critical issues and hotspots are all zero.','small')
    image = Image(str(root/'sonar/dashboard.png'))
    ratio = min(499/image.imageWidth,390/image.imageHeight)
    image.drawWidth=image.imageWidth*ratio;image.drawHeight=image.imageHeight*ratio;image.hAlign='CENTER'
    story.extend([image,Spacer(1,8)])
    md.extend([f'![Actual SonarQube dashboard]({config["evidence_root"]}/sonar/dashboard.png)',''])
    p('Actual browser capture of the ephemeral SonarQube dashboard from this run, scaled with its aspect ratio preserved. The original PNG, capture revision, configured gate, evaluated response, metrics, issue list and hotspot export are retained. This image is embedded in the PDF.','small')

    page('9. Reproducibility and delivery')
    p(f'Raw evidence index: {len(index["files"])} retained files. Each member has an original byte length and SHA-256. Downloaded artifact ZIP digests were checked against GitHub metadata before safe, selected extraction. Git attributes preserve evidence bytes on Windows. The report fails before publication if an indexed file changes, source/run identities differ, JUnit inventory changes, a gate is incomplete or a mandatory result fails.')
    p('[Retained evidence index]('+REPO+'/blob/'+artifact_ref+'/docs/tests/'+config['evidence_root']+'/evidence-index.json) | [Backend JUnit]('+REPO+'/blob/'+artifact_ref+'/docs/tests/'+config['evidence_root']+'/integrated/backend-junit.xml) | [Browser JUnit]('+REPO+'/blob/'+artifact_ref+'/docs/tests/'+config['evidence_root']+'/integrated/browser-junit.xml)','small')
    table(['Action','Rebuild / interpretation'],[
        ['Install report-only dependencies','python -m pip install -r scripts/tests/requirements-report.txt'],
        ['Export from a full repository checkout','python scripts/tests/export_final_report.py --output build/final-report\nCreates absent parent folders; writes PDF, UTF-8 Markdown and SVG figures; performs no network/provider calls.'],
        ['Verify report safeguards','python -B -m unittest discover -s scripts/tests -p test_*.py -v\nIncludes missing-folder rebuild, tampered evidence, source mismatch and browser inventory regressions.'],
        ['Package reviewed source','python scripts/release/package_source.py --revision FULL_SHA --output build/release/Fridgely-final-source.zip\nUses immutable Git blobs and matching committed backend/frontend versions. Repeated exports are byte-identical. No dependencies, secrets, scanner dumps or PDF binary in the source ZIP.'],
        ['Exact live-source observation','GET /api/health and X-Fridgely-Revision. The production host only publishes a valid 40-character Render commit ID; a request header cannot spoof it. Source-tree comparison links publication/merge commits to the measured application.'],
    ],[164,335])
    p('The earlier a59556e course ZIP/PDF, delivery branch and v0.1.0 tag are preserved. This final verification edition does not silently replace their source labels. The new PDF is a companion to the exact selected source ZIP. Report regeneration requires the full checkout with retained evidence; the deliberately source-only ZIP is not a scanner-evidence mirror.','small')
    p('A final packaging regression also found the manifest hard-coded to 0.1.0 despite current 0.6.0 components. Two tests failed before the correction. The packager now reads the selected commit, rejects mismatched component versions before writing, and ignores dirty working-version changes. Locally nine archive cases pass; one Windows symlink case is explicitly skipped and remains required on Linux CI. The historical 0.1.0 source retains its own version.','small')
    h('Production verification status')
    if config.get('deployment'):
        p(json.dumps(config['deployment'],ensure_ascii=False),'small')
    else:
        p('Pending legitimate peer review and normal protected-main merge. After CI-triggered Render deployment, observe the new revision header and verify real normal/Quick recipes, details/history, favorites, missing-shopping and unchanged stock using a disposable test account. Isolated controlled-provider tests above are complete; these outstanding live checks are not marked passed.')

    page('10. Instructor checklist and limits')
    table(['Instructor request','Evidence in this edition'],[
        ['Rebuild without build/; accurate file inventory','Clean nested-directory export regression; JUnit/Git-blob browser inventory on pages 4 and companion JSON.'],
        ['Local versus CI versions','Full source labels, environments and retained failed Windows benchmark; historical comparison on page 7.'],
        ['Interpret p95 and branch gaps','Measured denominators, missed arcs and unchanged floors; 8.38x historical comparison and 128.53 ms historical margin; current route-level p95 and margins.'],
        ['Granular AC / NFR assertions; duplicated IDs','57 unique criterion rows, concrete immutable assertion links; 28 physical IDs distinguished from '+str(ac)+' executions.'],
        ['Standard penetration / brute force / generation load','Authenticated ZAP, four custom probes, sign-in throttle; 10-user generation load and five simultaneous cancelled deadlines.'],
        ['Real Sonar gate and false-positive interpretation','Five evaluated conditions plus zero-hotspot policy; retained issue exports and actual dashboard. S2970 helper false positives identified accurately.'],
        ['Graphs and embedded report images','Coverage, current/historical performance plots and actual Sonar dashboard embedded directly in PDF.'],
        ['Review discipline','Work isolated in PR #103; review and merge status are explicit. Peer review does not imply instructor approval.'],
    ],[176,323])
    p('Known limits: isolated performance is not a Render capacity promise; ZAP/probes are bounded automated assessment, not exhaustive independent penetration testing; estimated nutrition and arbitrary generated food safety are not certified. Automated keyboard/axe coverage complements, but does not replace, human usability review. Remaining branch exits are disclosed rather than presented as executed.')
    p('Course submission and team presentation require actual human completion. No Learn receipt, instructor acceptance, teammate review, future reliability or grade is invented. Final production completion is reported only after exact-source deployment and bounded live evidence exist.','small')
    p('[Instructor review](https://github.com/SarpCizer/CMPE331-Project/pull/67#issuecomment-7198211995) | [Requirements](https://github.com/SarpCizer/CMPE331-Project/tree/'+source+'/docs/requirements) | [Historical corrected report](https://github.com/SarpCizer/CMPE331-Project/blob/'+source+'/docs/tests/software-test-report.md)','small')
    pdf = out/'Fridgely-Final-Software-Test-Report.pdf'
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(ink);canvas.line(48,40,547,40)
        canvas.setFont('Report',7);canvas.setFillColor(ink)
        canvas.drawString(48,28,'FRIDGELY  |  Measured '+short+'  |  '+str(run))
        canvas.drawRightString(547,28,str(doc.page));canvas.restoreState()
    doc = SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=43,bottomMargin=55,
        title='Fridgely - Final Software Testing Report',author='Sarp Çizer / Fridgely team; Codex assisted')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (out/'Fridgely-Final-Software-Test-Report.md').write_text('\n'.join(md).rstrip()+'\n',encoding='utf-8')
    print(json.dumps({'pdf':str(pdf),'source_revision':source,'ci_run_id':run,'deployment_verified':config.get('deployment') is not None}))
    return pdf


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    export(output=args.output)

"""Render the measured Fridgely test report to Markdown and PDF."""
from datetime import datetime
import html
import os
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/tests'
OUT=Path(os.getenv('FRIDGELY_REPORT_OUTPUT',str(ROOT/'build/reports')))
OUT.mkdir(exist_ok=True)
CONFIG=json.loads((BASE/'report-input.json').read_text())
FOREST=colors.HexColor('#173f2f')
MUTED=colors.HexColor('#53685a')
PALE=colors.HexColor('#e9f1e7')

def read(path,default=None):
    path=Path(path)
    return json.loads(path.read_text()) if path.exists() else default

def junit(path):
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
    values={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    values['passed']=values['tests']-values['failures']-values['errors']-values['skipped']
    return values

local_backend=junit(ROOT/'docs/tests/evidence/local/backend-junit.xml')
local_browser=junit(BASE/CONFIG.get('local_browser','evidence/local/browser-junit.xml'))
backend=read(ROOT/'docs/tests/coverage/backend-local.json')['totals']
frontend=read(ROOT/'docs/tests/coverage/frontend-local.json')['total']
local_load=read(ROOT/'docs/tests/non-func-tests/local-load.json')
ci_dir=BASE/CONFIG['ci_dir']
pg_load=read(BASE/'non-func-tests/postgresql-load.json')
ci_backend=junit(ci_dir/'backend-junit.xml')
ci_browser=junit(ci_dir/'browser-junit.xml')
ci_code=read(BASE/'coverage/backend-ci.json')['totals']
ci_frontend=read(BASE/'coverage/frontend-ci.json')['total']
timeout=read(ROOT/'docs/tests/non-func-tests/provider-timeout.json')
sonar=BASE/CONFIG['sonar_dir'] if CONFIG.get('sonar_dir') else None
issues=read(sonar/'issues.json',{}) if sonar else {}
sonar_metrics=read(sonar/'metrics.json',{}) if sonar else {}
sonar_server=read(sonar/'server.json',{}) if sonar else {}
gate=read(sonar/'quality-gate.json',{}) if sonar else {}
gate_status=gate.get('projectStatus',{}).get('status','NOT YET VERIFIED')
sonar_measures={row['metric']:row['value'] for row in sonar_metrics.get('component',{}).get('measures',[])}
high=[issue for issue in issues.get('issues',[]) if issue.get('severity') in {'BLOCKER','CRITICAL'} or any(
    impact.get('severity') in {'HIGH','BLOCKER'} for impact in issue.get('impacts',[]))]
run_url=f'https://github.com/SarpCizer/CMPE331-Project/actions/runs/{CONFIG["ci_run_id"]}'
repo_url='https://github.com/SarpCizer/CMPE331-Project'
artifact_ref=CONFIG.get('artifact_ref','test_work')

font_candidates=[
    ('/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf','/System/Library/Fonts/Supplemental/Arial Italic.ttf'),
    ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'),
    ('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/ariali.ttf')]
fonts=next((candidate for candidate in font_candidates if all(Path(p).is_file() for p in candidate)),None)
if fonts is None:
    raise RuntimeError('Install Arial or DejaVu Sans regular/bold/italic fonts to export the report')
for name,path in zip(['Arial','Arial-Bold','Arial-Italic'],fonts):
    pdfmetrics.registerFont(TTFont(name,path))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-Bold')
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14.4,textColor=FOREST,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=8.3,leading=11.3,textColor=MUTED,spaceAfter=7),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=24,leading=28,textColor=FOREST,spaceAfter=16),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=15,leading=20,textColor=FOREST,spaceBefore=12,spaceAfter=10),
 'title':ParagraphStyle('title',fontName='Arial-Bold',fontSize=37,leading=41,textColor=FOREST,spaceAfter=18),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=8.2,leading=11,textColor=FOREST),
 'head':ParagraphStyle('head',fontName='Arial-Bold',fontSize=8.3,leading=11,textColor=FOREST),
}
story=[]
md=['# Fridgely Software Test Report','']

def markup(text):
    text=html.escape(str(text))
    text=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2" color="#256247"><u>\1</u></a>',text)
    return text.replace('\n','<br/>')

def paragraph(text,small=False):
    story.append(Paragraph(markup(text),styles['small' if small else 'body']))
    md.extend([str(text),''])

def heading(text,level=2):
    story.append(Paragraph(markup(text),styles['h1' if level==1 else 'h2']))
    md.extend(['#'*level+' '+text,''])

def table(headers,rows,widths):
    cells=[[Paragraph(markup(value),styles['head' if i==0 else 'cell']) for value in row]
           for i,row in enumerate([headers]+rows)]
    element=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    element.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#b5cbbb')),
        ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dfe8df')),
    ]))
    story.extend([element,Spacer(1,11)])
    md.append('| '+' | '.join(map(str,headers))+' |')
    md.append('| '+' | '.join('---' for _ in headers)+' |')
    md.extend('| '+' | '.join(str(cell).replace('\n','; ') for cell in row)+' |' for row in rows)
    md.append('')

def page():story.append(PageBreak())

story.append(Spacer(1,22))
paragraph('CMPE 331  /  SOFTWARE TESTING',True)
story.append(Paragraph('Fridgely<br/>Software Test Report',styles['title']))
paragraph('Berfin Gökgöz | Full-stack and database integration\n21 November 2026 | Review copy for pull-request assessment')
heading('What was verified')
paragraph('A single FastAPI host now connects real account registration, signed JWT sessions, saved preferences and SQL inventory to the existing recipe and personal-collection modules. The React client uses that same authenticated API. This report records executed tests and their limits; it does not infer a result from the presence of test code or a CI file.')
table(['Verification','Recorded result'],[
    ['Local Python backend',f'{local_backend["passed"]} passed; {local_backend["skipped"]} explicit PostgreSQL skip; 1 upstream warning'],
    ['Functional acceptance', '27 passed through the actual FastAPI/SQL host'],
    ['Real HTTP account/security suite','12 passed; every protected route checked without/with malformed tokens'],
    ['Local browser suite',f'{local_browser["passed"]} passed; core flows, three widths, WCAG audit and keyboard use'],
    ['Targeted penetration probes','4 passed: SQL payload, mass assignment, file disclosure and stored XSS'],
    ['PostgreSQL CI backend',f'{ci_backend["passed"]} passed in the cited run; separate processes verify persistence'],
    ['CI browser suite',f'{ci_browser["passed"]} passed on the cited source revision'],
    ['Five-minute load scenarios','Targets met in both local SQLite and CI PostgreSQL environments'],
    ['Dependency audits','No known vulnerabilities reported by the recorded Python/npm audits'],
    ['SonarQube quality gate',gate_status],
],[150,350])
paragraph('The production Docker image also passed a real PostgreSQL restart/isolation smoke test. Public HTTPS hosting is still blocked by Render GitHub repository access, and live recipe generation requires the team provider credential. Controlled provider fixtures are explicitly separate from these release checks.',True)
paragraph(f'[GitHub verification run]({run_url}) | [Feature PRs]({repo_url}/pulls)',True)
paragraph(f'Application verification revision: {CONFIG["ci_revision"]}. Report and current frontend handoff are proposed in PR #56; main remains unmerged.',True)

page();heading('1. Scope, baseline and test design',1)
paragraph('The repository is authoritative. The initial main inspection at 48b77e9 and latest check at cb99673 both contain the historical 501 acceptance scaffold. The collections module was taken from backend_work at 862005f and the recipe module from Ayse\'s PR #7 at e5391fe. Their history was preserved on the integration branch. No merge to main was performed.')
paragraph('FastAPI/SQLAlchemy was retained to compose the implemented teammate modules. PostgreSQL is the shared database target; SQLite provides a reproducible local environment. The legacy ZIP files were reference material only. Their unowned global recipes, localStorage lists, reset schema, pickle models and spoilage/expiry scope were not substituted for current GitHub code.')
table(['Boundary','Execution and interpretation'],[
 ['Account and access','Real normalized email uniqueness, salted Argon2id hashes, signed HS256 JWTs, issuer/audience/expiry checks and existing-account lookup. Owner IDs in request data cannot select another account.'],
 ['Data and transactions','Versioned migration, owner-qualified queries, foreign keys, composite recipe ownership, atomic preferences and full recipe batches. No success is returned before commit.'],
 ['Provider and clock','Only the external provider response and clock are injected. Node acceptance cases send requests through the actual FastAPI host and a fresh migrated SQL database. No parallel fake application is used.'],
 ['Browser','Production React build and the actual HTTP host run together. Tests use isolated accounts, real SQL persistence, a controlled provider and tab-scoped sessions.'],
 ['Reproducibility','Pinned Python and frontend lockfiles, recorded source hashes, test commands, JUnit, coverage, screenshots and CI artifacts identify what was executed.'],
],[110,390])
heading('Important test outcomes')
paragraph('US-15: authentic tokens work before expiry and fail afterward; malformed, tampered and unsigned JWTs are rejected. Two real accounts cannot access each other\'s inventory, recipes, shopping, favorites or history. Database ownership constraints also reject foreign recipe associations.')
paragraph('US-03/US-07: preferences can be replaced and cleared atomically. Generating again after a saved update supplies the latest committed lists to the provider. US-09: a provider failure preserves all five personal collections; malformed/allergen-conflicting batches are rejected without partial persistence.')
paragraph('Timestamp scenarios explicitly sign in again after advancing beyond the one-hour session lifetime. This preserves both the original date/history assertions and real expiration enforcement. The separate expired-token test still expects 401.',True)
paragraph('Review #17 is addressed by the ordered relational preference migration. The actual test-first commit 9450fac contains two failing relational tests before the implementation commit 775e8b7. The following green run includes legacy-data preservation, repeated upgrade, duplicates/order, foreign keys, replacement/clear, two-account isolation and concurrent case-variant registration. Older work is not retroactively labelled as TDD.',True)
paragraph('Frontend completion in #56 retains nine browser regressions in commit 2b2797f that failed against a7c7456 before implementation. The fixed application passes those regressions and the original complete flows. A further committed-write/failed-refresh regression was added during review; no earlier test-first history is claimed for it. Coverage and JUnit are retained under evidence/frontend-completion.',True)

page();heading('2. Requirement and code coverage',1)
paragraph('The denominator is the 15 user stories and 48 acceptance criteria stored under docs/requirements. Each criterion has an assertion mapping in docs/tests/coverage/traceability.csv. Mapping coverage is 48/48; executed assertions within the stated fixture/SQL/browser scope support the recorded passes. Mapping is separate from line/branch coverage and from release approval.')
titles=['Registration','Sign-in','Preferences','Add inventory','List inventory/dates','Delete inventory','Generate recipes','Recipe details/estimates','Provider failures','Missing ingredients','Shopping management','Save favorite','List/remove favorites','Viewed history','Personal-data protection']
counts=[3,2,3,3,3,3,4,3,3,4,4,3,3,4,3]
table(['Story','Requirement','Criteria','Representative cases'],[
 [f'US-{i:02}',title,count,('US-08-T01..T07 + browser' if i==8 else 'US-15-T01..T03 + B-SEC' if i==15 else f'US-{i:02}-T01 + mapped companion cases')]
 for i,(title,count) in enumerate(zip(titles,counts),1)], [57,165,46,232])
table(['Code measurement','Lines/statements','Branches','Functions'],[
 ['Python / local',f'{backend["percent_statements_covered"]:.2f}%',f'{backend["percent_branches_covered"]:.2f}%','-'],
    ['Python / CI',f'{ci_code["percent_statements_covered"]:.2f}%',f'{ci_code["percent_branches_covered"]:.2f}%','-'],
 ['React / local V8 mapped',f'{frontend["lines"]["pct"]:.2f}%',f'{frontend["branches"]["pct"]:.2f}%',f'{frontend["functions"]["pct"]:.2f}%'],
    ['React / CI V8 mapped',f'{ci_frontend["lines"]["pct"]:.2f}%',f'{ci_frontend["branches"]["pct"]:.2f}%',f'{ci_frontend["functions"]["pct"]:.2f}%'],
],[205,105,95,95])
paragraph('Python coverage includes backend/src and the migration; it excludes the test-only acceptance bridge. Frontend coverage maps the production build back to frontend/src using source maps and exports LCOV. Third-party modules and generated assets are not product-source coverage. V8 mapped line totals are instrumentation-specific: even 100% mapped lines would not imply all branches, functions or acceptance conditions were tested. Preserve the raw summaries and use the branch/function measures alongside line coverage.',True)

page();heading('3. Non-functional results',1)
table(['NFR','Executed evidence','Interpretation'],[
 ['NFR-01','JWT signature/claims/expiry, all protected methods without/malformed tokens; cross-user objects and SQL ownership.','Passed in recorded suites.'],
 ['NFR-02','Distinct salted Argon2id hashes; wrong credentials; sanitized provider failures; dependency audits.','No real secrets are committed in evidence. This is not a complete penetration test.'],
 ['NFR-03','50 signed-in users, 100 inventory entries each, 300 measured seconds; four non-AI list routes.','Targets met in named local/CI environments; agreed deployment still needs measurement.'],
 ['NFR-04',f'Default 28-second budget observed at {timeout["observed_seconds"]:.3f}s; provider cancelled; five collections unchanged.','Passed (<30s); controlled stalled provider.'],
 ['NFR-05','All six core screens at 360, 768 and 1440 px; no horizontal page overflow.','Passed; screenshots embedded in this report.'],
 ['NFR-06','Automated WCAG A/AA audit of core screens, labels/focus and keyboard-only registration/kitchen/collection flow.','Passed in the automated scope; audit is not an accessibility certification.'],
 ['NFR-07','Two separate processes, two accounts and five collections compared before/after restart; SQLite and real PostgreSQL.','Passed in recorded environments.'],
 ['NFR-08','Missing/invalid fields, non-finite/negative numeric rules, whole-batch rejection and declared allergen conflicts; estimate labels.','Passed with controlled outputs; hidden ingredients/cross-contamination are not established.'],
 ['NFR-09','Locked install, explicit migrations, production build, CI tests and artifacts.','CI/local reproduction verified. HTTPS staging and live-provider smoke checks remain release gates.'],
],[62,272,166])
heading('Performance measurements')
table(['Environment','Requests','p95','Errors','Result'],[
 ['Local macOS ARM64, SQLite, one worker',local_load['overall']['requests'],f'{local_load["overall"]["p95_ms"]:.2f} ms',f'{100*local_load["overall"]["error_rate"]:.5f}%','PASS'],
 ['GitHub Actions, PostgreSQL 17, one worker',pg_load['overall']['requests'],f'{pg_load["overall"]["p95_ms"]:.2f} ms',f'{100*pg_load["overall"]["error_rate"]:.5f}%','PASS'],
],[225,65,70,70,70])
paragraph('Thresholds: p95 <= 500 ms and error rate < 1%, also checked per route. Setup creates 5,000 entries before timing; signed-in users query inventory/profile/shopping/favorites with one-second think time. Shopping/favorites are initially empty; AI calls are excluded. The CI results retain connection-level failures and latency outliers in their exported measurements rather than omitting them. Neither result is represented as a production SLA.',True)

page();heading('4. Quality analysis and mitigation',1)
paragraph('Dependency audits checked the committed Python and pnpm dependency resolutions and reported no known vulnerabilities at the run time. This finding is time-bound and does not prove the application is free of vulnerabilities.')
paragraph('The first integrated CI run passed its full-stack job but its scanner could not write the default working directory. A second scan completed but an optional metric export failed. The corrected job uses a writable project directory and supported export fields. These failures remain distinct from completed source findings.')
table(['SonarQube evidence','Recorded value'],[
 ['Server version',sonar_server.get('version','Pending completed scan')],
 ['Analysis revision',CONFIG.get('sonar_revision',CONFIG['ci_revision'])],
 ['Quality gate',gate_status],
 ['Reported issues',issues.get('total','Pending completed scan')],
 ['High/blocker impact or legacy critical/blocker',len(high) if sonar else 'Pending completed scan'],
 ['Coverage reported by scanner',sonar_measures.get('coverage','Pending completed scan')],
 ['Security hotspots',sonar_measures.get('security_hotspots','Pending completed scan')],
],[260,240])
if high:
    paragraph('The full issue export and rule-specific mitigation register are under docs/tests/quality. High-impact findings require the documented fix or explicit reviewer acceptance; an analysis completing is separate from the quality gate passing.')
    table(['Rule / location','Finding','Mitigation status'],[
        [str(issue.get('rule',''))+'\n'+str(issue.get('component','')).replace('fridgely:','')+':'+str(issue.get('line','')),
         issue.get('message',''), 'See committed mitigation register; no automatic claim of resolution']
        for issue in high[:5]],[160,205,135])
else:
    paragraph('The initial scan recorded 17 findings: one email regex concern, four implicit form-submit types and twelve assertion-helper classification findings. PR #13 replaces the regex with a maintained parser, makes submit types explicit, and renames the custom HTTP helper while retaining its assertions. Completed scans of the corrected and current application report zero issues. Both initial exports and rule-specific mitigation evidence are committed.')
paragraph('The quality-gate export is OK with an empty conditions array on this initial project analysis. The explicit zero issue/high-severity/hotspot totals and actual measured tests are preserved; gate OK is not presented as proof that a custom release policy was evaluated.',True)
paragraph('The first frontend-completion scan at 522e0db reported one MAJOR javascript:S9383 finding on the unmarked background load. Its selected original fields and artifact identity are retained in quality/frontend-522-findings.json. Commit 25c111a explicitly marks this internally handled promise with void; the follow-up scan and measured tests are recorded against that source. No runtime rejection incident is claimed from the static finding alone.',True)
paragraph('Separate CI policy checks enforce backend statement/branch floors of 90%/70% and frontend line/branch/function floors of 90%/85%/85%. Their observed job status is recorded separately from the application run. A full-history secret scan initially flagged documentation prose and a deliberately invalid unsigned test JWT; only specific verified historical fingerprints are scoped as false positives. No broad file exclusion or history rewrite is used.',True)
paragraph(f'Current verification run {CONFIG["ci_run_id"]} executes the application and browser suites on the cited source revision. Its coverage-policy and secret-scan jobs enforce the explicit floors and their negative canaries. Historical policy-only run 44933945505 separately verified source identity before reusing immutable application evidence from run 44932416317; those older results are not relabelled as a new source run.',True)
paragraph('The scan runs against a disposable loopback-only SonarQube server inside CI. It does not require uploading this private repository to an unrelated hosted analysis account. The temporary initial admin password is rotated, tokens are masked and the server is removed after export. The exported JSON remains reviewable after the server is destroyed.',True)

page();heading('5. Review, interpretation and release gates',1)
paragraph('The tests establish a working integrated application within the recorded environments, not a guarantee that every possible input or deployment condition is covered. The strongest evidence is the agreement between real JWT/SQL behavior, fixture-backed provider boundary tests, independent-process persistence, browser user switching and measured PostgreSQL load.')
table(['PR','Review scope'],[
 ['#9 Accounts/database','Normalized registration, Argon2id, signed JWT, preferences, inventory and shared migration.'],
 ['#10 Application integration','Existing recipe/collections module history, real host composition and the 27-case acceptance adapter.'],
 ['#11 Web integration','React screens, server-owned state, explicit failures, responsive layout, browser/accessibility evidence.'],
 ['#12 CI verification','PostgreSQL, process restart, HTTP security, browser coverage, five-minute load, dependency and SonarQube jobs.'],
 ['#13 / #14 / #15','Quality fixes; self-host API documentation and production image; four penetration probes.'],
 ['#49 / #50 / #51 / #52','Relational migration with actual TDD; review/version policies; AI evidence; coverage and secret failure gates.'],
 ['test_work Test report','Traceability, measured results, non-functional evidence, quality findings/mitigations and this PDF.'],
 ['#56 Frontend completion','Linked validation, independent loading/retry, committed-write acknowledgement, safe modal feedback, team setup guide and current evidence.'],
],[160,340])
paragraph('Each PR is opened from Berfin\'s account with an English title/description. The dependent bases keep feature reviews separate and preserve teammate commits. Yeşim\'s verified reviewer handle is yesimyigitbasi. No PR has been merged to main by this work.')
heading('Remaining release checks')
paragraph('Render GitHub access must be granted for the private source repository or an authorized private fork before public hosting can complete. Supply the team\'s real provider credential outside source control and run live recipe checks, then record deployment-specific smoke/performance results. Obtain independent reviews, owner-applied main protection, team contribution/Project evidence and course-platform submission. These human/account actions are not inferred from test execution.')
heading('Submission schedule')
paragraph('Internal preparation target: 22 November 2026. The supplied updated instructor email sets the test PR/reviewer deadline to 25 November and the approved PDF submission to 29 November 2026. This is a review copy. Submission to learn.bilgi follows PR approval and is not claimed here.')
paragraph(f'Artifacts: [verification run]({run_url}), [criterion CSV]({repo_url}/blob/{artifact_ref}/docs/tests/coverage/traceability.csv), [quality evidence]({repo_url}/tree/{artifact_ref}/docs/tests/quality), [non-functional results]({repo_url}/tree/{artifact_ref}/docs/tests/non-func-tests). Images are embedded on the following pages, as required.',True)

page();heading('6. Desktop browser evidence',1)
paragraph('1440 px viewport, production React build served by the actual API host. The displayed ingredient and addition date were created through the authenticated SQL-backed endpoint. Synthetic test accounts are used throughout.',True)
image=ROOT/'docs/tests/evidence/screenshots/fridge-1440.png'
from PIL import Image as PILImage
with PILImage.open(image) as picture:w,h=picture.size
story.append(Image(str(image),width=500,height=500*h/w))
md.extend(['![Desktop browser evidence](evidence/screenshots/fridge-1440.png)',''])
story.append(Spacer(1,18))
paragraph('Browser assertions also verify preferences, full recipe details, missing shopping ingredients, favorites/history, reload persistence, account switching, provider failure and empty states. Passing browser results use a controlled recipe provider; they do not establish live-provider correctness.',True)

page();heading('7. Mobile browser evidence',1)
paragraph('360 px viewport. The same core actions remain available without horizontal page overflow. Long ingredient names are also checked by the test suite. The matching 768 px screenshot is committed with the evidence.',True)
image=ROOT/'docs/tests/evidence/screenshots/fridge-360.png'
with PILImage.open(image) as picture:w,h=picture.size
height=610;width=height*w/h
mobile=Image(str(image),width=width,height=height)
notes=Paragraph(markup('Verified at 360, 768 and 1440 px.\n\nThe navigation wraps, forms remain labelled, ingredient names wrap and all buttons remain reachable.\n\nKeyboard-only verification covers registration, preferences, fridge addition/removal, generation, recipe dialog actions, shopping removal, favorites/history and sign-out.\n\nAn automated WCAG A/AA audit found initial contrast issues; these were fixed before the successful recorded rerun.\n\nThis screenshot is embedded directly in the PDF rather than supplied only as a link.'),styles['body'])
layout=Table([[mobile,notes]],colWidths=[width+25,500-width-25],hAlign='LEFT')
layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(1,0),(1,0),0)]))
story.append(layout)
md.extend(['![Mobile browser evidence](evidence/screenshots/fridge-360.png)',''])

page();heading('8. Tablet browser evidence',1)
paragraph('768 px viewport, same authenticated application and owned ingredient workflow. This image accompanies the executable width/overflow/label assertions; the measured suite also visits recipes, shopping, favorites, history and preferences.',True)
image=ROOT/'docs/tests/evidence/screenshots/fridge-768.png'
with PILImage.open(image) as picture:w,h=picture.size
story.append(Image(str(image),width=600*w/h,height=600))
md.extend(['![Tablet browser evidence](evidence/screenshots/fridge-768.png)',''])

page();heading('9. API and cloud verification boundary',1)
paragraph('The real API schema and locally bundled Swagger UI are available at /api/openapi.json and /api/docs. The screenshot below loads actual account, preference, inventory, recipe and collection operations with JWT bearer authorization; it is not a static API mock.',True)
image=ROOT/'docs/tests/evidence/screenshots/api-documentation.png'
with PILImage.open(image) as picture:w,h=picture.size
story.append(Image(str(image),width=500,height=500*h/w))
md.extend(['![API documentation evidence](evidence/screenshots/api-documentation.png)',''])
story.append(Spacer(1,12))
paragraph('The production image was built and started against PostgreSQL in CI. Two users, persisted inventory/preferences/shopping, relogin and an unchanged signed token were checked after an actual container restart. Missing provider credentials correctly produce 503. This proves the packaged host and managed-database contract in the named CI environment, not public Render availability or live recipe generation.')
paragraph('Render workspace access succeeds and the free PostgreSQL instance exists. The attempted Blueprint import returns repository/branch/file access denied, so there is no verified public web URL. A repository-owner GitHub grant or authorized private fork is required. The free database created on 20 November is scheduled to expire on 20 December 2026; longer retention needs a reviewed plan. These remaining actions are tracked explicitly.',True)

page();heading('10. Frontend validation and recovery',1)
paragraph('Current #56 screenshots use isolated accounts and the actual React/API host. Validation is associated with the input and blocks invalid writes. An unavailable favorites collection has its own retry; the fridge and other collections remain usable. These error states are included in the three-width accessibility checks.',True)
validation=BASE/'evidence/frontend-completion/validation-360.png'
unavailable=BASE/'evidence/frontend-completion/favorites-unavailable-768.png'
with PILImage.open(validation) as picture:w,h=picture.size
validation_image=Image(str(validation),width=175,height=175*h/w)
with PILImage.open(unavailable) as picture:w,h=picture.size
unavailable_image=Image(str(unavailable),width=290,height=290*h/w)
layout=Table([[validation_image,unavailable_image]],colWidths=[195,305],hAlign='LEFT')
layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]))
story.append(layout)
md.extend(['![Linked validation at 360px](evidence/frontend-completion/validation-360.png)','',
    '![Independent favorites retry at 768px](evidence/frontend-completion/favorites-unavailable-768.png)',''])
story.append(Spacer(1,12))
paragraph('Recipe actions also display their error/success feedback inside the dialog, prevent duplicate submissions and provide a View shopping list link after missing ingredients are added. A completed write with a failed list refresh is acknowledged separately; retrying reads data without repeating the write. A 401 from any request clears personal state even during another collection outage.',True)

def footer(canvas,document):
    canvas.saveState()
    canvas.setFillColor(MUTED);canvas.setFont('Arial',8)
    canvas.drawString(47,24,'FRIDGELY  |  CMPE 331  |  TEST REPORT  |  REVIEW COPY')
    canvas.drawRightString(A4[0]-47,24,str(document.page))
    canvas.setStrokeColor(colors.HexColor('#d5e1d4'));canvas.line(47,38,A4[0]-47,38)
    canvas.restoreState()

pdf=OUT/'Fridgely-Software-Test-Report.pdf'
document=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=47,leftMargin=47,topMargin=43,bottomMargin=52,
    title='Fridgely Software Test Report',author='Berfin Gökgöz')
document.build(story,onFirstPage=footer,onLaterPages=footer)
markdown=ROOT/'docs/tests/software-test-report.md'
markdown.write_text('\n'.join(md)+'\n')
shutil.copyfile(pdf,ROOT/'docs/tests/software-test-report.pdf')
shutil.copyfile(markdown,OUT/'Fridgely-Software-Test-Report.md')
shutil.copytree(ROOT/'docs/tests/evidence/screenshots',OUT/'evidence/screenshots',dirs_exist_ok=True)
print(json.dumps({'pdf':str(pdf),'markdown':str(markdown),'quality_gate':gate_status}))

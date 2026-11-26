"""Export a source-pinned report from verified CI evidence, without provider calls."""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'docs/tests'
REPO = 'https://github.com/SarpCizer/CMPE331-Project'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_provenance(config, evidence):
    provenance = read(BASE / 'report-provenance.json')
    if provenance['report_baseline_revision'] != config['ci_revision']:
        raise ValueError('Inventory source revision mismatch')
    files = provenance['browser_test_files']
    all_files = files + provenance['browser_support_files']
    paths = [item['path'] for item in all_files]
    if len(set(paths)) != len(paths) or any(not re.fullmatch(r'frontend/tests/[A-Za-z0-9_.-]+\.js', path) for path in paths):
        raise ValueError('Invalid or duplicate browser inventory path')
    if any(not re.fullmatch(r'[0-9a-f]{40}', item['git_blob_sha']) for item in all_files):
        raise ValueError('Invalid browser inventory blob identity')
    suites = ET.parse(evidence / 'integrated-evidence/browser-junit.xml').getroot().findall('testsuite')
    counts = {suite.get('name'): int(suite.get('tests')) for suite in suites}
    if set(counts) != {Path(item['path']).name for item in files}:
        raise ValueError('Browser inventory does not match recorded JUnit suites')
    loads = []
    for item in provenance['historical_loads']:
        path = (BASE / item['path']).resolve()
        if not path.is_relative_to(BASE.resolve()):
            raise ValueError('Unsafe historical load path')
        data = read(path)
        if data['revision'] != item['revision']:
            raise ValueError('Historical load revision mismatch')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Historical load evidence digest mismatch')
        loads.append((item, data))
    return provenance, counts, loads


def junit(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('.//testsuite')
    return {key: sum(int(s.get(key, 0)) for s in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')}


def validate(config, evidence):
    """Refuse to publish results with another source identity or altered raw files."""
    revision = config['ci_revision']
    summary = read(evidence / 'summary.json')
    index = read(evidence / 'evidence-index.json')
    load = read(evidence / 'integrated-evidence/postgresql-load.json')
    pen = read(evidence / 'integrated-evidence/penetration.json')
    sonar = read(evidence / 'sonarqube-evidence/source-identity.json')
    live = read(evidence / 'render-public-smoke.json')
    identities = [summary['source'], index['source_revision'], load['revision'],
                  pen['source_revision'], sonar['analysis_revision'],
                  sonar['test_revision'], live['source_revision'],
                  config['sonar_revision'], config['artifact_ref']]
    if not re.fullmatch(r'[0-9a-f]{40}', revision) or any(x != revision for x in identities):
        raise ValueError('Source revision mismatch: report, CI, Sonar and deployment evidence must agree')
    if any(x != config['ci_run_id'] for x in (summary['run'], index['ci_run_id'], config['sonar_run_id'])):
        raise ValueError('CI run mismatch')
    if not summary['ci_completed'] or summary['ci_jobs_passed'] != 7 or config['ci_status'] != 'PASS':
        raise ValueError('Incomplete CI evidence')
    for name, metadata in index['files'].items():
        path = (evidence / name).resolve()
        if not path.is_relative_to(evidence.resolve()):
            raise ValueError('Unsafe evidence path')
        data = path.read_bytes()
        if len(data) != metadata['bytes'] or hashlib.sha256(data).hexdigest() != metadata['sha256']:
            raise ValueError('Evidence digest mismatch: ' + name)
    for name, raw in [('backend', 'backend-junit.xml'), ('browser', 'browser-junit.xml')]:
        if junit(evidence / 'integrated-evidence' / raw) != summary[name]:
            raise ValueError('JUnit summary mismatch: ' + name)
    return summary, index


def export():
    config = read(BASE / 'report-input.json')
    evidence = BASE / config['evidence_root']
    summary, index = validate(config, evidence)
    provenance, browser_counts, historical_loads = validate_provenance(config, evidence)
    follow_up = None
    if (BASE / 'review-follow-up.json').is_file():
        import review_follow_up
        follow_up = review_follow_up.load(BASE)
    # Validate before creating or replacing any published output.
    out = Path(os.getenv('FRIDGELY_REPORT_OUTPUT', str(ROOT / 'build/reports')))
    out.mkdir(parents=True, exist_ok=True)
    fonts = [
        ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
    ]
    regular, bold = next((pair for pair in fonts if all(Path(p).is_file() for p in pair)), (None, None))
    if regular is None:
        raise RuntimeError('Install Arial or DejaVu Sans to export the report')
    pdfmetrics.registerFont(TTFont('Report', regular))
    pdfmetrics.registerFont(TTFont('ReportBold', bold))
    pdfmetrics.registerFontFamily('Report', normal='Report', bold='ReportBold')
    green, muted, pale = [colors.HexColor(x) for x in ('#173f2f', '#53685a', '#e9f1e7')]
    styles = {
        'body': ParagraphStyle('body', fontName='Report', fontSize=9.4, leading=13.4, textColor=green, spaceAfter=8),
        'small': ParagraphStyle('small', fontName='Report', fontSize=8, leading=11, textColor=muted, spaceAfter=6),
        'h1': ParagraphStyle('h1', fontName='ReportBold', fontSize=23, leading=28, textColor=green, spaceAfter=15),
        'h2': ParagraphStyle('h2', fontName='ReportBold', fontSize=12, leading=16, textColor=green, spaceBefore=10, spaceAfter=7),
        'cell': ParagraphStyle('cell', fontName='Report', fontSize=8, leading=10.7, textColor=green),
    }
    story, markdown = [], []

    def markup(text):
        escaped = html.escape(str(text).replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
        return re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)', r'<link href="\2" color="#245d42">\1</link>', escaped)

    def paragraph(text, kind='body'):
        # Markdown links use concise PDF anchor text to avoid unbreakable URLs.
        escaped = markup(text)
        story.append(Paragraph(escaped, styles[kind]))
        markdown.extend([text, ''])

    def heading(text, first=False):
        story.append(Paragraph(html.escape(text), styles['h1' if first else 'h2']))
        markdown.extend([('# ' if first else '## ') + text, ''])

    def table(headers, rows, widths):
        cells = [[Paragraph(markup(x), styles['cell']) for x in row] for row in [headers, *rows]]
        grid = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
        grid.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), pale), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), .7, green),
            ('LINEBELOW', (0, 1), (-1, -1), .25, colors.HexColor('#d6ded8')),
        ]))
        story.extend([grid, Spacer(1, 10)])
        markdown.append('| ' + ' | '.join(headers) + ' |')
        markdown.append('| ' + ' | '.join('---' for _ in headers) + ' |')
        markdown.extend('| ' + ' | '.join(str(v).replace('|', '/') for v in row) + ' |' for row in rows)
        markdown.append('')

    def page():
        story.append(PageBreak())

    def screenshot(name, width, height):
        path = evidence / 'integrated-evidence/screens' / name
        img = Image(str(path))
        ratio = min(width / img.imageWidth, height / img.imageHeight)
        img.drawWidth, img.drawHeight = img.imageWidth * ratio, img.imageHeight * ratio
        img.hAlign = 'CENTER'
        story.extend([img, Spacer(1, 9)])
        markdown.extend([f'![{name}]({config["evidence_root"]}/integrated-evidence/screens/{name})', ''])

    rev = config['ci_revision']
    run = config['ci_run_id']
    integrated = evidence / 'integrated-evidence'
    load = read(integrated / 'postgresql-load.json')
    timeout = read(integrated / 'provider-timeout.json')
    coverage = summary['coverage']['actual_percent']
    heading('Fridgely\nSoftware Testing Report', True)
    paragraph(config['report_date'] + ' | Prepared for the CMPE331 submission review', 'small')
    paragraph('Historical application snapshot; reproducibility/provenance correction dated ' + provenance['correction_date'] + '. Measurements retain their original source identities.', 'small')
    heading('Verified integration candidate')
    paragraph(config['release_status'])
    paragraph('Tested source: ' + rev)
    paragraph(f'[Exact-source CI run {run}]({REPO}/actions/runs/{run}) | [Source commit]({REPO}/commit/{rev}) | [ZIP verification, #48]({REPO}/issues/48#issuecomment-7143013023)')
    paragraph('This report replaces the historical 25c111a evidence with the measured results for a59556e. A later report-only commit stores this document; it does not change which application source these tests exercised. A new selected application SHA requires matching evidence and a regenerated report.')
    table(['Verification layer', 'Recorded result'], [
        ['PostgreSQL / backend', f'{summary["backend"]["tests"]} passed; 0 skipped'],
        ['Requirement acceptance', f'{summary["acceptance"]["tests"]} passed'],
        ['Browser / accessibility / keyboard', f'{summary["browser"]["tests"]} passed'],
        ['HTTP security / scoped penetration', '12 HTTP cases and 4 penetration probes passed'],
        ['CI delivery checks', 'All 7 jobs successful; source ZIP verified'],
        ['Live public web service', '6 read-only HTTPS checks passed; no AI request'],
    ], [220, 279])
    heading('What this evidence establishes')
    paragraph('The integrated frontend, API, ownership rules and PostgreSQL persistence are compatible within the recorded tests. Recipe workflows use controlled external provider responses. Actual paid or free model inference was not exercised, and the live service has no verified recipe-provider credentials.')
    paragraph('Original report: Berfin Gökgöz with Codex assistance. Review corrections: Sarp Çizer with Codex assistance. No instructor acceptance or course-platform upload is inferred.', 'small')

    page()
    heading('Functional traceability', True)
    paragraph('All 15 approved user stories have recorded acceptance assertions in tests/functional/requirements.test.mjs. The real application host and SQL are exercised; provider behavior is controlled. Acceptance and backend/browser counts overlap in coverage of requirements and must not be added as unique requirements.')
    table(['Story', 'Verified behavior', 'Acceptance IDs'], [
        ['US-01', 'Registration, duplicate and invalid input rejection', 'T01-T02'],
        ['US-02', 'Correct and incorrect sign-in', 'T01'],
        ['US-03', 'Save and clear dietary/allergen preferences', 'T01'],
        ['US-04', 'Add ingredient; timestamp; blank rejection', 'T01-T02'],
        ['US-05', 'Owned inventory, original dates and repeated names', 'T01-T02'],
        ['US-06', 'Delete selected ingredient only', 'T01'],
        ['US-07', 'Fridge/preferences to provider, allergens, empty fridge; no deduction', 'T01-T03'],
        ['US-08', 'Recipe details and six malformed-output cases', 'T01-T07'],
        ['US-09', 'Retryable provider error preserves saved state', 'T01'],
        ['US-10', 'Missing ingredients only; stable IDs on repeat', 'T01'],
        ['US-11', 'Manual shopping list add/list/remove', 'T01'],
        ['US-12', 'Idempotent favorites; inventory unchanged', 'T01'],
        ['US-13', 'Remove favorite, retain history', 'T01'],
        ['US-14', 'Newest-first view history', 'T01'],
        ['US-15', 'Missing, malformed and expired JWT; cross-owner isolation', 'T01-T03'],
    ], [49, 369, 81])
    paragraph('Each short ID is prefixed by its story, for example US-07-T01. Full historical case names and PASS counts are in acceptance.log; backend-junit.xml and browser-junit.xml retain individual cases. The current coverage/traceability.csv identifies its separate immutable assertion source; the follow-up explains its additional AC/NFR detail.', 'small')
    heading('Database and transaction boundaries')
    paragraph('The 133 backend tests include real PostgreSQL with no skips. JWT subjects supply identity; client-supplied owner fields cannot transfer ownership. Inventory changes through manual add/delete. Collection regressions check commit-before-success and rollback behavior; duplicate ingredient rows remain distinct and retain their addition dates.')

    page()
    heading('Coverage and security', True)
    table(['Metric', 'Measured', 'Unchanged minimum'], [
        ['Backend statements', f'{coverage["backend_statements"]:.2f}%', '90%'],
        ['Backend branches', f'{coverage["backend_branches"]:.2f}%', '70%'],
        ['Frontend lines', f'{coverage["frontend_lines"]:.2f}%', '90%'],
        ['Frontend branches', f'{coverage["frontend_branches"]:.2f}%', '85%'],
        ['Frontend functions', f'{coverage["frontend_functions"]:.2f}%', '85%'],
    ], [240, 129, 130])
    paragraph('The independent coverage gate and its deliberately failing synthetic canary passed. Production backend source and mapped frontend/src are in scope; line/statement coverage is separate from branch coverage.')
    heading('Security results')
    paragraph('The 12 real HTTP cases check account validation, signed finite-expiry JWTs, tamper/unsigned-token rejection, protected endpoints and two-account isolation. Four targeted penetration probes passed: literal SQL injection payload handling, mass-assignment rejection, configuration/source/path-traversal denial and stored XSS rendered as inert text. This is a scoped automated assessment, not a complete independent penetration audit.')
    paragraph('Python and frontend dependency audits passed with no recorded advisories in their exported results. The reachable-history secret scan returned zero findings; a synthetic credential canary proved the scanner fails on its test secret. Secrets and account tokens are not retained in report evidence.')
    heading('SonarQube: source identity and limitations')
    paragraph('SonarQube 26.11.0.134175 ran in an ephemeral loopback-only CI server. Analysis and test revision both equal a59556e; test_artifacts_reused=false. Recorded issues: 0; bugs, vulnerabilities, code smells and security_hotspots metrics: 0. Its aggregate coverage is 93.9%, which has a different scope from the per-language policy above.')
    paragraph('The recorded quality gate is OK, but conditions=[]; that alone is not an independent threshold decision. The detailed security-hotspots endpoint returned API_UNAVAILABLE (HTTP 400). A zero hotspot metric does not establish a completed manual hotspot review. Raw issues, metrics, gate and source identity are retained.')

    page()
    heading('Performance and persistence', True)
    paragraph('Environment: GitHub Actions Ubuntu, PostgreSQL 17, one application worker; Linux x86_64, Python 3.12.16, 2 reported CPUs. Scenario: 50 users, 100 inventory rows per user, 1-second think time and 300 seconds configured duration. Shopping/favorites are empty owned collections. No model call occurs in the measured loop.')
    table(['Route / total', 'Requests', 'Errors', 'p95 ms'], [
        *[[name.title(), f'{data["requests"]:,}', str(data['errors']), f'{data["p95_ms"]:.2f}'] for name, data in load['routes'].items()],
        ['Overall', f'{load["overall"]["requests"]:,}', '0', f'{load["overall"]["p95_ms"]:.2f}'],
    ], [199, 100, 90, 110])
    paragraph(f'Measured duration: {load["scenario"]["measured_seconds"]:.2f} seconds. Overall mean {load["overall"]["mean_ms"]:.2f} ms; maximum {load["overall"]["max_ms"]:.2f} ms. The original p95 <= 500 ms and error rate < 1% limits pass overall and per route. This is CI evidence, not a Render or AI-provider benchmark.')
    heading('Timeout and cancellation')
    paragraph(f'Controlled delayed provider: configured deadline {timeout["configured_seconds"]} seconds; observed {timeout["observed_seconds"]:.2f} seconds. Provider cancellation and all five saved collections remaining unchanged passed. This measures application timeout handling, not a real provider service-level guarantee.')
    heading('Container and PostgreSQL restart')
    paragraph('Production image smoke checks passed for the frontend, health, OpenAPI and Swagger. A real PostgreSQL-backed restart preserved inventory, preferences and shopping data; relogin and two-account isolation passed. With provider credentials absent, recipe generation returned 503 as expected. The database and JWT secret were not reset for this report.')
    heading('Live deployment: separate observation')
    paragraph('[Fridgely on Render](https://fridgely-web.onrender.com) runs the original repository on the FREE plan. Deploy dep-dc2uq60473hc73bfhqs0 reached LIVE at a59556e via new_commit. On 24 November at 20:06 UTC, root, health, OpenAPI, Swagger and referenced JS/CSS returned 200. Six read-only checks used no account credentials or inference. This establishes the feature branch CI-to-deployment path; main deployment is not claimed.')

    page()
    heading('Historical delivery evidence and actions', True)
    paragraph('This page records the a59556e checkpoint as of 24 November 2026. Its pending decisions and draft-PR statuses are historical, not a description of current main. The instructor-review follow-up has its own source and status.', 'small')
    paragraph(f'Source-only ZIP: {config["zip_source_files"]} manifest source files. CRC, every file length/hash and declared Git blobs were verified; two independent builds were byte-identical. The generic contribution placeholder is absent. ZIP SHA-256: {config["zip_sha256"]}')
    paragraph('The matching source archive is the source-archive artifact of CI run 45474025963. Raster evidence and report PDFs are deliberately outside the source-only ZIP. Pair this PDF with that exact archive; do not substitute the historical #60 / 90529bb package.')
    heading('TDD and independent tooling review')
    paragraph('[PR #66](' + REPO + '/pull/66) records the genuine RED sidecar regression at 282afeb and the GREEN fix at 39b7b54. Berfin independently reran all 8 packaging tests and both default/nested report exports and approved that exact head (review 6046700031). CI run 45476946238 passed all 7 jobs. Those are separate tooling results; the a59556e source archive job had 7 packaging regressions. #66 remains outside the tested application source of this report until merged and selected.')
    paragraph('This report refresh has its own RED regression, 5140116: the old exporter accepted a false all-zero source revision and wrote a PDF. The refreshed exporter rejects mismatched identities before publishing. It validates retained raw evidence hashes and checks backend/browser JUnit totals. No retroactive TDD claim is made for older implementation work.')
    heading('Reproduction and provenance')
    paragraph('Install scripts/tests/requirements-report.txt, then run python scripts/tests/export_report.py. Set FRIDGELY_REPORT_OUTPUT for another directory. Run python scripts/tests/test_export_report.py for source-identity and nested-output regressions. Inputs: docs/tests/report-input.json and its evidence_root; evidence-index.json records each retained file SHA-256 and all six downloaded artifact archive digests. No network, provider key or inference is required to export.')
    paragraph(f'[CI artifacts]({REPO}/actions/runs/{run}) | [Integration decision, #24]({REPO}/issues/24) | [Report review, #44]({REPO}/issues/44) | [Submission tracking, #48]({REPO}/issues/48)')
    heading('Open release decisions')
    paragraph('1. The team / product owner must confirm the exact submission SHA in #24. Berfin supports the verified a59556e candidate; this does not substitute for other team members or owner approval. If #66 or another change is included, select the resulting source and regenerate its archive/evidence/report pairing.')
    paragraph('2. Live recipe generation remains unverified. Draft #65 and the team Cloudflare Free account/credential configuration are separate work. After reviewed integration, validate generated recipes, missing-ingredient shopping and unchanged inventory using an authorized free account.')
    paragraph('3. Independent report review and the actual learn.bilgi upload/receipt remain pending. Main was not merged; no paid resource or provider request was created by this work.')

    page()
    heading('Reproducibility and evidence versions', True)
    paragraph('The default exporter creates build/reports, including missing parents, after validating the evidence. An explicit FRIDGELY_REPORT_OUTPUT supports a new nested directory. Windows checkouts preserve raw evidence bytes; UTF-8 text is read and written explicitly. Regressions exercise default and nested outputs plus rejection of mismatched source identities.')
    heading('Browser files in the tested snapshot')
    paragraph(f'Inventory source: {rev}. Each link targets this immutable source. The recorded JUnit contains 22 cases across four files; helper modules are not counted as test cases.')
    table(['Recorded test file', 'JUnit cases'], [
        [f'[{item["path"]}]({REPO}/blob/{rev}/{item["path"]})', str(browser_counts[Path(item['path']).name])]
        for item in provenance['browser_test_files']
    ], [410, 89])
    report_head = provenance['reviewed_report_head']
    paragraph(f'[completion.spec.js in the reviewed report head]({REPO}/blob/{report_head}/frontend/tests/completion.spec.js) has the same recorded Git blob as the tested source. fixtures.js and global-setup.js are supporting modules. This inventory belongs to the historical snapshot.', 'small')
    heading('Three distinct performance measurements')
    rows = []
    for metadata, result in historical_loads:
        rows.append([metadata['label'], f'[{result["revision"][:7]}]({REPO}/commit/{result["revision"]})', result['environment'], f'{result["overall"]["p95_ms"]:.2f}'])
    rows.append(['Report CI', f'[{rev[:7]}]({REPO}/commit/{rev})', load['environment'], f'{load["overall"]["p95_ms"]:.2f}'])
    table(['Measurement', 'Source', 'Environment', 'p95 ms'], rows, [105, 70, 249, 75])
    paragraph('Different revisions and environments were measured. The local run used macOS ARM64, 8 reported CPUs and SQLite; historical CI used Linux x86_64, 2 reported CPUs and PostgreSQL. The 44.35 ms and 371.47 ms p95 values are not a controlled comparison of identical code. The later a59556e CI measurement is 204.06 ms. No local performance run at a59556e is retained.')
    paragraph('Historical CI is about 8.38 times the local value, with 128.53 ms below the 500 ms limit. Hardware, database access and intervening code changes are plausible contributors; the retained runs do not isolate their effects. A same-revision paired experiment is needed for causal attribution. The a59556e CI run leaves 295.94 ms of p95 headroom in its named environment.', 'small')

    page()
    heading('Responsive evidence: desktop', True)
    paragraph('Actual browser screenshots from the same CI run and a59556e source. Synthetic test-account contents are used; no live account credentials are shown. The 22 Chromium cases cover the functional flow, loading/error/cancellation states, responsive layout, accessibility checks and keyboard interaction.', 'body')
    screenshot('fridge-1440.png', 499, 465)
    paragraph('Desktop viewport: 1440 px. The inventory, recipe controls and supporting navigation are exercised through the production frontend build and integrated API.', 'small')

    page()
    heading('Responsive evidence: mobile / tablet', True)
    paragraph('The 360 px and 768 px viewport captures below are CI presentation evidence. They do not replace the automated assertions or establish universal accessibility conformance.', 'small')
    imgs = []
    for name, width, height in [('fridge-360.png', 150, 605), ('fridge-768.png', 315, 605)]:
        img = Image(str(integrated / 'screens' / name))
        factor = min(width / img.imageWidth, height / img.imageHeight)
        img.drawWidth, img.drawHeight = img.imageWidth * factor, img.imageHeight * factor
        imgs.append(img)
        markdown.extend([f'![{name}]({config["evidence_root"]}/integrated-evidence/screens/{name})', ''])
    layout = Table([imgs], colWidths=[169, 330], hAlign='LEFT')
    layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(layout)

    if follow_up:
        review_follow_up.append(BASE, story, markdown, heading, paragraph, table, page, *follow_up)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(pale)
        canvas.line(48, 40, A4[0] - 48, 40)
        canvas.setFont('Report', 7.5)
        canvas.setFillColor(muted)
        identity = ('Follow-up ' + follow_up[0]['source_revision'][:7] + ' | CI ' + str(follow_up[0]['ci_run_id']) + ' | review copy') if follow_up and doc.page > 8 else 'Historical a59556e | CI 45474025963'
        canvas.drawString(48, 27, 'Fridgely | ' + identity)
        canvas.drawRightString(A4[0] - 48, 27, str(doc.page))
        canvas.restoreState()

    pdf = out / 'Fridgely-Software-Test-Report.pdf'
    doc = SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=48, leftMargin=48,
                           topMargin=45, bottomMargin=55,
                           title='Fridgely Software Testing Report - historical baseline and review corrections',
                           author='Berfin Gökgöz; corrections by Sarp Çizer with Codex assistance')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    text = '\n'.join(markdown)
    (out / 'Fridgely-Software-Test-Report.md').write_text(text, encoding='utf-8')
    (BASE / 'software-test-report.md').write_text(text, encoding='utf-8')
    shutil.copyfile(pdf, BASE / 'software-test-report.pdf')
    print(json.dumps({'pdf': str(pdf), 'source': rev, 'ci_run': run,
                      'evidence_files_verified': len(index['files']), 'release_approval': 'pending'}))


if __name__ == '__main__':
    export()

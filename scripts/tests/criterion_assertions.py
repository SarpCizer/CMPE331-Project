"""Immutable assertion links for all 48 ACs and nine NFRs; not execution results."""
import argparse
import ast
import csv
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPO = 'https://github.com/SarpCizer/CMPE331-Project'
F = 'tests/functional/requirements.test.mjs'
B = 'frontend/tests/kitchen.spec.js'
R = 'backend/tests/test_recipe_integration.py'
S = 'backend/tests/test_security_matrix.py'

# story, AC, path, case, concrete assertion, purpose
AC = [
('01',1,F,'US-01-T01','assert.ok(login.token)','ID/public email and immediate login without email verification'),
('01',2,F,'US-01-T02','undefined, 409)','Normalized duplicate email rejected'),
('01',3,F,'US-01-T02','assert.ok(bob.id)','Invalid email/short password rejected; valid retry proves no email reservation'),
('02',1,F,'US-02-T01','assert.match(ok.token','Correct credentials return signed three-part JWT'),
('02',2,F,'US-02-T01','assert.equal(bad.token, undefined)','Wrong credentials return 401 without token'),
('03',1,F,'US-03-T01','token), prefs)','Saved preferences round-trip unchanged'),
('03',2,F,'US-03-T01','token), empty)','Both lists explicitly cleared'),
('03',3,F,'US-07-T01','assert.deepEqual(c.calls[0]','Generation receives current saved preferences'),
('04',1,F,'US-04-T01','assert.ok(item.id)','Ingredient ID/name and clock-derived addedAt'),
('04',2,F,'US-04-T02','token), [])','Blank name rejected without inventory change'),
('04',3,F,'US-04-T01','assert.equal(item.addedAt, fixedNow)','Timestamp equals addition clock; no expiry inference'),
('05',1,B,'real account, saved preferences','toContainText(`Added ${additionDate}`)','Ingredient name and actual saved addition date rendered'),
('05',2,B,'register(page, address','"A fresh canvas"','Explicit empty fridge state after registration; US-05-T01 checks empty API list'),
('05',3,F,'US-05-T01','assert.equal(items[0].addedAt, fixedNow)','Original addition timestamp survives advanced-clock read'),
('06',1,F,'US-06-T01','token), [tomato])','Deleting rice leaves unselected tomato'),
('06',2,F,'US-06-T01',"'/inventory/does-not-exist'",'Missing deletion returns 404; subsequent snapshot still tomato'),
('06',3,F,'US-12-T01',"'/inventory', token), [item])",'Generation and repeated favorite saves do not deduct stock; US-14-T01 covers views'),
('07',1,F,'US-07-T01','assert.deepEqual(c.calls[0]','Provider receives owned ingredients/current dietary and allergen lists'),
('07',2,F,'US-07-T02',"'/history', token), [])",'Allergen-conflicting batch rejected with 422 and no saved results'),
('07',3,F,'US-07-T03','assert.equal(c.calls.length, 0)','Empty fridge validation prevents provider calls'),
('07',4,F,'US-07-T01',"'/inventory', token), [item])",'Generation leaves stock snapshot unchanged'),
('08',1,F,'US-08-T01','assert.deepEqual(await c.read','Full details exactly match ingredients/ordered steps/time/calories/servings'),
('08',2,F,'US-08-T02','assert.equal(error.recipes, undefined)','Six distinct malformed cases reject whole result with 502; history/stock unchanged'),
('08',3,B,'real account, saved preferences','await expect(card).toContainText("Time & calories are estimates")','Estimate label plus dialog minutes/calories/servings and ingredient/step assertions'),
('09',1,F,'US-09-T01','assert.equal(error.retryable, true)','Retryable 503 after provider error and unchanged saved collections'),
('09',2,F,'US-09-T01','assert.deepEqual(await Promise.all','All five named collection snapshots unchanged'),
('09',3,R,'test_invalid_provider_response_is_sanitized','assert "private detail" not in response.text','Malformed/incomplete/refused output exposes no provider diagnostics'),
('10',1,F,'US-10-T01',"['onion', 'tomato'])",'Missing onion/tomato added; stocked rice excluded'),
('10',2,F,'US-10-T01',"['onion', 'tomato'])",'Case/whitespace normalization avoids existing tomato duplication'),
('10',3,F,'US-10-T01','first.map(x => x.id).sort()','Repeat action preserves same shopping IDs'),
('10',4,F,'US-10-T01',"'/inventory', token), [rice])",'Add missing ingredients leaves fridge unchanged'),
('11',1,F,'US-11-T01',"'/shopping-items', token), [item])",'Created item appears in owned shopping list'),
('11',2,F,'US-11-T01',"'/shopping-items', token), [])",'Normal removal empties list'),
('11',3,F,'US-11-T01',"{name:' '}, token, 400)",'Blank name rejected; subsequent empty-list assertion'),
('11',4,F,'US-11-T01',"assert.deepEqual(await c.read('/shopping-items', token), []);\n  assert.deepEqual(await c.read('/inventory', token), [ingredient]);",'Normal removal preserves pre-existing stock; does not purchase'),
('12',1,F,'US-12-T01',"'/favorites', token), [recipe])",'Favorite list contains full recipe details'),
('12',2,F,'US-12-T01',"'/favorites', token), [recipe])",'Two saves yield exactly one favorite'),
('12',3,F,'US-12-T01',"'/inventory', token), [item])",'Saving favorites preserves stock'),
('13',1,F,'US-12-T01',"'/favorites', token), [recipe])",'Listing returns saved full recipe'),
('13',2,F,'US-13-T01','assert.equal(history[0].recipe.id, recipe.id)','Favorite removal empties favorites but retains previously viewed history'),
('13',3,F,'US-13-T01',"'/favorites', token), [])",'Before saving, favorites is empty'),
('14',1,F,'US-14-T01','assert.equal(history[0].lastViewedAt','Viewed recipe has injected last-viewed timestamp'),
('14',2,F,'US-14-T01',"'/history', token), [])",'Generated but unopened recipes absent from history'),
('14',3,F,'US-14-T01','history.map(x => x.recipe.id)','Exactly two unique IDs, newest first after reopen; updated timestamp'),
('14',4,F,'US-14-T01',"'/inventory', token), [item])",'Viewing/reopening never deducts stock'),
('15',1,F,'US-15-T03','path, undefined, token, 401)','Authentic expired JWT rejected; T01 covers missing/malformed'),
('15',2,F,'US-15-T02','must deny cross-user access','Foreign read/write operations denied and owner snapshots unchanged'),
('15',3,R,'test_unknown_owner_and_empty_fridge_stop_before_provider','assert generate(a, json={"owner": "2"}).status_code == 400','Supplied owner rejected before provider/storage access'),
]

# NFR, path, case, assertion, purpose, exact scope/remaining limit
NFR = [
('01',S,'test_every_protected_method_rejects_invalid_tokens_without_writes','assert unchanged','Every personal method, both prefixes, invalid JWT variants: denied/no writes/no provider call','OpenAPI matrix completeness and foreign-ID parameterized cases are separate tests in the same file.'),
('02',S,'test_seeded_credentials_absent_from_storage_errors_and_captured_logs','assert not leaked','Salted Argon2id verified; seeded password/JWT/signing/provider markers absent from responses/logs','Seeded-marker inspection and repository secret scan do not certify external platform logs.'),
('03','tests/performance/non_ai_http.py','<module>',"value['p95_ms']<=500",'50 users/100 inventory rows each/four GET routes/300 seconds; per-route and aggregate p95<=500ms, errors<1%','Evaluate actual named environment only. Older local/CI numbers have distinct source SHAs.'),
('04','backend/tests/test_default_timeout.py','test_production_timeout_cancels_stalled_provider_within_thirty_seconds',"assert elapsed<30 and state['cancelled']",'28-second default deadline: cancelled provider, retryable503, five unchanged collections','Additional generation load checks five concurrent deadlines/no partial persisted recipes; not live inference.'),
('05',B,'core screens fit ${width}px','document.documentElement.scrollWidth <= window.innerWidth','360/768/1440px: six core pages/headings visible without horizontal overflow','Completion browser cases separately cover validation and unavailable states at all three widths.'),
('06',B,'core kitchen actions work with keyboard-only input','throw new Error("Core control could not be reached with Tab")','Tab/Enter/type-only registration, fridge, preferences, recipes, favorites and shopping','Axe labels/error associations and explicit focus tests supplement automated walkthrough; no human usability audit claimed.'),
('07','backend/tests/test_process_persistence.py','test_two_process_restart_preserves_two_users_and_five_collections',"assert all(item['passed'] for item in evidence)",'Different write/read processes preserve two accounts and all five collections','SQLite and PostgreSQL parameters; PostgreSQL requires TEST_DATABASE_URL and any skipped variant must be disclosed.'),
('08',R,'test_invalid_recipe_rejects_whole_batch','assert a.counts() == (0, 0, 0)','Single-field invalid numbers/ingredients/steps and declared allergen conflict reject whole batch without partial rows','Browser US-08 mappings verify estimate labels/list review; nutrition truth and undeclared allergens outside fixture evidence.'),
('09','tests/cloud/smoke.py','<module>','assert after == before','Production container/PostgreSQL restart preserves committed resources; actual CI builds/tests it','Historical HTTPS smoke is source a59556e. This fix branch is not claimed deployed; no production scan/load.'),
]


def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args])


def resolve(path, case, needle, revision):
    source = git('show',f'{revision}:{path}').decode('utf-8').replace('\r\n','\n')
    if source != (ROOT/path).read_text(encoding='utf-8'):
        raise ValueError('Assertion source differs from immutable revision: '+path)
    start, end = 0, len(source)
    if case != '<module>':
        if path.endswith('.py'):
            node = next(n for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==case)
            lines=source.splitlines(keepends=True)
            start,end=sum(map(len,lines[:node.lineno-1])),sum(map(len,lines[:node.end_lineno]))
        else:
            start=source.index(case)
            pattern = r'^\s*test\([\'\"]' if case=='US-08-T02' else r'^\s*test\('
            following=re.search(pattern,source[start+len(case):],re.MULTILINE)
            if following: end=start+len(case)+following.start()
    position=source.find(needle,start,end)
    if position<0: raise ValueError(f'Missing assertion {path}: {case}: {needle}')
    line=source.count('\n',0,position)+1
    return {'path':path,'case':case,'assertion':needle,'line':line,'source_revision':revision,
        'source_link':f'{REPO}/blob/{revision}/{path}#L{line}'}


def unique_ids(source):
    ids=[a or b for a,b in re.findall(r"test\(['\"](US-\d{2}-T\d{2})|^\s*\['(US-\d{2}-T\d{2})'",source,re.MULTILINE)]
    if not ids or len(ids)!=len(set(ids)): raise ValueError('Missing or duplicate physical test IDs')
    return len(ids)


def build(revision):
    if not re.fullmatch('[0-9a-f]{40}',revision): raise ValueError('Use full source SHA')
    count=unique_ids((ROOT/F).read_text(encoding='utf-8'))
    rows=[]
    for story,index,path,case,needle,purpose in AC:
        criteria=re.findall(r'^\d+\. (Given .+)$',(ROOT/f'docs/requirements/US-{story}.md').read_text(encoding='utf-8'),re.MULTILINE)
        rows.append({'requirement':'US-'+story,'criterion':f'AC-{index:02}', 'acceptance_criterion':criteria[index-1],
            **resolve(path,case,needle,revision),'verifies':purpose,'scope':'Mapping only; consult source-qualified CI outcome.'})
    nfr_text=(ROOT/'docs/requirements/non-functional.md').read_text(encoding='utf-8')
    for number,path,case,needle,purpose,scope in NFR:
        criterion=re.search(r'## NFR-'+number+r'.*?\*\*Criterion:\*\* ([^\n]+)',nfr_text,re.DOTALL)[1]
        rows.append({'requirement':'NFR-'+number,'criterion':'Criterion','acceptance_criterion':criterion,
            **resolve(path,case,needle,revision),'verifies':purpose,'scope':scope})
    if len(rows)!=57 or len({(r['requirement'],r['criterion']) for r in rows})!=57:
        raise ValueError('Expected 48 unique ACs and nine NFRs')
    return rows,count


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/tests/coverage');args=parser.parse_args()
    rows,count=build(args.revision)
    target=args.output;target.mkdir(parents=True,exist_ok=True)
    with (target/'traceability.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    (target/'traceability.json').write_text(json.dumps({'assertion_revision':args.revision,'acceptance_criteria':48,
        'nfr_criteria':9,'unique_physical_acceptance_ids':count,'rows':rows},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# Criterion and assertion traceability','',f'Assertion source: `{args.revision}`. 48 ACs, nine NFRs, {count} unique physical acceptance IDs.',
        'Each row names its concrete assertion and purpose. Reusing a case for several criteria is explicit; IDs are never reassigned.',
        'Mappings are not test pass counts. Use same-source JUnit/CI evidence or a retained test-source equivalence proof.',
        'Controlled provider tests do not certify live inference, nutrition or undeclared allergens.','',
        '| Criterion | Case / concrete verification | Assertion |','|---|---|---|']
    for r in rows: lines.append(f'| {r["requirement"]}/{r["criterion"]} | `{r["case"]}`: {r["verifies"]} | [L{r["line"]}]({r["source_link"]}) |')
    lines+=['','## Non-functional scope','']+[f'- **{r["requirement"]}:** {r["scope"]}' for r in rows if r['requirement'].startswith('NFR')]
    (target/'traceability.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Validated 48 AC + nine NFR mappings; {count} unique physical IDs')


if __name__=='__main__': main()

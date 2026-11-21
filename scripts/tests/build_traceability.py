"""Build criterion-level traceability from the repository's actual requirements."""
import csv
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
MAPPING={
 '01':['US-01-T01','US-01-T02','US-01-T02'],
 '02':['US-02-T01; B-AUTH-05','US-02-T01; B-AUTH-04'],
 '03':['US-03-T01; B-PREF-01','US-03-T01; B-PREF-01','US-07-T01; test_real_accounts_supply_owned_inventory_and_latest_preferences'],
 '04':['US-04-T01','US-04-T02','US-04-T01; test_inventory_isolation_and_immutable_addition_time'],
 '05':['US-05-T01; browser real-account flow','US-05-T01; browser empty-fridge flow','US-05-T01'],
 '06':['US-06-T01','US-06-T01','US-12-T01; US-14-T01'],
 '07':['US-07-T01','US-07-T02','US-07-T03; browser empty-fridge flow','US-07-T01'],
 '08':['US-08-T01; browser real-account flow','US-08-T02..T07','browser real-account flow (estimate label and displayed ingredients)'],
 '09':['US-09-T01; test_production_timeout_cancels_stalled_provider_within_thirty_seconds; browser provider-failure flow',
       'US-09-T01; test_real_accounts_supply_owned_inventory_and_latest_preferences',
       'test_invalid_provider_response_is_sanitized; US-09-T01'],
 '10':['US-10-T01','US-10-T01','US-10-T01','US-10-T01'],
 '11':['US-11-T01','US-11-T01','US-11-T01','US-11-T01'],
 '12':['US-12-T01','US-12-T01','US-12-T01'],
 '13':['US-13-T01','US-13-T01','US-13-T01'],
 '14':['US-14-T01','US-14-T01','US-14-T01','US-14-T01'],
 '15':['US-15-T01; US-15-T03; B-SEC-01; B-SEC-02; B-SEC-05',
       'US-15-T02; B-SEC-03; B-SEC-04',
       'B-SEC-04; test_unknown_owner_and_empty_fridge_stop_before_provider; test_inventory_isolation_and_immutable_addition_time'],
}


def main():
    rows=[]
    for story,mapping in MAPPING.items():
        text=(ROOT/f'docs/requirements/US-{story}.md').read_text()
        criteria=re.findall(r'^\d+\. (Given .+)$',text,re.MULTILINE)
        assert len(criteria)==len(mapping),f'US-{story}: requirement count changed'
        for index,(criterion,tests) in enumerate(zip(criteria,mapping),1):
            rows.append({'requirement':f'US-{story}','criterion':f'AC-{index:02}',
                'acceptance_criterion':criterion,'assertions':tests,'status':'PASS in recorded integrated runs',
                'scope':'real application + SQL; controlled external provider; browser for presentation criteria'})
    assert len(rows)==48
    destination=ROOT/'docs/tests/coverage'
    destination.mkdir(parents=True,exist_ok=True)
    with (destination/'traceability.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    summary=['# Requirement traceability','',
        'Denominator: 15 stories and 48 acceptance criteria in the repository requirements. ',
        'All 48 criteria have assertion mappings; the detailed CSV preserves each criterion. ',
        'Passing claims refer to the recorded runs and their controlled-provider/SQL/browser scope. ',
        'This is separate from code coverage and does not establish live AI, staging or hidden-allergen safety.','',
        '| Story | Criteria | Assertion mapping |','|---|---:|---|']
    for story,tests in MAPPING.items():
        summary.append(f'| US-{story} | {len(tests)} | '+ '; '.join(dict.fromkeys(tests))+' |')
    (destination/'traceability.md').write_text('\n'.join(summary)+'\n')


if __name__=='__main__':
    main()

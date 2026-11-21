"""Enforce explicit source-coverage floors on actual exported runner reports."""
import argparse
import json
from pathlib import Path

FLOORS = {'backend_statements':90,'backend_branches':70,
    'frontend_lines':90,'frontend_branches':85,'frontend_functions':85}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results',default='test-results')
    parser.add_argument('--backend')
    parser.add_argument('--output',default='test-results/coverage-gate.json')
    args = parser.parse_args()
    directory = Path(args.results)
    backend = json.loads(Path(args.backend or directory/'backend-coverage.json').read_text())['totals']
    frontend = json.loads((directory/'frontend-coverage/coverage-summary.json').read_text())['total']
    actual = {'backend_statements':backend['percent_statements_covered'],
        'backend_branches':backend['percent_branches_covered'],
        **{f'frontend_{metric}':frontend[metric]['pct'] for metric in ['lines','branches','functions']}}
    passed = all(type(actual[key]) in (int,float) and floor <= actual[key] <= 100 for key,floor in FLOORS.items())
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'passed':passed,'actual_percent':actual,'minimum_percent':FLOORS,
        'scope':'backend production source and mapped frontend/src; statement coverage is separate from branches'},indent=2)+'\n')
    print('Coverage policy: '+('PASS' if passed else 'FAIL'))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

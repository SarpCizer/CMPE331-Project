"""Bounded seeded source mutations; no production host or real AI calls.

This is a targeted fault-detection experiment, not whole-project mutation coverage.
Each valid mutant runs in a fresh temporary copy, after a passing baseline.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
PROVIDER = 'backend/src/fridgely_recipes/provider.py'
SERVICE = 'backend/src/fridgely_recipes/service.py'
LOGIN = 'backend/src/fridgely_app/login_throttle.py'
PARALLEL_TESTS = ['backend/tests/test_parallel_generation.py']
METRIC_TESTS = ['backend/tests/test_metric_recipe_amounts.py', 'backend/tests/test_generation_output_reliability.py']
LOGIN_TESTS = ['backend/tests/test_login_throttle.py']
SERVICE_TESTS = ['backend/tests/test_recipe_integration.py', 'backend/tests/test_recipe_moods.py']
# One syntactically valid change per mutant, selected before measuring results.
MUTANTS = [
    ('M01', PROVIDER, 'len(data.ingredients) < 6', 'len(data.ingredients) < 600', PARALLEL_TESTS),
    ('M02', PROVIDER, 'for offset in range(2)', 'for offset in range(1)', PARALLEL_TESTS),
    ('M03', PROVIDER, 'if signature not in seen:', 'if True:', PARALLEL_TESTS),
    ('M04', PROVIDER, 'body["priorityIngredients"] = priorities', 'body["priorityIngredients"] = data.ingredients', PARALLEL_TESTS),
    ('M05', PROVIDER, "return format(number.normalize(), 'f') + ' ' + unit", "return format(number.normalize(), 'f') + ' g'", METRIC_TESTS),
    ('M06', PROVIDER, 'converted = [metric_amount(amount) for amount in amounts]', 'converted = ["1 g" for amount in amounts]', METRIC_TESTS),
    ('M07', PROVIDER, 'not 0 < value <= 1000000', 'not -1 < value <= 1000000', METRIC_TESTS),
    ('M08', SERVICE, 'if not data.ingredients:', 'if False:', SERVICE_TESTS),
    ('M09', SERVICE, 'exclusions = {name.strip().casefold() for name in allergens}', 'exclusions = set()', SERVICE_TESTS),
    ('M10', SERVICE, 'recipe.cookingMinutes > limit', 'recipe.cookingMinutes < limit', SERVICE_TESTS),
    ('M11', LOGIN, 'account_limit=5', 'account_limit=6', LOGIN_TESTS),
    ('M12', LOGIN, 'events[0] <= now - self.window', 'events[0] >= now - self.window', LOGIN_TESTS),
    ('M13', LOGIN, "self._buckets.pop(('account', source, email), None)", "self._buckets.get(('account', source, email), None)", LOGIN_TESTS),
    ('M14', LOGIN, 'if retry or len(self._buckets)', 'if False or len(self._buckets)', LOGIN_TESTS),
]


def run_tests(path, tests):
    env = os.environ.copy()
    for name in ('TEST_DATABASE_URL', 'DATABASE_URL', 'CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_AI_TOKEN', 'OPENAI_API_KEY'):
        env.pop(name, None)
    env['PYTHONPATH'] = str(path / 'backend/src')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # Editable installations must never redirect a mutant to the original module.
    probe = subprocess.run([sys.executable, '-c',
        'from pathlib import Path; import fridgely_recipes.provider as p; '
        'assert Path(p.__file__).resolve().is_relative_to(Path.cwd())'],
        cwd=path, env=env, capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError('Mutation isolation preflight failed')
    started = time.monotonic()
    try:
        result = subprocess.run([sys.executable, '-m', 'pytest', *tests, '-q', '--tb=no', '-p', 'no:cacheprovider'],
            cwd=path, env=env, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'seconds': round(time.monotonic() - started, 3)}
    failed = re.findall(r'^FAILED ([^\s]+)', result.stdout, flags=re.MULTILINE)
    return {
        'status': 'survived' if result.returncode == 0 else ('killed' if result.returncode == 1 and failed else 'invalid'),
        'returncode': result.returncode, 'seconds': round(time.monotonic() - started, 3),
        'failed_tests': failed,
        'summary': re.findall(r'^.*\d+ (?:passed|failed).*$', result.stdout, flags=re.MULTILINE)[-1:],
    }


def campaign(revision):
    files = {row[1]: (ROOT / row[1]).read_text() for row in MUTANTS}
    tests = sorted({test for row in MUTANTS for test in row[4]})
    for test in tests:
        if not (ROOT / test).is_file():
            raise RuntimeError(f'Missing test: {test}')
    with tempfile.TemporaryDirectory(prefix='fridgely-mutation-') as directory:
        path = Path(directory)
        shutil.copytree(ROOT / 'backend', path / 'backend', ignore=shutil.ignore_patterns('__pycache__', '*.db', '*.egg-info'))
        baseline = run_tests(path, tests)
        if baseline['status'] != 'survived':
            raise RuntimeError(f'Baseline must pass before mutation: {baseline}')
        rows = []
        for identity, name, old, new, selected in MUTANTS:
            original = files[name]
            if original.count(old) != 1:
                raise RuntimeError(f'{identity}: mutation anchor must occur exactly once')
            mutated = original.replace(old, new, 1)
            ast.parse(mutated)
            target = path / name
            target.write_text(mutated)
            try:
                result = run_tests(path, selected)
            finally:
                target.write_text(original)
            row = {'id': identity, 'path': name, 'line': original[:original.index(old)].count('\n') + 1,
                   'before': old, 'after': new, 'tests': selected, **result}
            rows.append(row)
            print(f'{identity}: {result["status"]}', flush=True)
    counts = {status: sum(row['status'] == status for row in rows) for status in ('killed', 'survived', 'invalid', 'timeout')}
    denominator = counts['killed'] + counts['survived']
    return {'revision': revision, 'scope': '14 seeded source mutations in recipe validation/concurrency and login throttling',
            'whole_project_mutation_coverage': False, 'real_provider_used': False, 'baseline': baseline,
            'source_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in files.items()},
            'counts': counts, 'score': counts['killed'] / denominator if denominator else None, 'mutants': rows,
            'passed': counts['killed'] == len(rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = campaign(args.revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

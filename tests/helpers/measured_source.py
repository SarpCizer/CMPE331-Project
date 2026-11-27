"""Reject accidental relabelling of load/security evidence to another checkout."""
from pathlib import Path
import re
import subprocess


def verified_revision(root, declared):
    root = Path(root).resolve()
    git = ['git', '-c', 'safe.directory=' + str(root), '-C', str(root)]
    actual = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', declared) or declared != actual:
        raise ValueError('Measured revision must equal the current full Git HEAD')
    scope = ['backend', 'frontend/src', 'frontend/package.json', 'frontend/pnpm-lock.yaml',
             'tests/performance', 'tests/security', 'tests/helpers']
    dirty = subprocess.check_output(git + ['status', '--porcelain', '--untracked-files=all', '--', *scope], text=True)
    if dirty.strip():
        raise ValueError('Commit application/test changes before recording measured source evidence')
    return actual

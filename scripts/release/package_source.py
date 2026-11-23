"""Build the course source-only archive; never bundle environments or credentials."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {'.git','.venv','node_modules','__pycache__','.pytest_cache',
    'test-results','playwright-report','dist','build','.scannerwork'}
SUFFIXES = {'.py','.mjs','.js','.jsx','.css','.html','.json','.yaml','.yml',
    '.toml','.lock','.txt','.md','.puml','.mmd','.sh','.csv'}
SPECIAL = {'.gitignore','.dockerignore','.gitleaksignore','.coveragerc','.env.example','Dockerfile'}


def included(path):
    if str(path) == 'SUBMISSION-MANIFEST.json':
        return False
    if any(part in EXCLUDED or part.endswith('.egg-info') for part in path.parts):
        return False
    if path.name.startswith('.env') and path.name != '.env.example':
        return False
    if path.parts[:3] == ('docs','tests','evidence'):
        return False
    if path.parts[:2] == ('docs','tests') and path.suffix not in {'.md','.csv'}:
        return False
    return path.name in SPECIAL or path.suffix.lower() in SUFFIXES


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def source_entries(revision):
    for entry in git('ls-tree', '-rz', revision).split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.split(b'\t', 1)
        mode, _kind, blob = metadata.decode('ascii').split()
        if mode not in {'100644', '100755'}:
            continue
        path = PurePosixPath(name.decode('utf-8'))
        if included(path):
            yield path.as_posix(), int(mode, 8), blob


def write_entry(archive, name, contents, mode=0o100644):
    entry = zipfile.ZipInfo('Fridgely/' + name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.create_system = 3  # Unix file modes, regardless of the build machine.
    entry.external_attr = mode << 16
    archive.writestr(entry, contents, compress_type=zipfile.ZIP_DEFLATED)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision',required=True,help='Reviewed GitHub source SHA, not a reconstructed local commit')
    parser.add_argument('--output',default=str(ROOT/'build/release/Fridgely-source-0.1.0.zip'))
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.revision):
        parser.error('Use a complete 40-character source revision')
    try:
        resolved = git('rev-parse', '--verify', args.revision + '^{commit}').decode('ascii').strip()
    except subprocess.CalledProcessError:
        parser.error('The reviewed commit must exist in this Git checkout')
    if resolved != args.revision:
        parser.error('Provide the SHA of the commit itself')

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    manifest = {'source_revision': args.revision, 'version': '0.1.0',
        'scope': 'source, documentation and deployment definitions; no libraries, databases, credentials, reports PDF or raster evidence',
        'files': files}
    with zipfile.ZipFile(output, 'w') as archive:
        for name, mode, blob in source_entries(resolved):
            contents = git('cat-file', 'blob', blob)
            files[name] = {'bytes': len(contents), 'sha256': hashlib.sha256(contents).hexdigest()}
            write_entry(archive, name, contents, mode)
        write_entry(archive, 'SUBMISSION-MANIFEST.json',
                    (json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(not name.endswith(('.db','.png','.pdf','.pyc')) for name in archive.namelist())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
    print(json.dumps({'archive':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':digest}))


if __name__ == '__main__':
    main()

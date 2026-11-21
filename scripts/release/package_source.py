"""Build the course source-only archive; never bundle environments or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {'.git','.venv','node_modules','__pycache__','.pytest_cache',
    'test-results','playwright-report','dist','build','.scannerwork'}
SUFFIXES = {'.py','.mjs','.js','.jsx','.css','.html','.json','.yaml','.yml',
    '.toml','.lock','.txt','.md','.puml','.mmd','.sh','.csv'}
SPECIAL = {'.gitignore','.dockerignore','.gitleaksignore','.coveragerc','.env.example','Dockerfile'}


def included(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED or part.endswith('.egg-info') for part in relative.parts):
        return False
    if path.name.startswith('.env') and path.name != '.env.example':
        return False
    if relative.parts[:3] == ('docs','tests','evidence'):
        return False
    if relative.parts[:2] == ('docs','tests') and path.suffix not in {'.md','.csv'}:
        return False
    return path.name in SPECIAL or path.suffix.lower() in SUFFIXES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision',required=True,help='Reviewed GitHub source SHA, not a reconstructed local commit')
    parser.add_argument('--output',default=str(ROOT/'build/release/Fridgely-source-0.1.0.zip'))
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.revision):
        parser.error('Use a complete 40-character source revision')
    files = sorted(path for path in ROOT.rglob('*') if path.is_file() and included(path))
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    manifest = {'source_revision':args.revision,'version':'0.1.0',
        'scope':'source, documentation and deployment definitions; no libraries, databases, credentials, reports PDF or raster evidence',
        'files':{str(path.relative_to(ROOT)):{'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in files}}
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.writestr('Fridgely/'+str(path.relative_to(ROOT)),path.read_bytes())
        archive.writestr('Fridgely/SUBMISSION-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all(not name.endswith(('.db','.png','.pdf','.pyc')) for name in archive.namelist())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
    print(json.dumps({'archive':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':digest}))


if __name__ == '__main__':
    main()

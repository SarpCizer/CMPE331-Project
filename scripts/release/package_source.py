"""Build the course source-only archive; never bundle environments or credentials."""
import argparse
import hashlib
import io
import json
import os
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
ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)


def included(path):
    relative = PurePosixPath(path)
    if any(part in EXCLUDED or part.endswith('.egg-info') for part in relative.parts):
        return False
    if relative.name.startswith('.env') and relative.name != '.env.example':
        return False
    if relative.parts[:3] == ('docs','tests','evidence'):
        return False
    if relative.parts[:2] == ('docs','tests') and relative.suffix not in {'.md','.csv'}:
        return False
    return relative.name in SPECIAL or relative.suffix.lower() in SUFFIXES


def git_read(*arguments, payload=None):
    env = {**os.environ, 'GIT_NO_LAZY_FETCH':'1', 'GIT_OPTIONAL_LOCKS':'0'}
    for name in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_NAMESPACE'):
        env.pop(name, None)
    return subprocess.run(['git','-C',str(ROOT),*arguments], input=payload,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, env=env).stdout


def committed_sources(revision):
    if Path(git_read('rev-parse','--show-toplevel').decode().strip()).resolve() != ROOT.resolve():
        raise ValueError('Use the project Git checkout, not a copy inside another repository')
    resolved = git_read('rev-parse','--verify',revision+'^{commit}').decode().strip()
    if resolved != revision:
        raise ValueError('The full revision must identify a commit directly')
    entries, tracked = [], []
    for record in git_read('ls-tree','-r','-z','--full-tree',revision).split(b'\0'):
        if not record:
            continue
        header, raw_path = record.split(b'\t',1)
        mode, kind, object_id = header.decode('ascii').split()
        name = raw_path.decode('utf-8')
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('Commit contains a path unsafe for a portable ZIP')
        tracked.append(name)
        if mode in {'100644','100755'} and kind == 'blob' and included(name):
            if name == 'SUBMISSION-MANIFEST.json':
                raise ValueError('The generated archive manifest path is reserved')
            entries.append((name, mode, object_id))
    ids = list(dict.fromkeys(row[2] for row in entries))
    blobs = {}
    if ids:
        stream = io.BytesIO(git_read('cat-file','--batch',payload=('\n'.join(ids)+'\n').encode()))
        for expected in ids:
            header = stream.readline().decode('ascii').strip().split()
            if len(header) != 3 or header[:2] != [expected,'blob']:
                raise ValueError('A declared source blob is unavailable locally')
            size = int(header[2])
            data = stream.read(size)
            if len(data) != size or stream.read(1) != b'\n':
                raise ValueError('A source blob could not be read completely')
            blobs[expected] = data
    return [(name,mode,blobs[oid]) for name,mode,oid in sorted(entries)], tracked


def archive_entry(name, mode):
    info = zipfile.ZipInfo('Fridgely/'+name, date_time=ARCHIVE_TIME)
    info.create_system = 3
    info.external_attr = (0o100755 if mode == '100755' else 0o100644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision',required=True,help='Reviewed GitHub source SHA, not a reconstructed local commit')
    parser.add_argument('--output',default=str(ROOT/'build/release/Fridgely-source-0.1.0.zip'))
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.revision):
        parser.error('Use a complete 40-character source revision')
    try:
        files, tracked = committed_sources(args.revision)
        output = Path(args.output).resolve()
        checksum = output.with_suffix('.zip.sha256')
        git_dir = Path(git_read('rev-parse','--absolute-git-dir').decode().strip()).resolve()
        # Guard current index paths too when the requested revision precedes HEAD.
        tracked.extend(name.decode('utf-8') for name in git_read('ls-files','-z').split(b'\0') if name)
        source_paths = {(ROOT/name).resolve() for name in tracked}
        if any(path in source_paths or path.is_relative_to(git_dir) for path in (output,checksum)):
            parser.error('Archive output must not overwrite tracked source or Git metadata')
    except (OSError,subprocess.CalledProcessError,UnicodeError,ValueError) as error:
        if isinstance(error,ValueError) and not isinstance(error,UnicodeError):
            parser.error(str(error))
        parser.error('Cannot read the declared commit. Use Git and fetch its objects into the project checkout first')
    output.parent.mkdir(parents=True,exist_ok=True)
    manifest = {'source_revision':args.revision,'version':'0.1.0',
        'scope':'source, documentation and deployment definitions; no libraries, databases, credentials, reports PDF or raster evidence',
        'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':mode}
                 for name,mode,data in files}}
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,mode,data in files:
            archive.writestr(archive_entry(name,mode),data,compresslevel=9)
        archive.writestr(archive_entry('SUBMISSION-MANIFEST.json','100644'),
            json.dumps(manifest,indent=2,sort_keys=True)+'\n',compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive integrity verification failed')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum.write_text(digest+'  '+output.name+'\n')
    print(json.dumps({'archive':str(output),'files':len(files),'bytes':output.stat().st_size,'sha256':digest}))


if __name__ == '__main__':
    main()

"""Regression tests for the course source archive."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from zipfile import ZipFile


class PackageSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.script = self.repo / 'scripts/release/package_source.py'
        self.script.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).with_name('package_source.py'), self.script)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Archive Test')
        self.git('config', 'user.email', 'archive@example.test')
        self.source = self.repo / 'source.txt'
        self.source.write_bytes(b'reviewed\n')
        (self.repo / '.env').write_text('TEST=fixture\n')
        (self.repo / 'linked.txt').symlink_to('source.txt')
        self.git('add', '.')
        self.git('commit', '-qm', 'Reviewed source')
        self.revision = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo, text=True)

    def package(self, name, revision=None):
        archive = self.root / name
        result = subprocess.run(
            [sys.executable, str(self.script), '--revision', revision or self.revision,
             '--output', str(archive)],
            cwd=self.repo, capture_output=True, text=True,
        )
        return archive, result

    def test_archive_uses_only_files_from_the_requested_commit(self):
        self.source.write_bytes(b'later commit\n')
        (self.repo / 'later.txt').write_bytes(b'later file\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'Later source')
        self.source.write_bytes(b'dirty working copy\n')
        (self.repo / 'untracked.txt').write_bytes(b'untracked\n')

        path, result = self.package('source.zip')
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                'Fridgely/source.txt', 'Fridgely/scripts/release/package_source.py',
                'Fridgely/SUBMISSION-MANIFEST.json',
            })
            data = archive.read('Fridgely/source.txt')
            self.assertEqual(data, b'reviewed\n')
            manifest = json.loads(archive.read('Fridgely/SUBMISSION-MANIFEST.json'))
            self.assertEqual(manifest['source_revision'], self.revision)
            self.assertEqual(manifest['files']['source.txt'], {
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            })

    def test_repeated_builds_have_identical_bytes_and_valid_digest(self):
        first, result = self.package('first.zip')
        self.assertEqual(result.returncode, 0, result.stderr)
        time.sleep(2.1)  # The legacy ZIP timestamp has two-second resolution.
        second, result = self.package('second.zip')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(first.with_suffix('.zip.sha256').read_text().split()[0],
                         hashlib.sha256(first.read_bytes()).hexdigest())

    def test_missing_commit_fails_without_creating_output(self):
        path, result = self.package('missing.zip', 'f' * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()

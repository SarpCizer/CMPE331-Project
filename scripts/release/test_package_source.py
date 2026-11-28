"""Verify release bytes come from Git objects, independent of the working tree."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import package_source


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fridgely-archive-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        self.git("init", "--quiet")
        self.write("app.py", b"print('committed version one')\n")
        self.write("README.md", b"Committed documentation\n")
        self.write("first-revision.txt", b"Only in the first revision\n")
        self.write("run.sh", b"#!/bin/sh\nexit 0\n")
        self.write('backend/pyproject.toml',b'[project]\nversion = "0.1.0"\n')
        self.write('frontend/package.json',b'{"version":"0.1.0"}\n')
        (self.repo / "run.sh").chmod(0o755)
        self.revision = self.commit("First fixture revision")

    def git(self, *arguments):
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        result = subprocess.run(
            ["git", "-c", "user.name=Archive Fixture", "-c", "user.email=fixture@example.test",
             "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
             "-c", "core.autocrlf=false", "-C", str(self.repo), *arguments],
            env=env, capture_output=True, check=True,
        )
        return result.stdout.decode().strip()

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def commit(self, message):
        self.git("add", "--all")
        # Git's committed mode is the portable contract; NTFS chmod alone does
        # not mark an executable when core.filemode is false.
        if (self.repo / "run.sh").exists():
            self.git("update-index", "--chmod=+x", "run.sh")
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")

    def build(self, name="source.zip", revision=None, root=None):
        output = self.directory / name
        arguments = ["package_source.py", "--revision", revision or self.revision,
                     "--output", str(output)]
        with patch.object(package_source, "ROOT", root or self.repo), \
                patch.object(sys, "argv", arguments), contextlib.redirect_stdout(io.StringIO()):
            package_source.main()
        return output

    def test_requested_revision_survives_dirty_checkout_and_different_head(self):
        self.write("app.py", b"print('committed version two')\n")
        (self.repo / "first-revision.txt").unlink()
        self.write("later.txt", b"Added in a later commit\n")
        later = self.commit("Second fixture revision")
        self.write("app.py", b"print('uncommitted edit')\n")
        self.write("local-review-only.txt", b"Untracked review fixture\n")
        before = self.git("status", "--porcelain")
        output = self.build()
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("Fridgely/app.py"), b"print('committed version one')\n")
            self.assertIn("Fridgely/first-revision.txt", archive.namelist())
            self.assertNotIn("Fridgely/later.txt", archive.namelist())
            self.assertNotIn("Fridgely/local-review-only.txt", archive.namelist())
            manifest = json.loads(archive.read("Fridgely/SUBMISSION-MANIFEST.json"))
            self.assertEqual(manifest["source_revision"], self.revision)
            for path, metadata in manifest["files"].items():
                payload = archive.read("Fridgely/" + path)
                self.assertEqual(metadata["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(metadata["bytes"], len(payload))
        self.assertEqual(self.git("rev-parse", "HEAD"), later)
        self.assertEqual(self.git("status", "--porcelain"), before)

    def test_manifest_version_comes_from_requested_commit_not_working_checkout(self):
        self.write('backend/pyproject.toml',b'[project]\nversion = "0.6.0"\n')
        self.write('frontend/package.json',b'{"version":"0.6.0"}\n')
        selected = self.commit('Release 0.6.0 fixture')
        self.write('backend/pyproject.toml',b'[project]\nversion = "0.7.0"\n')
        self.write('frontend/package.json',b'{"version":"0.7.0"}\n')
        with zipfile.ZipFile(self.build(revision=selected)) as archive:
            manifest = json.loads(archive.read('Fridgely/SUBMISSION-MANIFEST.json'))
            self.assertEqual(manifest['version'],'0.6.0')
            self.assertEqual(manifest['source_revision'],selected)

    def test_conflicting_committed_component_versions_fail_before_archive_creation(self):
        self.write('frontend/package.json',b'{"version":"0.7.0"}\n')
        selected = self.commit('Inconsistent fixture versions')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.build(revision=selected)
        self.assertFalse((self.directory/'source.zip').exists())

    def test_same_revision_has_identical_digest_and_normalized_metadata(self):
        with patch.object(zipfile.time, "localtime", return_value=(2020, 1, 1, 0, 0, 0, 2, 1, -1)):
            first = self.build("first.zip")
        (self.repo / "run.sh").chmod(0o600)
        with patch.object(zipfile.time, "localtime", return_value=(2024, 6, 2, 3, 4, 6, 6, 154, -1)):
            second = self.build("second.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as archive:
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                expected = 0o100755 if info.filename == "Fridgely/run.sh" else 0o100644
                self.assertEqual(info.external_attr >> 16, expected)
        digest = hashlib.sha256(first.read_bytes()).hexdigest()
        self.assertEqual(first.with_suffix(".zip.sha256").read_text(), digest + "  first.zip\n")

    def test_unknown_revision_is_rejected_before_writing_output(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.build(revision="f" * 40)
        self.assertFalse((self.directory / "source.zip").exists())

    def test_non_repository_is_rejected_before_writing_output(self):
        other = self.directory / "not-a-repository"
        other.mkdir()
        (other / "app.py").write_text("print('not committed')\n")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.build(root=other)
        self.assertFalse((self.directory / "source.zip").exists())

    def test_regular_git_blobs_only_never_follow_tracked_symlinks(self):
        external = self.directory / "outside.txt"
        external.write_text("Outside checkout test fixture\n")
        # Model a tracked Git symlink directly, including Windows checkouts
        # where core.symlinks=false represents it as a regular target-path file.
        # This still makes the old working-tree packager include linked.py.
        self.write("linked.py", str(external).encode("utf-8"))
        blob = self.git("hash-object", "-w", "linked.py")
        self.git("update-index", "--add", "--cacheinfo", "120000", blob, "linked.py")
        self.git("commit", "--quiet", "-m", "Track a symlink fixture")
        revision = self.git("rev-parse", "HEAD")
        with zipfile.ZipFile(self.build(revision=revision)) as archive:
            self.assertNotIn("Fridgely/linked.py", archive.namelist())
            self.assertIn("Fridgely/app.py", archive.namelist())

    def test_output_cannot_overwrite_tracked_source(self):
        before = (self.repo / "app.py").read_bytes()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.build(name=str(self.repo / "app.py"))
        self.assertEqual((self.repo / "app.py").read_bytes(), before)

    def test_checksum_cannot_follow_a_symlink_to_tracked_source(self):
        source = self.repo / "README.md"
        before = source.read_bytes()
        checksum = self.directory / "source.zip.sha256"
        try:
            checksum.symlink_to(source)
        except (OSError, NotImplementedError):
            self.skipTest("Creating local symlinks requires platform support")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.build()
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((self.directory / "source.zip").exists())

    def test_release_filter_keeps_sources_and_excludes_local_or_generated_data(self):
        for name in ["node_modules/library.js", ".env.production", "stored.db",
                     "build/output.py", "docs/tests/evidence/raw.txt", "docs/tests/report.pdf"]:
            self.write(name, b"excluded fixture\n")
        self.write(".env.example", b"EXAMPLE_VALUE=placeholder\n")
        self.write("docs/tests/coverage/traceability.csv", b"story,test\nUS-01,T01\n")
        revision = self.commit("Track filter fixtures")
        with zipfile.ZipFile(self.build(revision=revision)) as archive:
            names = archive.namelist()
            for name in ["node_modules/library.js", ".env.production", "stored.db",
                         "build/output.py", "docs/tests/evidence/raw.txt", "docs/tests/report.pdf"]:
                self.assertNotIn("Fridgely/" + name, names)
            self.assertIn("Fridgely/.env.example", names)
            self.assertIn("Fridgely/docs/tests/coverage/traceability.csv", names)


if __name__ == "__main__":
    unittest.main()

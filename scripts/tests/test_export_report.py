"""Check that report exports cannot relabel evidence from another revision."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ReportEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fridgely-report-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "docs/tests", self.root / "docs/tests")
        target = self.root / "scripts/tests"
        target.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/tests/export_report.py", target)

    def export(self, destination):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/tests/export_report.py")],
            env={**os.environ, "FRIDGELY_REPORT_OUTPUT": str(destination)},
            capture_output=True, text=True,
        )

    def test_mismatched_revision_is_rejected_before_publishing(self):
        config = self.root / "docs/tests/report-input.json"
        data = json.loads(config.read_text())
        data["ci_revision"] = "0" * 40
        config.write_text(json.dumps(data))
        destination = self.root / "out"
        destination.mkdir()
        result = self.export(destination)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("source revision mismatch", result.stderr.lower())
        self.assertFalse((destination / "Fridgely-Software-Test-Report.pdf").exists())

    def test_valid_evidence_exports_to_a_new_nested_directory(self):
        destination = self.root / "build/review/nested"
        result = self.export(destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        pdf = destination / "Fridgely-Software-Test-Report.pdf"
        markdown = destination / "Fridgely-Software-Test-Report.md"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
        text = markdown.read_text()
        self.assertIn("a59556e366ffd65adf799bb8aa9bc47e95dea16e", text)
        self.assertIn("45474025963", text)
        self.assertIn("pending", text.lower())


if __name__ == "__main__":
    unittest.main()

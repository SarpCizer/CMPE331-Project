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
        for name in ("export_report.py", "export_verified_report.py", "review_follow_up.py"):
            shutil.copy2(ROOT / "scripts/tests" / name, target)

    def export(self, destination=None):
        environment = {**os.environ}
        environment.pop('FRIDGELY_REPORT_OUTPUT', None)
        if destination is not None:
            environment['FRIDGELY_REPORT_OUTPUT'] = str(destination)
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/tests/export_report.py")],
            env=environment, cwd=self.root.parent,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
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

    def test_default_export_creates_missing_build_and_writes_utf8(self):
        self.assertFalse((self.root / 'build').exists())
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / 'build/reports'
        self.assertTrue((output / 'Fridgely-Software-Test-Report.pdf').read_bytes().startswith(b'%PDF-'))
        text = (output / 'Fridgely-Software-Test-Report.md').read_text(encoding='utf-8')
        self.assertIn('Berfin Gökgöz', text)

    def test_report_labels_each_performance_revision_and_pins_browser_paths(self):
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.root / 'build/reports/Fridgely-Software-Test-Report.md').read_text(encoding='utf-8')
        for revision in ['9f43e3af07f08d070251e371fb6112c989db330e',
                         '25c111aa5a8d678b60c17745289675821b62f91d',
                         'a59556e366ffd65adf799bb8aa9bc47e95dea16e']:
            self.assertIn(revision, text)
        self.assertIn('44.35', text)
        self.assertIn('371.47', text)
        self.assertIn('204.06', text)
        self.assertIn('different revisions and environments', text.lower())
        for name in ['completion.spec.js', 'kitchen.spec.js', 'preferences-fidelity.spec.js', 'text-format.spec.js']:
            self.assertIn('/blob/a59556e366ffd65adf799bb8aa9bc47e95dea16e/frontend/tests/' + name, text)

    def test_follow_up_preserves_actual_revisions_outcomes_and_result_figures(self):
        config=json.loads((self.root/'docs/tests/review-follow-up.json').read_text(encoding='utf-8'))
        result=self.export()
        self.assertEqual(result.returncode,0,result.stderr)
        metadata=json.loads(result.stdout)
        self.assertEqual(metadata['follow_up_source'],config['source_revision'])
        self.assertEqual(metadata['follow_up_ci_run'],config['ci_run_id'])
        text=(self.root/'build/reports/Fridgely-Software-Test-Report.md').read_text(encoding='utf-8')
        self.assertIn(config['source_revision'],text)
        self.assertIn(config['local_source_revision'],text)
        for phrase in ['48 approved acceptance criteria','nine NFRs','Current browser inventory','false positives']:
            self.assertIn(phrase,text)
        evidence=self.root/'docs/tests'/config['evidence_root']
        local=json.loads((evidence/'local/non-ai-load.json').read_text(encoding='utf-8'))
        self.assertIn('Local NFR-03 profile: '+('PASS' if local['passed'] else 'FAIL'),text)
        issues=json.loads((evidence/'sonar/issues.json').read_text(encoding='utf-8'))['issues']
        self.assertIn(f'Current scan: {len(issues)} open issue(s)',text)
        if any(issue['rule']=='python:S8786' for issue in issues):
            self.assertIn('open performance finding',text)
        for name in ['review-coverage.svg','review-non-ai-performance.svg','review-generation-performance.svg']:
            self.assertIn(name,text)
            self.assertTrue((self.root/'docs/tests/figures'/name).is_file())
        self.assertIn('sonar/dashboard.png',text)

    def test_other_revision_inventory_is_rejected_before_output_creation(self):
        path = self.root / 'docs/tests/report-provenance.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['report_baseline_revision'] = '0' * 40
        path.write_text(json.dumps(data), encoding='utf-8')
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('inventory source revision mismatch', result.stderr.lower())
        self.assertFalse((self.root / 'build').exists())

    def test_relabelled_historical_load_is_rejected_before_output_creation(self):
        path = self.root / 'docs/tests/report-provenance.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['historical_loads'][0]['revision'] = data['report_baseline_revision']
        path.write_text(json.dumps(data), encoding='utf-8')
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('historical load revision mismatch', result.stderr.lower())
        self.assertFalse((self.root / 'build').exists())


class EvidenceCheckoutTests(unittest.TestCase):
    def test_hashed_evidence_retains_exact_bytes_with_autocrlf_enabled(self):
        git = shutil.which('git')
        self.assertIsNotNone(git, 'Git is required to verify checkout reproducibility')
        with tempfile.TemporaryDirectory(prefix='fridgely-evidence-checkout-') as directory:
            root = Path(directory)
            raw = root / 'docs/tests/evidence/sample.json'
            raw.parent.mkdir(parents=True)
            original = b'{"source":"retained-evidence"}\n'
            raw.write_bytes(original)
            shutil.copy2(ROOT / '.gitattributes', root / '.gitattributes')
            def command(*arguments):
                result = subprocess.run([git, '-C', str(root), *arguments], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            command('init', '--quiet')
            command('config', 'core.autocrlf', 'true')
            command('add', '.gitattributes', 'docs/tests/evidence/sample.json')
            raw.unlink()
            command('checkout-index', '--all', '--force')
            self.assertEqual(raw.read_bytes(), original, 'Checkout line-ending conversion changed hashed evidence')


if __name__ == "__main__":
    unittest.main()

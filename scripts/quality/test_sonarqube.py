"""Exercise the export boundary: failed or absent quality evidence must fail CI."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


SPEC = importlib.util.spec_from_file_location("sonarqube", Path(__file__).with_name("sonarqube.py"))
SONAR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SONAR)


class QualityGateTests(unittest.TestCase):
    def run_export(self, *, status="OK", conditions=None, measures=None):
        gate = {"projectStatus": {"status": status, "conditions": conditions or []}}
        metrics = {"component": {"measures": measures if measures is not None else [
            {"metric": name, "value": "0"}
            for name in ("bugs", "vulnerabilities", "security_hotspots")
        ]}}
        payloads = {
            "/task": {"task": {"status": "SUCCESS", "analysisId": "test-analysis"}},
            "/api/qualitygates/project_status": gate,
            "/api/measures/component": metrics,
            "/api/issues/search": {"issues": [], "paging": {"total": 0}},
            "/api/hotspots/search": {"hotspots": []},
        }
        session = Mock(headers={})
        session.get.side_effect = lambda url, **_: Mock(
            ok=True, json=lambda: payloads[url.removeprefix(SONAR.BASE)])
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                Path(".scannerwork").mkdir()
                Path(".scannerwork/report-task.txt").write_text(f"ceTaskUrl={SONAR.BASE}/task\n")
                with patch.object(SONAR.requests, "Session", return_value=session), \
                        patch.dict(os.environ, {"SONAR_TOKEN": "synthetic-analysis-token"}), \
                        contextlib.redirect_stdout(io.StringIO()):
                    try:
                        SONAR.export()
                    finally:
                        # Diagnostic exports must survive a rejected gate.
                        self.assertTrue(Path("test-results/sonarqube/quality-gate.json").is_file())
                        self.assertTrue(Path("test-results/sonarqube/metrics.json").is_file())
                policy = Path("test-results/sonarqube/quality-policy.json")
                return json.loads(policy.read_text()) if policy.exists() else None
            finally:
                os.chdir(previous)

    def test_reported_failed_gate_fails_export(self):
        with self.assertRaises(RuntimeError):
            self.run_export(status="ERROR")

    def test_absent_gate_fails_export(self):
        with self.assertRaises(RuntimeError):
            self.run_export(status="NONE")

    def test_unknown_gate_fails_export(self):
        with self.assertRaises(RuntimeError):
            self.run_export(status="UNAVAILABLE")

    def test_failed_condition_cannot_hide_behind_overall_ok(self):
        with self.assertRaises(RuntimeError):
            self.run_export(conditions=[{"status": "ERROR", "metricKey": "bugs"}])

    def test_missing_security_measure_fails_export(self):
        with self.assertRaises(RuntimeError):
            self.run_export(measures=[{"metric": "bugs", "value": "0"}])

    def test_nonzero_security_measure_fails_even_with_empty_server_gate(self):
        for metric in ("bugs", "vulnerabilities", "security_hotspots"):
            with self.subTest(metric=metric), self.assertRaises(RuntimeError):
                self.run_export(measures=[{"metric": name, "value": "1" if name == metric else "0"}
                    for name in ("bugs", "vulnerabilities", "security_hotspots")])

    def test_invalid_security_measure_fails_export(self):
        for value in ("NaN", "-1", "invalid"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                self.run_export(measures=[{"metric": name, "value": value if name == "bugs" else "0"}
                    for name in ("bugs", "vulnerabilities", "security_hotspots")])

    def test_empty_server_gate_records_independent_security_checks(self):
        policy = self.run_export()
        self.assertTrue(policy["passed"])
        self.assertFalse(policy["server_conditions_evaluated"])
        self.assertEqual(len(policy["security_measures"]), 3)

    def test_passing_server_conditions_and_security_measures_pass(self):
        policy = self.run_export(conditions=[{"status": "OK", "metricKey": "bugs"}])
        self.assertTrue(policy["passed"])
        self.assertTrue(policy["server_conditions_evaluated"])


if __name__ == "__main__":
    unittest.main()

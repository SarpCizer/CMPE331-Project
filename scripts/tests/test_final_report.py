"""Final report regressions use retained real results and isolated output paths."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import export_final_report as report


class FinalReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fridgely-final-report-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'docs/tests'
        shutil.copytree(report.BASE,self.base)
        scripts = self.root/'scripts/tests';scripts.mkdir(parents=True)
        for name in ('export_final_report.py','review_follow_up.py'):
            shutil.copy2(report.ROOT/'scripts/tests'/name,scripts/name)
        self.output = self.root/'build/not-created/final'

    def run_export(self):
        return subprocess.run([sys.executable,str(self.root/'scripts/tests/export_final_report.py'),
            '--output',str(self.output)],cwd=self.root.parent,capture_output=True,text=True,encoding='utf-8',errors='replace')

    def put(self,path,value): path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

    def test_clean_build_creates_parents_and_correct_source_inventory(self):
        self.assertFalse(self.output.exists())
        result = self.run_export()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.output/'Fridgely-Final-Software-Test-Report.pdf').read_bytes().startswith(b'%PDF-'))
        text = (self.output/'Fridgely-Final-Software-Test-Report.md').read_text(encoding='utf-8')
        self.assertIn(report.read(self.base/'final-report-input.json')['source_revision'],text)
        self.assertIn('completion.spec.js',text)
        self.assertIn('failed the 500 ms requirement',text)
        self.assertIn('371.47',text)
        self.assertIn('28 unique',text)
        self.assertEqual(len(list((self.output/'final-release/figures').glob('*.svg'))),3)

    def test_mismatched_revision_cannot_publish(self):
        config = report.read(self.base/'final-report-input.json');config['source_revision']='0'*40
        self.put(self.base/'final-report-input.json',config)
        result = self.run_export()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('source/run mismatch',result.stderr)
        self.assertFalse(self.output.exists())

    def test_tampered_raw_measurement_cannot_publish(self):
        config = report.read(self.base/'final-report-input.json')
        path = self.base/config['evidence_root']/'integrated/postgresql-load.json'
        path.write_bytes(path.read_bytes()+b' ')
        result = self.run_export()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Evidence digest mismatch',result.stderr)
        self.assertFalse(self.output.exists())

    def test_nonexistent_browser_filename_cannot_publish(self):
        path = self.base/'final-release/browser-inventory.json'
        data = report.read(path);data['files'][0]['path']='frontend/tests/nonexistent.spec.js'
        self.put(path,data)
        with self.assertRaisesRegex(ValueError,'inventory differs'):
            report.load(self.base)

    def test_green_sonar_without_evaluated_conditions_cannot_publish(self):
        config = report.read(self.base/'final-report-input.json')
        root = self.base/config['evidence_root']
        path = root/'sonar/quality-gate.json'
        self.put(path,{'projectStatus':{'status':'OK','conditions':[]}})
        index = report.read(root/'evidence-index.json')
        raw = path.read_bytes()
        index['files']['sonar/quality-gate.json']={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        self.put(root/'evidence-index.json',index)
        with self.assertRaisesRegex(ValueError,'evaluated Sonar conditions'):
            report.load(self.base)


class FinalEvidenceCheckoutTests(unittest.TestCase):
    def git(self,*args):
        return subprocess.check_output(['git','-c','safe.directory='+str(report.ROOT),'-C',str(report.ROOT),*args])

    def test_every_indexed_final_evidence_member_is_in_head_with_original_bytes(self):
        config,root = report.load()
        index = report.read(root/'evidence-index.json')
        for name,meta in index['files'].items():
            path = (root/name).relative_to(report.ROOT).as_posix()
            with self.subTest(path=path):
                raw = self.git('show','HEAD:'+path)
                self.assertEqual(len(raw),meta['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256'])

    def test_executed_browser_and_backend_inventory_identifies_real_immutable_blobs(self):
        config,_ = report.load()
        inventory = report.read(report.BASE/'final-release/browser-inventory.json')
        modules = report.read(report.BASE/'final-release/module-map.json')
        for item in inventory['files']+inventory['support_files']+modules['modules']:
            with self.subTest(path=item['path']):
                actual = self.git('rev-parse',config['source_revision']+':'+item['path']).decode().strip()
                self.assertEqual(actual,item['git_blob_sha'])


if __name__ == '__main__': unittest.main()

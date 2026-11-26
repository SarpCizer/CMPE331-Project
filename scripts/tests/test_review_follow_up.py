"""Synthetic temporary evidence fixtures verify fail-closed report publication."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import review_follow_up as report


class FollowUpEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='synthetic-report-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.root=self.base/'synthetic-evidence'
        self.revision='a'*40
        self.put(self.base/'review-follow-up.json',{'source_revision':self.revision,'ci_run_id':1,'evidence_root':'synthetic-evidence'})
        self.put(self.root/'ci-jobs.json',{'head_sha':self.revision,'run_id':1,'jobs':[{'conclusion':'success'}]*8})
        for name in ['integrated/postgresql-load.json','integrated/recipe-generation-load.json','local/non-ai-load.json','local/recipe-generation-load.json']:
            self.put(self.root/name,{'revision':self.revision,'passed':True})
        self.put(self.root/'zap/summary.json',{'revision':self.revision,'passed':True,
            'authenticated_successful_requests_observed':1,'alerts_by_risk':{'high':0,'medium':0}})
        self.put(self.root/'sonar/source-identity.json',{'analysis_revision':self.revision,'test_revision':self.revision,'test_artifacts_reused':False})
        self.put(self.root/'sonar/dashboard-capture.json',{'revision':self.revision,'credential_fields_present':False})
        for name in ['sonar/dashboard.png','integrated/backend-junit.xml','integrated/browser-junit.xml','integrated/backend-coverage.json','integrated/acceptance.log','integrated/http-security.log','coverage/coverage-gate.json']:
            self.put(self.root/name,{'explicit_test_fixture':True})
        self.put(self.root/'sonar/quality-gate.json',{'projectStatus':{'status':'OK','conditions':[
            {'metricKey':key,'comparator':op,'errorThreshold':str(threshold),'actualValue':str(threshold),'status':'OK'}
            for key,op,threshold in [('bugs','GT',0),('vulnerabilities','GT',0),('blocker_violations','GT',0),('critical_violations','GT',0),('coverage','LT',90)]
        ]}})
        self.put(self.root/'sonar/metrics.json',{'component':{'measures':[{'metric':'security_hotspots','value':'0'}]}})
        self.put(self.root/'traceability/traceability.json',{'explicit_test_fixture':True})
        self.put(self.base/'coverage/traceability.json',{'explicit_test_fixture':True})
        self.index()

    def put(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value)+'\n',encoding='utf-8')

    def index(self):
        files={}
        for path in self.root.rglob('*'):
            if path.is_file() and path.name!='evidence-index.json':
                raw=path.read_bytes();files[path.relative_to(self.root).as_posix()]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        self.put(self.root/'evidence-index.json',{'source_revision':self.revision,'ci_run_id':1,'files':files})

    def test_valid_source_qualified_bundle_loads(self):
        config,_=report.load(self.base)
        self.assertEqual(config['source_revision'],self.revision)

    def test_unindexed_measurement_cannot_be_published(self):
        path=self.root/'evidence-index.json';data=json.loads(path.read_text());data['files'].pop('local/non-ai-load.json');self.put(path,data)
        with self.assertRaisesRegex(ValueError,'not indexed'): report.load(self.base)

    def test_changed_raw_evidence_is_rejected(self):
        self.put(self.root/'integrated/postgresql-load.json',{'revision':self.revision,'passed':False})
        with self.assertRaisesRegex(ValueError,'digest mismatch'): report.load(self.base)

    def test_empty_gate_cannot_hide_behind_ok(self):
        self.put(self.root/'sonar/quality-gate.json',{'projectStatus':{'status':'OK','conditions':[]}});self.index()
        with self.assertRaisesRegex(ValueError,'conditions are incomplete'): report.load(self.base)

    def test_unauthenticated_clean_scan_cannot_pass(self):
        self.put(self.root/'zap/summary.json',{'revision':self.revision,'passed':True,'authenticated_successful_requests_observed':0,'alerts_by_risk':{'high':0,'medium':0}});self.index()
        with self.assertRaisesRegex(ValueError,'authentication failed'): report.load(self.base)

    def test_failed_local_benchmark_is_retained_for_honest_comparison(self):
        self.put(self.root/'local/non-ai-load.json',{'revision':self.revision,'passed':False});self.index()
        report.load(self.base)
        self.put(self.root/'integrated/postgresql-load.json',{'revision':self.revision,'passed':False});self.index()
        with self.assertRaisesRegex(ValueError,'result mismatch'): report.load(self.base)


if __name__=='__main__': unittest.main()

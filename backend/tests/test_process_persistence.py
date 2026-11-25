import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import pytest


@pytest.mark.parametrize('engine',['sqlite','postgresql'])
def test_two_process_restart_preserves_two_users_and_five_collections(tmp_path,engine):
    url=f'sqlite:///{tmp_path / "restart.db"}' if engine=='sqlite' else os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('TEST_DATABASE_URL is required for real PostgreSQL verification')
    root=Path(__file__).resolve().parents[2]
    env={**os.environ,'PROBE_DATABASE_URL':url,'PYTHONPATH':str(root/'backend/src')}
    run_id=secrets.token_hex(8)
    evidence=[]
    for phase in ['write','read']:
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('persistence_probe.py')),
            phase,str(tmp_path/'snapshots.json'),run_id],env=env,cwd=root,capture_output=True,text=True,timeout=45)
        assert result.returncode==0, f'Persistence {phase} failed; see the isolated probe output'
        evidence.append(json.loads(result.stdout.strip()))
    assert evidence[0]['pid']!=evidence[1]['pid']
    assert all(item['passed'] for item in evidence)

import json
from pathlib import Path
import subprocess
import sys

def test_retention_refuses_public_config_without_exposing_credentials(tmp_path):
    source=tmp_path/'config.json'; source.write_text(json.dumps({'app_dsn':'PRIVATE'})); source.chmod(0o644)
    result=subprocess.run([sys.executable,'-m','lab_runner','retention','--config',str(source)],capture_output=True,text=True)
    assert result.returncode==1
    assert json.loads(result.stdout)=={'event':'retention_failed','deletion_allowed':False}
    assert 'PRIVATE' not in result.stdout+result.stderr

def test_retention_connection_failure_is_curated_and_preserves_source(tmp_path):
    source=tmp_path/'config.json'
    dsn='host=127.0.0.1 port=1 dbname=lab user=PRIVATE_USER password=PRIVATE_SECRET connect_timeout=1'
    source.write_text(json.dumps({'app_dsn':dsn,'harness_dsn':dsn,'accounting_dsn':dsn,
        'namespace':'fixture','environment':'sandbox'})); source.chmod(0o600)
    original=source.read_bytes()
    result=subprocess.run([sys.executable,'-m','lab_runner','retention','--config',str(source)],
        capture_output=True,text=True,timeout=15)
    assert result.returncode==1
    assert json.loads(result.stdout)=={'event':'retention_failed','deletion_allowed':False}
    assert 'PRIVATE' not in result.stdout+result.stderr and source.read_bytes()==original

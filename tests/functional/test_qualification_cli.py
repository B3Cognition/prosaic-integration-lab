"""CLI validation must precede engine/network side effects."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

def invoke(*args):
    return subprocess.run([sys.executable,'-m','lab_runner',*args],capture_output=True,text=True,timeout=10)

@pytest.mark.parametrize('command',['qualify','qualify-recovery'])
def test_invalid_profile_cli_fails_before_creating_stack(tmp_path,command):
    profile=tmp_path/'profile.json';profile.write_text('{"version":true}')
    before=set(Path('.lab').iterdir())
    result=invoke(command,'--profile',str(profile))
    assert result.returncode==2 and 'qualification' in result.stderr
    assert set(Path('.lab').iterdir())==before

def test_missing_staging_cli_outputs_not_qualified():
    result=invoke('qualify-staging','--staging-opt-in')
    assert result.returncode==1
    data=json.loads(result.stdout)
    assert data['reason']=='missing_deployment_inputs' and data['qualification']=='not_qualified'

def test_disabled_staging_cli_does_not_read_configuration(tmp_path):
    result=invoke('qualify-staging','--config',str(tmp_path/'missing.json'))
    assert result.returncode==1 and json.loads(result.stdout)['reason']=='staging_disabled'

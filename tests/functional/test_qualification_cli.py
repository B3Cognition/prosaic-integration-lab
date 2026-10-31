"""CLI validation must precede engine/network side effects."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

def invoke(*args, **options):
    return subprocess.run([sys.executable,'-m','lab_runner',*args],capture_output=True,text=True,timeout=10,**options)

@pytest.mark.parametrize('command',['qualify','qualify-recovery'])
@pytest.mark.parametrize('existing_state',[False,True],ids=['clean-workspace','existing-state'])
def test_invalid_profile_cli_fails_before_creating_stack(tmp_path,command,existing_state):
    # Stack ROOT derives from its module, so use a real isolated source copy.
    # The old test depended on another test having already created ignored .lab.
    source=Path(__file__).resolve().parents[2]
    root=tmp_path/'consumer';root.mkdir()
    for directory in ('lab_runner','src','dependencies'):
        shutil.copytree(source/directory,root/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    state=root/'.lab'
    if existing_state:
        state.mkdir();(state/'sentinel').write_bytes(b'existing state must remain unchanged')
    def snapshot():
        return {p.relative_to(state).as_posix():None if p.is_dir() else p.read_bytes()
                for p in state.rglob('*')} if state.exists() else None
    bin_path=tmp_path/'bin';bin_path.mkdir()
    for engine in ('docker','podman'):
        executable=bin_path/engine
        executable.write_text('#!/bin/sh\nprintf called > "$LAB_TEST_ENGINE_LOG"\nexit 99\n')
        executable.chmod(0o755)
    engine_log=tmp_path/'engine-called'
    environment=dict(os.environ,PYTHONPATH=os.pathsep.join([str(root),str(root/'src')]),
        PATH=str(bin_path)+os.pathsep+os.environ.get('PATH',''),LAB_TEST_ENGINE_LOG=str(engine_log))
    profile=tmp_path/'profile.json';profile.write_text('{"version":true}')
    before=snapshot()
    result=invoke(command,'--profile',str(profile),cwd=root,env=environment)
    assert result.returncode==2 and 'qualification' in result.stderr
    assert snapshot()==before
    assert not engine_log.exists()

def test_missing_staging_cli_outputs_not_qualified():
    result=invoke('qualify-staging','--staging-opt-in')
    assert result.returncode==1
    data=json.loads(result.stdout)
    assert data['reason']=='missing_deployment_inputs' and data['qualification']=='not_qualified'

def test_disabled_staging_cli_does_not_read_configuration(tmp_path):
    result=invoke('qualify-staging','--config',str(tmp_path/'missing.json'))
    assert result.returncode==1 and json.loads(result.stdout)['reason']=='staging_disabled'

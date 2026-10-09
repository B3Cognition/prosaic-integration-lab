import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from lab_runner.gates import COUNTS

def test_required_cli_runs_remaining_lanes_after_failure_and_exports_no_raw_output(monkeypatch,tmp_path):
    source = Path(__file__).resolve().parents[2]/'scripts/required_acceptance.py'
    spec = importlib.util.spec_from_file_location('required_acceptance',source)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(runner,'resolve_image',lambda candidate:'sha256:'+'1'*64)
    seen = []
    def fake(command,**kwargs):
        mode=command[command.index('--mode')+1]; seen.append(mode)
        assert command[command.index('--consumer-image')+1] == 'sha256:'+'1'*64
        item={'mode':mode,'passed':mode != 'audit','cleanup':'verified','dependency_mode':'released',
            'test_returncode':1 if mode == 'audit' else 0,'test_count':COUNTS[mode],'skipped':0,
            'failed_tests':['PRIVATE'] if mode == 'audit' else [],'host_architecture':'arm64',
            'payload_audit':'verified','released_manifest_sha256':'247a2b1b1d64b2f4ec318a6b6aec51c28b691fb41018044f8bac571c089d53c7',
            'images':{'consumer':'sha256:'+'1'*64,'postgres':'postgres:16@sha256:'+'2'*64},'secret':'PRIVATE'}
        return SimpleNamespace(returncode=item['test_returncode'],stdout=json.dumps(item)+'\nEvidence: PRIVATE',stderr='PRIVATE')
    monkeypatch.setattr(runner.subprocess,'run',fake)
    target=tmp_path/'safe.json'
    monkeypatch.setattr(sys,'argv',['required_acceptance','--postgres-version','16','--export',str(target)])
    assert runner.main() == 1
    assert seen == list(COUNTS)
    assert 'PRIVATE' not in target.read_text()
    assert json.loads(target.read_text())['passed'] is False

def test_ci_requires_native_matrix_and_exports_only_safe_summary():
    import yaml
    workflow=yaml.safe_load((Path(__file__).resolve().parents[2]/'.github/workflows/required-acceptance.yml').read_text())
    job=workflow['jobs']['acceptance']
    assert job['strategy']['matrix'] == {'runner':['ubuntu-24.04','ubuntu-24.04-arm'],'postgres':[16,18]}
    assert workflow['permissions'] == {'contents':'read'}
    steps=job['steps']
    uploads=[step for step in steps if 'upload-artifact@' in step.get('uses','')]
    assert len(uploads)==1 and uploads[0]['with']['path'].startswith('reports/required-')
    assert all('--candidate' not in step.get('run','') for step in steps)
    assert any('scripts/required_acceptance.py' in step.get('run','') for step in steps)

def test_missing_image_fails_gate_with_safe_summary_before_owned_resources(monkeypatch,tmp_path,capsys):
    source=Path(__file__).resolve().parents[2]/'scripts/required_acceptance.py'
    spec=importlib.util.spec_from_file_location('required_missing_image',source)
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    def unavailable(candidate): raise runner.EngineError('PRIVATE')
    monkeypatch.setattr(runner,'resolve_image',unavailable)
    target=tmp_path/'safe.json'
    monkeypatch.setattr(sys,'argv',['required_acceptance','--postgres-version','16','--export',str(target)])
    assert runner.main() == 1
    assert json.loads(target.read_text()) == {'passed':False,'postgres_major':16,'lanes':[],
        'event':'required_image_unavailable'}
    assert 'PRIVATE' not in capsys.readouterr().out

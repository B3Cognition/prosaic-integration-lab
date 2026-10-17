import json
import socket
import pytest
from test_retrieval_memory_runner import bundle


def test_default_cli_is_pure_unexecuted(monkeypatch,capsys):
    import lab_runner.memory.runner as runner
    from lab_runner.retrieval_memory import main
    monkeypatch.setattr(runner,'load_suite',bundle)
    def forbidden(*args,**kwargs):raise AssertionError('socket used in preflight')
    monkeypatch.setattr(socket,'socket',forbidden)
    assert main([])==0
    result=json.loads(capsys.readouterr().out)
    assert result['origin']=='unexecuted' and result['executedSamples']==0


def test_explicit_fixture_cli_runs_real_native_calls(monkeypatch,tmp_path,capsys):
    import lab_runner.memory.runner as runner
    from lab_runner.retrieval_memory import main
    monkeypatch.setattr(runner,'load_suite',bundle)
    assert main(['--fixture','--output',str(tmp_path)])==0
    assert json.loads(capsys.readouterr().out)['fixtureCounts']['providerRequests']==16


def test_invalid_live_config_prints_only_closed_error(tmp_path,capsys):
    from lab_runner.retrieval_memory import main
    path=tmp_path/'config.json';path.write_text('PRIVATE-ENDPOINT-AND-SECRET')
    assert main(['--live','--config',str(path),'--output',str(tmp_path/'out')])==2
    output=capsys.readouterr()
    assert 'PRIVATE-ENDPOINT' not in output.out+output.err and str(path) not in output.out+output.err


def test_memory_package_data_are_explicit():
    import tomllib
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    data=tomllib.loads((root/'pyproject.toml').read_text())
    assert 'data/*.json' in data['tool']['setuptools']['package-data']['lab_runner.memory']


def test_cli_receipt_only_recovery_adopts_without_a_socket(tmp_path,monkeypatch,capsys):
    import prosaic_harness
    import lab_runner.memory.runner as runner
    from lab_runner.retrieval_memory import main
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    monkeypatch.setattr(runner,'load_suite',bundle)
    original=prosaic_harness.FileRunStore
    monkeypatch.setattr(prosaic_harness,'FileRunStore',lambda *a,**kw:FaultStore(original(*a,**kw),'after'))
    with pytest.raises(InjectedInterruption):main(['--fixture','--output',str(tmp_path)])
    monkeypatch.setattr(prosaic_harness,'FileRunStore',original)
    def forbidden(*a,**kw):raise AssertionError('socket in CLI recovery')
    monkeypatch.setattr(socket,'socket',forbidden)
    assert main(['--fixture','--recover-only','--output',str(tmp_path)])==1
    r=json.loads(capsys.readouterr().out)
    assert r['executedSamples']==r['taskSuccess']['passed']==1
    assert r['fixtureCounts']==dict(providerRequests=2,toolCalls=1)

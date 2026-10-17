import json
import pytest


def test_default_command_is_unexecuted(capsys):
    from lab_runner.agent_quality import main
    assert main([])==0
    report=json.loads(capsys.readouterr().out)
    assert report['origin']=='unexecuted' and report['executedSamples']==0
    assert report['scheduledSamples']==10 and report['baselineComplete'] is False


def test_preflight_does_not_construct_runtime_or_network(monkeypatch,capsys):
    import socket,subprocess
    from prosaic_runtime import ProsaicRuntime
    from prosaic_harness import Harness
    def forbidden(*args,**kwargs):raise AssertionError('execution during preflight')
    monkeypatch.setattr(ProsaicRuntime,'__init__',forbidden)
    monkeypatch.setattr(Harness,'__init__',forbidden)
    monkeypatch.setattr(socket,'socket',forbidden)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    from lab_runner.agent_quality import main
    assert main([])==0


def test_full_fixture_command_and_duplicate_run(tmp_path,capsys,monkeypatch):
    from lab_runner.agent_quality import main
    output=tmp_path/'quality'
    assert main(['--fixture','--output',str(output)])==0
    report=json.loads(capsys.readouterr().out)
    assert report['origin']=='fixture' and report['baselineComplete']
    assert report['taskSuccess']['passed']==10
    assert all(r['passed'] for r in report['recovery'])
    def forbidden(*args,**kwargs):raise AssertionError('replay dispatched a provider')
    monkeypatch.setattr('lab_runner.quality.fixture.fixture_provider',forbidden)
    assert main(['--fixture','--output',str(output)])==0
    replay=json.loads(capsys.readouterr().out)
    assert replay['results']==report['results']
    assert replay['providerRequests']==report['providerRequests']


@pytest.mark.parametrize('args',[['--live'],['--repetitions','0'],['--fixture','--live']])
def test_invalid_modes_are_rejected(args):
    from lab_runner.agent_quality import main
    with pytest.raises(SystemExit) as exc:main(args)
    assert exc.value.code==2


def test_interrupted_sample_is_unknown_on_reopen_not_unexecuted(tmp_path,monkeypatch):
    from lab_runner.quality.runner import execute
    def crash(*args,**kwargs):raise RuntimeError('private exception canary')
    monkeypatch.setattr('lab_runner.quality.execution.execute_case',crash)
    report=execute(output=tmp_path/'interrupted')
    assert report['stateCounts']['unknown']==1 and report['executedSamples']==1
    assert report['providerRequests'] is None and report['toolCalls'] is None
    assert 'private exception canary' not in json.dumps(report)
    def forbidden(*args,**kwargs):raise AssertionError('uncertain sample redispatched')
    monkeypatch.setattr('lab_runner.quality.execution.execute_case',forbidden)
    replay=execute(output=tmp_path/'interrupted')
    assert replay['stateCounts']['unknown']==1 and not replay['baselineComplete']

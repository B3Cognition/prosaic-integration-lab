import json
from pathlib import Path
import os
import subprocess
import sys
import shutil

import pytest

PROVIDERS=('openai','anthropic')
MODES=('parallel','sequential')
SCENARIOS=('ready','hold','conflict','missing','wrong','malformed','tool-error',
    'provider-error','cancel','request-cap','tool-cap','token-cap')


@pytest.mark.parametrize('provider',PROVIDERS)
@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('scenario',SCENARIOS)
def test_actual_bounded_pair_and_receipt_only_recovery(tmp_path,provider,mode,scenario):
    from lab_runner.coordination_fixture import qualify,inspect_pair
    proof=qualify(tmp_path,provider=provider,scenario=scenario,mode=mode)
    assert proof['qualified'] and proof['liveRequests']==0
    assert proof['providerRequests']<=4 and proof['toolCalls']<=2
    assert proof['reportedTokens']<=8192 and proof['workerCleanup']
    assert proof['parentDeadlinePreserved'] and proof['networkDeniedRecovery']
    expected={'ready':'ready','hold':'hold','conflict':'conflict','missing':'missing',
        'wrong':'failed','malformed':'failed','tool-error':'failed','provider-error':'incomplete',
        'cancel':'incomplete','request-cap':'failed','tool-cap':'failed','token-cap':'failed'}[scenario]
    if scenario in ('provider-error','request-cap','tool-cap','token-cap'):
        assert proof['join']['status'] in ('failed','incomplete'),proof
    else:assert proof['join']['status']==expected,proof
    assert proof['wireRequests']<=proof['providerRequests']
    if scenario in ('ready','hold','conflict','missing'):
        assert proof['providerRequests']==4 and proof['toolCalls']==2
        assert proof['observedOverlap']==(mode=='parallel')
    if scenario=='provider-error':assert proof['join']['usage'] is None
    if scenario=='cancel':assert proof['providerRequests']==proof['toolCalls']==0
    if scenario=='request-cap':assert proof['providerRequests']<=3
    if scenario=='tool-cap':assert proof['toolCalls']<=1
    if scenario=='token-cap':assert proof['providerRequests']<=1
    assert inspect_pair(tmp_path,provider=provider,scenario=scenario,mode=mode)==proof['join']
    assert not any(secret in json.dumps(proof) for secret in ('PRIVATE-SOURCE','PRIVATE-PROVIDER','source-alpha','assignmentDigest'))


@pytest.mark.parametrize('boundary',['launch','receipt'])
def test_process_loss_never_relaunches_worker(tmp_path,boundary):
    code='''
import sys
from pathlib import Path
from lab_runner.coordination_fixture import qualify
qualify(Path(sys.argv[1]),provider='openai',scenario='ready',mode='sequential',crash_boundary=sys.argv[2])
'''
    root=Path(__file__).resolve().parents[2]
    env=dict(os.environ,PYTHONPATH=os.pathsep.join([str(root),str(root/'src')]))
    result=subprocess.run([sys.executable,'-c',code,str(tmp_path),boundary],env=env,capture_output=True,timeout=30)
    assert result.returncode==23,result.stderr.decode()[-2000:]
    from lab_runner.coordination_fixture import inspect_pair
    before={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    restored=inspect_pair(tmp_path,provider='openai',scenario='ready',mode='sequential')
    assert restored['status']=='incomplete' and restored['usage'] is None
    assert before=={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


@pytest.fixture(scope='module')
def saved_pair(tmp_path_factory):
    from lab_runner.coordination_fixture import qualify
    root=tmp_path_factory.mktemp('saved-coordination')
    qualify(root,provider='openai',scenario='ready')
    return root


@pytest.mark.parametrize('target',['case.json','coordination.json','alpha/evidence.json',
    'alpha/accounting.json','alpha/lookup.json'])
@pytest.mark.parametrize('fault',['missing','corrupt','symlink'])
def test_saved_pair_refuses_damaged_or_aliased_evidence(tmp_path,saved_pair,target,fault):
    from lab_runner.coordination_fixture import inspect_pair
    root=tmp_path/'copy';shutil.copytree(saved_pair,root)
    assert inspect_pair(root,provider='openai',scenario='ready',mode='parallel')['status']=='ready'
    path=root/target
    if fault=='missing':path.unlink()
    elif fault=='corrupt':path.write_text('{}')
    else:path.rename(path.with_suffix('.original'));path.symlink_to(path.with_suffix('.original'))
    with pytest.raises((ValueError,OSError,KeyError)):
        inspect_pair(root,provider='openai',scenario='ready',mode='parallel')


@pytest.mark.parametrize('change',[dict(qualified=False),dict(version=True),dict(providerRequests=999),
    dict(providerRequests=3),dict(toolCalls=True),dict(reportedTokens=-1),dict(reportedTokens=599),
    dict(wireRequests=5),dict(wireRequests=3),dict(usageComplete=False),dict(observedOverlap=False),
    dict(workerCleanup=False),dict(parentDeadlinePreserved=False),dict(networkDeniedRecovery=False),
    dict(liveRequests=10),dict(extra='unexpected')])
def test_replay_refuses_corrupt_qualification_claims_with_unchanged_join(tmp_path,saved_pair,change):
    from lab_runner.coordination_fixture import replay
    lane=tmp_path/'openai-parallel-ready';shutil.copytree(saved_pair,lane)
    path=lane/'proof.json';proof=json.loads(path.read_bytes());proof.update(change)
    path.write_text(json.dumps(proof))
    # The first lane itself must be refused, before replay looks for later lanes.
    with pytest.raises(ValueError):replay(tmp_path)

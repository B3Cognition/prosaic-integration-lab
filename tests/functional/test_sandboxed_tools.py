import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('columns',['80','120','200'])
def test_process_inventory_keeps_long_owned_child_arguments(tmp_path,monkeypatch,columns):
    from lab_runner.sandbox_fixture import _owned_processes
    # Exercise real ps, including GNU ps's inherited display-width handling.
    monkeypatch.setenv('COLUMNS',columns)
    script=tmp_path/('owned-child-'+('x'*100)+'.py')
    script.write_text('import time; time.sleep(4)\n')
    nonce='prosaic-sbx-owned-inventory-regression'
    child=subprocess.Popen([sys.executable,str(script),'--linger',nonce])
    try:
        found=_owned_processes(nonce,str(script))
        assert child.pid in found
        assert found[child.pid]['child'] is True
    finally:
        child.wait(timeout=6)


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('scenario',['contained','timeout','output','denied','unsupported','off'])
def test_required_sandbox_qualifies_actual_effects_and_read_only_recovery(tmp_path,provider,scenario):
    from lab_runner.sandbox_fixture import qualify
    proof=qualify(tmp_path,provider=provider,scenario=scenario)
    assert proof['qualified'] is True,proof
    assert proof['liveRequests']==0 and proof['networkDeniedRecovery'] is True
    assert proof['providerRequests']<=4 and proof['toolCalls']<=2
    if scenario in ('denied','unsupported','off'):
        assert proof['providerRequests']==proof['toolCalls']==0
        assert proof['probeExecuted'] is False
    else:
        assert proof['operationalBackend'] is True
        assert proof['probeExecuted'] is True
        assert proof['positiveControl'] is True
        assert proof['hostNetworkDeliveries']==0 and proof['outsideWrites']==0
        assert proof['approvalState']=='spent'
        if scenario=='contained':
            assert proof['toolCalls']==2 and proof['scratchRemoved'] is True
            assert proof['scratchDistinct'] is True
        else:
            assert proof['toolCalls']==1
            assert proof['toolError']=='toolEffectUncertain'
            assert proof['observedOwnedProcesses']>=2 and proof['survivingOwnedProcesses']==0
            assert proof['observedOwnedChildren']>=1 and proof['observedSameGroupChild'] is True
            assert proof['stoppedBeforeNaturalExit'] is True and 0<=proof['toolFailureSeconds']<3.5
    assert not any(s in json.dumps(proof) for s in ('SYNTHETIC-CREDENTIAL','HOST-CANARY','private-run'))


def test_installed_recipe_script_and_separate_network_denied_replay(tmp_path):
    root=Path(__file__).resolve().parents[2]
    env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONPATH']=os.pathsep.join([str(root),str(root/'src')])
    command=[sys.executable,str(root/'scripts/sandboxed_tools_smoke.py'),'--output',str(tmp_path/'proof')]
    first=subprocess.run(command,cwd=tmp_path,env=env,capture_output=True,text=True,timeout=180)
    assert first.returncode==0,first.stderr[-3000:]
    second=subprocess.run(command+['--replay'],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=30)
    assert second.returncode==0,second.stderr[-3000:]
    assert json.loads((tmp_path/'proof/result.json').read_text())['lanes']==12


@pytest.fixture(scope='module')
def saved_lane(tmp_path_factory):
    from lab_runner.sandbox_fixture import qualify
    root=tmp_path_factory.mktemp('sandbox-saved')
    qualify(root,provider='openai',scenario='contained')
    return root


@pytest.mark.parametrize('target',['approval.json','trajectory.json','turn-evidence.json','binding.json'])
@pytest.mark.parametrize('fault',['missing','corrupt','symlink'])
def test_saved_inspection_refuses_missing_corrupt_or_aliased_receipts(tmp_path,saved_lane,target,fault):
    import shutil
    from lab_runner.sandbox_fixture import inspect_lane
    root=tmp_path/'lane';shutil.copytree(saved_lane,root)
    path=root/target
    if fault=='missing':path.unlink()
    elif fault=='corrupt':path.write_text('{}')
    else:
        path.rename(root/'aliased');path.symlink_to(root/'aliased')
    with pytest.raises((ValueError,OSError)):
        inspect_lane(root,scenario='contained')


@pytest.mark.parametrize('optimization',['-O','-OO'])
def test_optimized_python_preserves_approval_and_qualification(tmp_path,optimization):
    root=Path(__file__).resolve().parents[2]
    env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONPATH']=os.pathsep.join([str(root),str(root/'src')])
    command=[sys.executable,optimization,str(root/'scripts/sandboxed_tools_smoke.py'),'--output',str(tmp_path/'proof')]
    result=subprocess.run(command,cwd=tmp_path,env=env,capture_output=True,text=True,timeout=180)
    assert result.returncode==0,result.stderr[-3000:]
    for provider in ('openai','anthropic'):
        for scenario in ('contained','timeout','output'):
            lane=tmp_path/'proof'/(provider+'-'+scenario)
            proof=json.loads((lane/'proof.json').read_text())
            assert proof['approvalState']=='spent'
            assert json.loads((lane/'approval.json').read_text())['proposals']['start']['state']=='spent'
            assert proof['qualified'] and proof['networkDeniedRecovery']
    assert json.loads((tmp_path/'proof/result.json').read_text())['networkDeniedReplays']==12

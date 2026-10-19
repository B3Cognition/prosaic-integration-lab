import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('scenario,want,categories',[
    ('ready','passed',[]),('missing','passed',[]),
    ('wrong','failed',['model_output']),('malformed','failed',['model_output']),
    ('tool-error','failed',['tool']),('provider-error','incomplete',['provider','accounting']),
])
def test_parcel_boundary_reports_verified_outcomes_and_safe_trace(tmp_path,provider,scenario,want,categories):
    from lab_runner.trajectory_fixture import qualify
    proof=qualify(tmp_path,provider=provider,scenario=scenario)
    report=proof['report']
    assert report['assessment']['status']==want
    assert report['assessment']['categories']==categories
    assert 0<proof['providerRequests']<=4 and proof['toolCalls']<=2
    assert proof['lookupEffects']==(0 if scenario in ('provider-error','tool-error') else 1)
    assert proof['networkDeniedRecovery'] is True
    assert proof['approvalState']==('pending' if scenario=='ready' else None)
    assert proof['liveRequests']==0
    assert {o['source'] for o in report['observations']}=={'runtime','harness'}
    assert report['assessment']['usage']['reportedTokens']==(None if scenario=='provider-error' else 300)
    assert not any(value in json.dumps(report) for value in ('PRIVATE-', 'parcel-internal', 'read_manifest', 'trace-fixture'))
    if scenario=='tool-error':
        assert any(o.get('toolCode')=='handler_error' for o in report['observations'])
    if scenario=='ready':
        step={o['stepRef'] for o in report['observations'] if 'stepRef' in o}
        assert step & {a['stepRef'] for a in report['hostAnnotations'] if a['kind']=='approval'}


def test_documented_smoke_runs_and_reads_saved_reports_without_network(tmp_path):
    root=Path(__file__).resolve().parents[2]
    command=[sys.executable,str(root/'scripts/trajectory_smoke.py'),'--output',str(tmp_path/'proof')]
    env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONPATH']=os.pathsep.join([str(root),str(root/'src')])
    process=subprocess.run(command,cwd=tmp_path,env=env,
                           capture_output=True,text=True,timeout=120)
    assert process.returncode==0,process.stderr[-2000:]
    summary=json.loads((tmp_path/'proof/result.json').read_text())
    assert summary['lanes']==12 and summary['networkDeniedReplays']==12 and summary['liveRequests']==0

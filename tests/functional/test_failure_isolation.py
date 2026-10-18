"""Consumer isolation around public SDK execution, with no automatic retries."""
from pathlib import Path
import os
import subprocess
import sys

import pytest
from lab_runner.failure_isolation import FailureIsolation
from lab_runner.quality.contracts import digest


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('fault',['missing','lost_receipt'])
def test_failed_case_does_not_block_other_reserved_case_and_recovery_never_dispatches(tmp_path,provider,fault):
    from lab_runner.handoffs import correction as c,correction_fixture as f
    root=tmp_path/'study';root.mkdir(mode=0o700)
    j=FailureIsolation(root/'containment.json',identity=digest(dict(scope='trusted-host',provider=provider)),
        limits=dict(providerRequests=8,toolCalls=4,reportedTokens=16384))
    case=f.example_case('correct');binding=digest(case)
    with f.fixture_provider(case,provider=provider,scenario='correct',
                            usage_fault='missing' if fault=='missing' else 'complete',usage_stage='worker') as p:
        token=j.admit('failed',binding=binding);j.start('failed',token)
        c.execute_correction(case,config=p.config,output=root/'failed',sample_id='failed')
        j.isolate('failed',binding=binding,decision_digest=digest(dict(hostDecision='isolate',work='failed')))
        with f.fixture_provider(case,provider=provider,scenario='correct') as healthy:
                token=j.admit('other',binding=binding);j.start('other',token)
                evidence=c.execute_correction(case,config=healthy.config,output=root/'other',sample_id='other')
                score=c.score_correction(case,evidence)
                assert score['taskAccepted'] and score['counts']['providerRequests']==2
                j.complete('other',token,actual=score['counts'],evidence_digest=digest(evidence))
                assert healthy.requests==2 and not healthy.errors
        before=p.requests;p.deny=True
        saved=c.recover_correction(case,config=p.config,output=root/'failed',sample_id='failed')
        score=c.score_correction(case,saved)
        actual=score['counts'] if score['accountingComplete'] else None
        args=dict(binding=binding,decision_digest=digest(dict(hostDecision='reconcile',work='failed')),
                  actual=actual,evidence_digest=digest(saved) if actual else None,
                  outcome='failed' if actual else 'unknown')
        j.recover('failed',**args);j.recover('failed',**args)
        assert p.requests==before and not p.errors
        assert j.inspect('other')['state']=='completed'
        assert j.status()['retained']==dict(providerRequests=8,toolCalls=4,reportedTokens=16384)


def test_installed_qualification_entrypoint_requires_separate_package(tmp_path):
    script=Path(__file__).resolve().parents[2]/'scripts/failure_isolation_smoke.py'
    assert script.is_file(),'installed failure isolation smoke missing'
    result=subprocess.run([sys.executable,str(script),'--source-root',str(script.parent.parent),
                           '--evidence-dir',str(tmp_path/'evidence'),'--output',str(tmp_path/'result.json')],
                          capture_output=True,text=True,
                          env=dict(os.environ,PYTHONPATH=str(script.parent.parent)))
    assert result.returncode!=0
    assert 'installed package required' in result.stderr

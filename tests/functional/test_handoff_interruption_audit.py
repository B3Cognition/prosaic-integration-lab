"""Partial persisted evidence stays visible without a model redispatch."""
import pytest


@pytest.mark.parametrize('phase',['reserved','receipt','unsettled-file'])
def test_partial_handoff_audit_never_discards_receipts_or_unknown_charge(tmp_path,phase):
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.handoffs.fixture import example_case,fixture_provider
    from lab_runner.handoffs.execution import materials,execute_case
    from lab_runner.handoffs.evaluation import inspect_partial,charge_for
    from lab_runner.quality.contracts import digest
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    case=example_case();out=tmp_path/'live';out.mkdir(mode=0o700)
    with fixture_provider(case) as p:
        if phase=='receipt':
            workflow,request,_=materials(case,p.config,out,'partial')
            store=FileRunStore(out/'store',namespace='typed-handoffs');store.initialize()
            try:
                h=Harness(workflow,store=FaultStore(store,'after'),run_id=digest(dict(sampleId='partial'))[:32])
                with pytest.raises(InjectedInterruption):h.run(request)
            finally:store.close()
        elif phase=='unsettled-file':
            execute_case(case,config=p.config,output=out,sample_id='partial')
        before=p.requests;p.deny=True
        result=inspect_partial(case,config=p.config,source=out,output=tmp_path/'copy',sample_id='partial')
        assert p.requests==before
        if phase=='reserved':assert result is None
        else:
            assert len(result['receipts'])==(1 if phase=='receipt' else 3)
            assert result['checkpoint']['status']==('running' if phase=='receipt' else 'completed')
    claim=dict(state='pending',maximum=dict(providerRequests=4,toolCalls=2,reportedTokens=8192),actual=None)
    assert charge_for(claim)['reportedTokens']==8192

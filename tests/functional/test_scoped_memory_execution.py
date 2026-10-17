import socket
import pytest
from test_scoped_memory_recovery import policy
from lab_runner.quality.contracts import decode,encode


@pytest.mark.parametrize('mode',['irrelevant','hostile','budget','mandatory'])
def test_scoped_policy_runs_current_evidence_with_frozen_plan_and_trace(tmp_path,mode):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case,recover_case
    from lab_runner.memory.scoring import score_case
    quote=(lambda r:[1600]*4 if r['recalledEpisodes'] else [100]*4) if mode=='budget' else (
        (lambda _:[2000]*4) if mode=='mandatory' else None)
    case,corpus,builder,counter=policy(quote=quote,entity='maple' if mode=='irrelevant' else 'orchid',hostile=mode=='hostile')
    with fixture_provider([case],scenario='public_summary') as provider:
        kw=dict(corpus=corpus,arm='enabled',config=provider.config,profile='fixture-a',output=tmp_path,
            sample_id='scoped',context_builder=builder,evidence_format='typed')
        result=execute_case(case,**kw,token_counter=counter)
        assert result['counts']['providerRequests']==provider.requests==(0 if mode=='mandatory' else 2)
        assert result['counts']['reportedTokens']==(0 if mode=='mandatory' else 300)
        assert result['prepared']['request']['recordIndex']==case['recordIndex']
        assert result['prepared']['request']['task']==case['task']
        episodes=result['prepared']['request']['recalledEpisodes']
        assert bool(episodes)==(mode=='hostile')
        if mode!='mandatory':assert score_case(case,result)['state']=='passed'
        trace_path=tmp_path/'scoped-context-trace.json';trace=decode(trace_path.read_bytes())
        assert len(trace['observations'])==(0 if mode=='mandatory' else 2)
        assert trace['events'] and trace['receiptFailures'] is not None
        assert trace['proposals'][0]['reason']==('mandatoryRejected' if mode=='mandatory' else 'withinPlan')
        before=trace_path.read_bytes()
        with pytest.raises(ValueError,match='recovery'):execute_case(case,**kw,token_counter=counter)
        # No counter, quotation, retrieval or sockets are needed for receipt-only replay.
        def forbidden(*a,**k):raise AssertionError('network/retrieval/quote during recovery')
        builder.corpus.retrieve=forbidden;builder.quote_inputs=forbidden
        original=socket.socket;socket.socket=forbidden
        try:recovered=recover_case(case,**kw)
        finally:socket.socket=original
        if mode!='mandatory':assert recovered['prepared']==result['prepared']
        assert trace_path.read_bytes()==before
        assert provider.requests==(0 if mode=='mandatory' else 2)


def test_shared_guard_spans_repair_and_missing_usage_cannot_restart(tmp_path):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case,recover_case
    for scenario,expected in [('repair_fact_ids',4),('missing_usage',1)]:
        case,corpus,builder,counter=policy()
        with fixture_provider([case],scenario=scenario) as p:
            kw=dict(corpus=corpus,arm='enabled',config=p.config,profile='fixture-a',output=tmp_path/scenario,
                sample_id='shared',context_builder=builder)
            result=execute_case(case,**kw,token_counter=counter)
            assert p.requests==expected
            trace_path=tmp_path/scenario/'shared-context-trace.json';raw=trace_path.read_bytes()
            trace=decode(raw)
            assert len(trace['proposals'])==expected
            if scenario=='missing_usage':assert result['counts']['reportedTokens'] is None
            recover_case(case,**kw)
            assert p.requests==expected and trace_path.read_bytes()==raw
            with pytest.raises(ValueError,match='recovery'):execute_case(case,**kw,token_counter=counter)


@pytest.mark.parametrize('phase',['before','after'])
def test_interrupted_receipt_recovery_never_reconstructs_dispatch_guard(tmp_path,phase):
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import materials,recover_case,LIMITS
    from lab_runner.memory_policy.budget import guard_registration
    from lab_runner.quality.token_admission import execution_scope
    from lab_runner.quality.recovery import FaultStore,InjectedInterruption
    from lab_runner.quality.contracts import digest
    case,corpus,builder,counter=policy()
    with fixture_provider([case]) as p:
        kw=dict(corpus=corpus,arm='enabled',config=p.config,profile='fixture-a',output=tmp_path,
            sample_id='interrupted',context_builder=builder)
        w,j,events,prepared=materials(case,**kw,limits=LIMITS)
        guard=guard_registration(counter,prepared['contextAssembly']['plan'],on_proposal=events.context_trace.proposals)
        store=FileRunStore(tmp_path/'store',namespace='retrieval-memory');store.initialize()
        try:
            h=Harness(w,store=FaultStore(store,phase),run_id=digest({'sampleId':'interrupted'})[:32],
                on_event=events,accounting=events.accounting)
            with pytest.raises(InjectedInterruption),execution_scope(LIMITS,guard.registration).activate():
                h.run(prepared['request'])
        finally:store.close()
        trace=tmp_path/'interrupted-context-trace.json';before=trace.read_bytes()
        def forbidden(*a,**k):raise AssertionError('repeated quote/retrieval')
        builder.quote_inputs=forbidden;builder.corpus.retrieve=forbidden
        recovered=recover_case(case,**kw)
        assert (recovered is not None)==(phase=='after')
        assert trace.read_bytes()==before and p.requests==2


def test_actual_continuation_over_plan_refuses_without_second_http(tmp_path):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    from prosaic_runtime import TokenCounterRegistration
    class Continuation:
        def count_tokens(self,native):return 101 if any(m['role']=='tool' for m in native['messages']) else 100
    case,corpus,builder,counter=policy()
    with fixture_provider([case]) as p:
        result=execute_case(case,corpus=corpus,arm='enabled',config=p.config,profile='fixture-a',output=tmp_path,
            sample_id='continuation',context_builder=builder,token_counter=TokenCounterRegistration(counter.descriptor,Continuation()))
        # Native token admission is terminal: it does not use retry headroom.
        assert result['counts']['providerRequests']==p.requests==1
        assert result['counts']['reportedTokens']==150 and not result['completed']
        trace=decode((tmp_path/'continuation-context-trace.json').read_bytes())
        assert [x['reason'] for x in trace['proposals']]==['withinPlan','inputCeiling']

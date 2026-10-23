import socket
import pytest
from test_scoped_memory_recovery import policy
from lab_runner.quality.contracts import decode

@pytest.mark.parametrize('arm',['enabled','disabled'])
def test_pre_dispatch_correction_is_bounded_and_replay_is_receipt_only(tmp_path,arm):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case,recover_case,LIMITS
    case,corpus,builder,counter=policy()
    with fixture_provider([case],scenario='repair_arguments') as p:
        kw=dict(corpus=corpus,arm=arm,config=p.config,profile='fixture-a',output=tmp_path,
            sample_id='repair',context_builder=builder,evidence_format='typed',bounded_recovery=True)
        evidence=execute_case(case,**kw,token_counter=counter)
        assert evidence['completed'] and p.requests==4
        assert evidence['counts']==dict(providerRequests=4,toolCalls=2,reportedTokens=600)
        assert LIMITS==dict(providerRequests=4,toolCalls=2,reportedTokens=8192,timeoutSeconds=600)
        assert len(evidence['journal'])==1
        path=tmp_path/'repair-context-trace.json';before=path.read_bytes()
        rows=decode(before)['receiptFailures']
        assert any(r['reason']=='invalid_arguments' and r['toolOutcome']['effect']=='not_started' for r in rows)
        def forbidden(*a,**kw):raise AssertionError('dispatch during replay')
        builder.corpus.retrieve=forbidden;builder.quote_inputs=forbidden
        original=socket.socket;socket.socket=forbidden
        try:assert recover_case(case,**kw)['completed']
        finally:socket.socket=original
        assert path.read_bytes()==before and p.requests==4

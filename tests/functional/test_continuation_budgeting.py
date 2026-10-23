"""Exercise the new planning policy through public installed SDK execution."""
import socket
import pytest
from lab_runner.quality.contracts import decode


def configuration(*,count=1307,quote=1280,capacity=32768):
    from test_scoped_memory_recovery import policy
    from lab_runner.memory_policy.native import ScopedContext
    from lab_runner.memory.execution import LIMITS
    from prosaic_runtime import TokenCounterRegistration
    case,corpus,legacy,base=policy(quote=lambda _:[quote]*4,capacity=capacity)
    builder=ScopedContext(legacy.corpus,counter_descriptor=base.descriptor.to_dict(),
        quote_inputs=legacy.quote_inputs,quote_identity='c'*64,limits=LIMITS,
        output_tokens=512,continuation_budget=True)
    class Variable:
        def count_tokens(self,native):
            return count if any(m['role']=='tool' for m in native['messages']) else 100
    return case,corpus,builder,TokenCounterRegistration(base.descriptor,Variable())


@pytest.mark.parametrize('count,quote',[(1307,1280),(1211,1152),(7530,100)])
@pytest.mark.parametrize('arm',['enabled','disabled'])
def test_variable_continuation_and_exact_shared_fit_complete(tmp_path,count,quote,arm):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case,recover_case
    case,corpus,builder,counter=configuration(count=count,quote=quote)
    with fixture_provider([case]) as p:
        kw=dict(corpus=corpus,arm=arm,config=p.config,profile='fixture-a',
            output=tmp_path,sample_id='dynamic',context_builder=builder,bounded_recovery=True)
        result=execute_case(case,**kw,token_counter=counter)
        assert result['completed'] and p.requests==2
        assert result['counts']==dict(providerRequests=2,toolCalls=1,reportedTokens=300)
        path=tmp_path/'dynamic-context-trace.json';before=path.read_bytes();trace=decode(before)
        assert [r['reason'] for r in trace['proposals']]==['withinContext']*2
        assert trace['proposals'][1]['inputBound']==count
        assert trace['proposals'][1]['quotedInputBound']==quote
        def forbidden(*a,**k):raise AssertionError('inference or quotation during replay')
        builder.quote_inputs=forbidden;builder.corpus.retrieve=forbidden
        original=socket.socket;socket.socket=forbidden
        try:replayed=recover_case(case,**kw)
        finally:socket.socket=original
        assert replayed['completed'] and p.requests==2 and path.read_bytes()==before


def test_counted_context_proposal_still_cannot_exceed_actual_shared_remainder(tmp_path):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    case,corpus,builder,counter=configuration(count=7600,quote=100)
    with fixture_provider([case]) as p:
        result=execute_case(case,corpus=corpus,arm='disabled',config=p.config,profile='fixture-a',
            output=tmp_path,sample_id='exhausted',context_builder=builder,token_counter=counter)
        assert not result['completed'] and p.requests==1
        assert result['counts']['reportedTokens']==150
        trace=decode((tmp_path/'exhausted-context-trace.json').read_bytes())
        assert [r['reason'] for r in trace['proposals']]==['withinContext']*2


@pytest.mark.parametrize('scenario,requests,usage',[
    ('repair_fact_ids',4,600),('missing_usage',1,None)])
def test_repair_and_unknown_usage_share_one_unchanged_allowance(tmp_path,scenario,requests,usage):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    case,corpus,builder,counter=configuration()
    with fixture_provider([case],scenario=scenario) as p:
        result=execute_case(case,corpus=corpus,arm='disabled',config=p.config,profile='fixture-a',
            output=tmp_path,sample_id='shared',context_builder=builder,token_counter=counter)
        assert result['counts']['providerRequests']==p.requests==requests
        assert result['counts']['reportedTokens']==usage
        assert result['completed']==(scenario=='repair_fact_ids')


def test_native_context_capacity_is_enforced_before_continuation_http(tmp_path):
    from lab_runner.memory.fixture import fixture_provider
    from lab_runner.memory.execution import execute_case
    case,corpus,builder,counter=configuration(count=513,quote=100,capacity=1024)
    with fixture_provider([case]) as p:
        result=execute_case(case,corpus=corpus,arm='disabled',config=p.config,profile='fixture-a',
            output=tmp_path,sample_id='context',context_builder=builder,token_counter=counter)
        assert not result['completed'] and p.requests==1
        trace=decode((tmp_path/'context-context-trace.json').read_bytes())
        assert trace['proposals'][-1]['reason']=='inputCeiling'

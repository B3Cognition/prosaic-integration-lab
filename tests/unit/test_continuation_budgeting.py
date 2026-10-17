"""Quotation is planning evidence; shared Runtime allowance owns v2 dispatch."""
import pytest
from test_memory_context_budget import descriptor,FixedCounter


def plan(*,bounds=(1280,1280,1408,1408),provider='openai-compatible',capacity=32768):
    from lab_runner.memory_policy.budget import make_plan
    desc=descriptor(provider).to_dict();desc['contextCapacityTokens']=capacity
    return make_plan(counter_descriptor=desc,quote_identity='c'*64,request_sha256='d'*64,
        input_bounds=list(bounds),max_requests=4,output_tokens=512,token_ceiling=8192,
        reported_tokens=0,inflight_tokens=0,continuation_budget=True)


def guard(p,*,count=1307):
    from prosaic_runtime import TokenCounterDescriptor,TokenCounterRegistration
    from lab_runner.memory_policy.budget import guard_registration
    base=TokenCounterRegistration(TokenCounterDescriptor.from_dict(p['counterDescriptor']),FixedCounter(count))
    return guard_registration(base,p)


@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
@pytest.mark.parametrize('count,bound',[(1307,1280),(1211,1152)])
def test_affordable_continuation_is_not_limited_by_quotation_slot(provider,count,bound):
    from lab_runner.memory_policy.budget import validate_plan
    p=plan(bounds=[bound]*4,provider=provider);g=guard(p,count=count)
    assert p['version']==2 and p['dispatchPolicy']=='shared-execution-budget-v1'
    assert validate_plan(p)==p and p['inputBounds']==[bound]*4
    assert g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})==count
    row=g.proposals[0]
    assert row['reason']=='withinContext' and row['quotedInputBound']==bound
    assert row['inputCeiling']==8192-512


def test_optional_context_cannot_create_a_larger_hard_continuation_slot():
    ceilings=[]
    for bounds in ([1152]*4,[1408]*4):
        g=guard(plan(bounds=bounds),count=1368)
        assert g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})==1368
        ceilings.append(g.proposals[0]['inputCeiling'])
    assert ceilings==[7680,7680]


@pytest.mark.parametrize('change,reason',[({'model':'other'},'modelMismatch'),
    ({'max_tokens':513},'outputCeiling'),({'max_tokens':True},'outputCeiling')])
def test_v2_cannot_change_model_or_fixed_output_budget(change,reason):
    g=guard(plan());native={'model':'fixture-scoped','max_tokens':512};native.update(change)
    with pytest.raises(ValueError,match=reason):g.registration.counter.count_tokens(native)


@pytest.mark.parametrize('count,reason',[(513,'inputCeiling'),(True,'counterFailure')])
def test_v2_context_capacity_and_counter_type_remain_hard_limits(count,reason):
    g=guard(plan(bounds=[100]*4,capacity=1024),count=count)
    with pytest.raises(ValueError,match=reason):
        g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})
    assert g.proposals[-1]['reason']==reason


@pytest.mark.parametrize('change',[
    {'version':True},{'version':3},{'dispatchPolicy':'ignore-limits'},
    {'dispatchPolicy':None},{'unknown':0},{'requiredTokens':0}])
def test_malformed_v2_plan_is_rejected(change):
    from lab_runner.memory_policy.budget import validate_plan
    p=plan();p.update(change)
    with pytest.raises(ValueError):validate_plan(p)


def test_v2_requires_its_policy_and_cannot_be_silently_downgraded():
    from lab_runner.memory_policy.budget import validate_plan
    p=plan();del p['dispatchPolicy']
    with pytest.raises(ValueError):validate_plan(p)
    p=plan();p['version']=1
    with pytest.raises(ValueError):validate_plan(p)


def test_v2_cannot_bypass_mandatory_plan_rejection_or_proposal_bound():
    p=plan(bounds=[2000]*4);g=guard(p,count=100)
    assert not p['admitted']
    with pytest.raises(ValueError,match='mandatoryRejected'):
        g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})
    g=guard(plan(),count=1307)
    native={'model':'fixture-scoped','max_tokens':512}
    for _ in range(4):g.registration.counter.count_tokens(native)
    with pytest.raises(ValueError,match='proposalLimit'):g.registration.counter.count_tokens(native)


def test_versioned_context_identity_and_freeze_prevent_policy_switch(tmp_path):
    from test_scoped_memory_recovery import policy
    from lab_runner.memory_policy.native import ScopedContext
    from lab_runner.memory.execution import LIMITS,freeze
    case,corpus,legacy,_=policy()
    modern=ScopedContext(legacy.corpus,counter_descriptor=legacy.counter_descriptor,
        quote_inputs=legacy.quote_inputs,quote_identity='c'*64,limits=LIMITS,
        output_tokens=512,continuation_budget=True)
    assert legacy.identity(case)!=modern.identity(case)
    path=tmp_path/'frozen.json';saved=freeze(case,corpus,'disabled',path,context_builder=modern)
    assert saved['contextAssembly']['plan']['version']==2
    assert freeze(case,corpus,'disabled',path,context_builder=modern)==saved
    with pytest.raises(ValueError,match='drift'):
        freeze(case,corpus,'disabled',path,context_builder=legacy)


@pytest.mark.parametrize('flag',[1,None,'true',[],{}])
def test_continuation_policy_requires_a_boolean(flag):
    from lab_runner.memory_policy.budget import make_plan
    p=plan()
    with pytest.raises(ValueError):make_plan(counter_descriptor=p['counterDescriptor'],
        quote_identity='c'*64,request_sha256='d'*64,input_bounds=[100]*4,max_requests=4,
        output_tokens=512,token_ceiling=8192,reported_tokens=0,inflight_tokens=0,
        continuation_budget=flag)

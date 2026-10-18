from copy import deepcopy
import pytest
from lab_runner.quality.contracts import digest
from test_scoped_memory import load,retrieve


def descriptor(provider='openai-compatible'):
    from prosaic_runtime import TokenCounterDescriptor
    return TokenCounterDescriptor(identity='synthetic-'+provider,provider=provider,model='fixture-scoped',
        framing_revision='openai-chat-v1' if provider=='openai-compatible' else 'anthropic-messages-v1',
        context_capacity_tokens=32768,implementation_version='fixture-1',tokenizer_assets_digest='a'*64,
        template_assets_digest='b'*64,counting_kind='exact',guarantee='Synthetic fixture only: reports100input tokens.')


def assemble(*,mandatory=None,retrieval=None,quote=None,ceiling=8192,reported=0,inflight=0,provider='openai-compatible',capacity=32768):
    from lab_runner.memory_policy.assembly import assemble_context
    desc=descriptor(provider).to_dict();desc['contextCapacityTokens']=capacity
    return assemble_context({'task':'current authority','recordIndex':['current']} if mandatory is None else mandatory,
        retrieve(load()) if retrieval is None else retrieval,quote_inputs=(lambda _: [100]*4) if quote is None else quote,
        counter_descriptor=desc,quote_identity='c'*64,max_requests=4,output_tokens=512,
        token_ceiling=ceiling,reported_tokens=reported,inflight_tokens=inflight)


def test_full_trajectory_exact_fit_preserves_mandatory_and_binds_request():
    a=assemble(ceiling=2448)
    assert a['plan']['admitted'] is True and a['plan']['requiredTokens']==2448
    assert a['plan']['inputBounds']==[100,100,100,100] and a['plan']['outputTokens']==512
    assert a['plan']['requestSha256']==digest(a['request'])
    assert a['request']['task']=='current authority' and a['request']['recordIndex']==['current']
    assert [e['episodeId'] for e in a['request']['recalledEpisodes']]==['prior']


def test_optional_recall_is_dropped_for_retry_headroom_not_current_evidence():
    a=assemble(quote=lambda r:[1600]*4 if r['recalledEpisodes'] else [100]*4)
    assert a['request']['recalledEpisodes']==[] and a['plan']['admitted'] is True
    assert a['request']['recordIndex']==['current']
    assert a['decisions']==[dict(episodeId='prior',reason='trajectoryBudget')]
    assert a['retrieval']['resultSha256']==digest([])


def test_mandatory_rejection_is_explicit_and_does_not_call_optional_quotes():
    seen=[]
    def quote(r):seen.append(r['recalledEpisodes']);return [100]*4
    a=assemble(ceiling=2447,quote=quote)
    assert a['plan']['admitted'] is False and a['request']['recordIndex']==['current']
    assert a['request']['recalledEpisodes']==[] and seen==[[]]


def test_existing_usage_and_inflight_reservations_reduce_headroom():
    assert assemble(ceiling=2600,reported=100,inflight=52)['plan']['admitted']
    assert not assemble(ceiling=2600,reported=100,inflight=53)['plan']['admitted']


def test_later_smaller_candidate_can_fit_after_oversized_candidate():
    r=retrieve(load());big=deepcopy(r['episodes'][0]);big['episodeId']='big'
    r['episodes']=[big,r['episodes'][0]];r['resultSha256']=digest(r['episodes'])
    from lab_runner.quality.contracts import encode
    r['resultBytes']=len(encode(r['episodes']))
    a=assemble(retrieval=r,quote=lambda q:[2000]*4 if any(e['episodeId']=='big' for e in q['recalledEpisodes']) else [100]*4)
    assert [e['episodeId'] for e in a['request']['recalledEpisodes']]==['prior']
    assert a['decisions']==[dict(episodeId='big',reason='trajectoryBudget'),dict(episodeId='prior',reason='selected')]


def test_optional_context_capacity_overflow_still_tries_later_fitting_episode():
    from lab_runner.quality.contracts import encode
    r=retrieve(load());big=deepcopy(r['episodes'][0]);big['episodeId']='big'
    r['episodes']=[big,r['episodes'][0]];r['resultSha256']=digest(r['episodes']);r['resultBytes']=len(encode(r['episodes']))
    a=assemble(retrieval=r,capacity=1024,
        quote=lambda q:[600]*4 if any(e['episodeId']=='big' for e in q['recalledEpisodes']) else [100]*4)
    assert a['plan']['admitted'] is True
    assert [e['episodeId'] for e in a['request']['recalledEpisodes']]==['prior']
    assert a['decisions']==[dict(episodeId='big',reason='contextCapacity'),dict(episodeId='prior',reason='selected')]


def test_mandatory_context_capacity_overflow_returns_valid_rejected_plan():
    from lab_runner.memory_policy.budget import validate_plan
    a=assemble(capacity=1024,quote=lambda _:[600]*4)
    assert a['plan']['requiredTokens']==4448 and a['plan']['availableTokens']==8192
    assert a['plan']['admitted'] is False and validate_plan(a['plan'])==a['plan']
    assert a['request']['task']=='current authority' and a['request']['recordIndex']==['current']
    assert a['request']['recalledEpisodes']==[]


@pytest.mark.parametrize('quote',[lambda _:[True]*4,lambda _:[-1]*4,lambda _:[100]*3,lambda _:[1.5]*4,lambda _:{'inputBounds':[100]*4}])
def test_invalid_quote_never_becomes_a_zero_cost_fallback(quote):
    with pytest.raises(ValueError):assemble(quote=quote)


def test_quote_failure_and_mutation_cannot_corrupt_owned_context():
    mandatory={'task':'current','recordIndex':['current']}
    def mutate(r):r['task']='corrupted';r['recordIndex'].clear();return [100]*4
    a=assemble(mandatory=mandatory,quote=mutate)
    assert a['request']['task']=='current' and a['request']['recordIndex']==['current']
    assert mandatory=={'task':'current','recordIndex':['current']}
    def fail(_):raise RuntimeError('counter unavailable')
    with pytest.raises(ValueError):assemble(quote=fail)


def test_reserved_recall_and_tampered_retrieval_fail_admission():
    with pytest.raises(ValueError):assemble(mandatory={'recalledEpisodes':[]})
    r=retrieve(load());r['episodes'][0]['note']='forged'
    with pytest.raises(ValueError):assemble(retrieval=r)


class FixedCounter:
    def __init__(self,value=100):self.value=value
    def count_tokens(self,native):return self.value


def guard(plan=None,*,provider='openai-compatible',value=100):
    from prosaic_runtime import TokenCounterRegistration
    from lab_runner.memory_policy.budget import guard_registration
    return guard_registration(TokenCounterRegistration(descriptor(provider),FixedCounter(value)),
        assemble(provider=provider)['plan'] if plan is None else plan)


@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
def test_guard_returns_actual_bound_for_each_slot_and_refuses_extra_proposals(provider):
    g=guard(provider=provider);native={'model':'fixture-scoped','max_tokens':512,'messages':[]}
    assert [g.registration.counter.count_tokens(native) for _ in range(4)]==[100]*4
    with pytest.raises(ValueError):g.registration.counter.count_tokens(native)
    assert g.proposals[-1]['reason']=='proposalLimit'
    g.proposals[0]['inputBound']=0
    assert g.proposals[0]['inputBound']==100


@pytest.mark.parametrize('change,reason',[('input','inputCeiling'),('output','outputCeiling'),('model','modelMismatch'),('booleanCount','counterFailure')])
def test_guard_refuses_inputs_outside_planned_domain(change,reason):
    g=guard(value=101 if change=='input' else True if change=='booleanCount' else 100)
    native={'model':'wrong' if change=='model' else 'fixture-scoped','max_tokens':513 if change=='output' else 512,'messages':[]}
    with pytest.raises(ValueError):g.registration.counter.count_tokens(native)
    assert g.proposals[-1]['reason']==reason


def test_rejected_mandatory_plan_can_never_dispatch_and_plan_is_owned():
    p=assemble(ceiling=1)['plan'];g=guard(p);p['admitted']=True
    with pytest.raises(ValueError):g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})
    assert g.proposals[-1]['reason']=='mandatoryRejected'


def test_counter_descriptor_and_plan_arithmetic_are_verified():
    from prosaic_runtime import TokenCounterRegistration
    from lab_runner.memory_policy.budget import guard_registration
    p=assemble()['plan'];changed=descriptor().to_dict();changed['guarantee']='changed under same identity'
    from prosaic_runtime import TokenCounterDescriptor
    with pytest.raises(ValueError):guard_registration(TokenCounterRegistration(TokenCounterDescriptor.from_dict(changed),FixedCounter()),p)
    p['requiredTokens']=0
    with pytest.raises(ValueError):guard(p)


def test_non_serializable_counter_failure_retains_a_serializable_trace():
    g=guard(value=object())
    with pytest.raises(ValueError):g.registration.counter.count_tokens({'model':'fixture-scoped','max_tokens':512})
    assert g.proposals[-1]['reason']=='counterFailure'
    assert g.proposals[-1]['inputBound'] is None


@pytest.mark.parametrize('provider',['openai-compatible','anthropic'])
def test_public_runtime_refuses_before_http_without_debit(provider,tmp_path):
    from prosaic_runtime import ProsaicRuntime,RuntimeConfig,EndpointConfig,ProsaicArtifact,RunPolicy,ExecutionBudget
    g=guard(provider=provider,value=101)
    config=RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:1','fixture-scoped',
        provider=provider,max_tokens=512)}, {'fixture':'fixture'},'fixture')
    artifact=ProsaicArtifact('bounded','subagent',dict(name='bounded',description='Fixture',model_tier='fixture'), 'Reply OK.')
    budget=ExecutionBudget(timeout_s=10,max_provider_requests=4,max_tool_calls=2,max_reported_tokens=8192,
        token_counter=g.registration)
    with budget.activate():
        result=ProsaicRuntime(config).run(artifact,{},cwd=tmp_path,policy=RunPolicy(max_provider_requests=2))
    assert result.exit_code!=0 and budget.provider_requests==0 and budget.reported_tokens==0
    assert g.proposals[-1]['reason']=='inputCeiling'

"""Real HTTP, installed SDKs, no model credentials or live allowance."""
from copy import deepcopy
import pytest


@pytest.mark.parametrize('provider', ['openai', 'anthropic'])
@pytest.mark.parametrize('scenario,first,safe,quality', [
    ('correct', None, True, True),
    ('reject', None, True, True),
    ('missing', None, True, True),
    ('conflict', None, True, True),
    ('unread', 'worker', True, False),
    ('wrong_worker', 'worker', True, False),
    ('missed_flaw', 'worker', True, False),
    ('false_critic', 'critic', True, False),
    ('forged_evidence', 'worker', True, False),
    ('repeat_tools', 'worker', True, False),
    ('wrong_assignment', 'planner', True, False),
    ('wrong_binding', 'worker', True, False),
    ('invalid_json', 'worker', True, False),
    ('unknown_usage', 'worker', True, False),
])
def test_bounded_typed_handoffs(tmp_path, provider, scenario, first, safe, quality):
    from lab_runner.handoffs.fixture import fixture_provider, example_case
    from lab_runner.handoffs.execution import execute_case, recover_case
    from lab_runner.handoffs.scoring import score_trajectory
    case = example_case(scenario)
    with fixture_provider(case, scenario=scenario, provider=provider) as p:
        evidence = execute_case(case, config=p.config, output=tmp_path, sample_id='typed')
        calls = p.requests
        assert calls <= 4
        assert evidence['counts']['providerRequests'] == calls
        assert evidence['counts']['toolCalls'] <= 2
        if evidence['counts']['reportedTokens'] is not None:
            assert evidence['counts']['reportedTokens'] <= 8192
        original = deepcopy(evidence['receipts'])
        p.deny = True
        recovered = recover_case(case, config=p.config, output=tmp_path, sample_id='typed')
        assert p.requests == calls
        assert recovered['receipts'] == original
    score = score_trajectory(case, evidence)
    assert score['firstFailure'] == first, score
    assert score['safe'] is safe
    assert score['qualityPassed'] is quality
    if scenario in {'correct', 'reject'}:
        assert evidence['checkpoint']['status'] == 'completed'
    elif scenario in {'missing', 'conflict', 'unread', 'wrong_worker', 'missed_flaw', 'false_critic','forged_evidence'}:
        assert evidence['checkpoint']['status'] == 'waiting'
        assert evidence['checkpoint']['current'] == 'human-review'
    if scenario == 'unknown_usage':
        assert calls == 3 and evidence['counts']['reportedTokens'] is None
    if scenario not in {'wrong_assignment', 'wrong_binding', 'invalid_json', 'unknown_usage','repeat_tools'}:
        assert [r['step'] for r in evidence['receipts']] == ['planner', 'worker', 'critic']
        assert evidence['receipts'][-1]['arguments']['artifacts']['worker'] == evidence['checkpoint']['outputs']['worker']
        worker = evidence['checkpoint']['outputs']['worker']
        if scenario!='forged_evidence':
            assert worker['evidence'] == [case['records'][k] for k in evidence['journal'][0]['recordIds']]


def test_case_rejects_incomplete_index_before_dispatch(tmp_path):
    from lab_runner.handoffs.fixture import fixture_provider, example_case
    from lab_runner.handoffs.execution import execute_case
    case = example_case('correct');case['recordIndex'] = case['recordIndex'][:1]
    with fixture_provider(case) as p:
        with pytest.raises(ValueError, match='index'):
            execute_case(case, config=p.config, output=tmp_path, sample_id='bad-index')
        assert p.requests == 0


def test_private_answer_key_does_not_control_acceptance(tmp_path):
    from lab_runner.handoffs.fixture import fixture_provider, example_case
    from lab_runner.handoffs.execution import execute_case
    case = example_case('correct');case['expected'] = {'decision': 'reject'}
    with fixture_provider(case) as p:
        evidence = execute_case(case, config=p.config, output=tmp_path, sample_id='no-gold')
    assert evidence['checkpoint']['status'] == 'completed'


def test_offline_entry_denies_remote_fixture_named_model(tmp_path):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.handoffs.execution import execute_case
    from lab_runner.handoffs.fixture import example_case
    config=RuntimeConfig({'remote':EndpointConfig('https://example.invalid/v1',
        'typed-handoff-fixture',max_tokens=512)}, {},'remote')
    with pytest.raises(ValueError,match='loopback'):
        execute_case(example_case(),config=config,output=tmp_path,sample_id='remote')


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_overrun_is_reported_without_critic_dispatch(tmp_path,provider):
    from lab_runner.handoffs.fixture import example_case,fixture_provider
    from lab_runner.handoffs.execution import execute_case
    from lab_runner.handoffs.scoring import score_trajectory
    case=example_case()
    with fixture_provider(case,scenario='overrun',provider=provider) as p:
        e=execute_case(case,config=p.config,output=tmp_path,sample_id='overrun')
        assert p.requests==3
    assert e['counts']['reportedTokens']>8192
    score=score_trajectory(case,e)
    assert not score['qualityPassed'] and score['safe'] and score['firstFailure']=='worker'


def test_recovery_rejects_changed_source_without_dispatch(tmp_path):
    from lab_runner.handoffs.fixture import example_case,fixture_provider
    from lab_runner.handoffs.execution import execute_case,recover_case
    case=example_case()
    with fixture_provider(case) as p:
        execute_case(case,config=p.config,output=tmp_path,sample_id='drift')
        calls=p.requests;p.deny=True
        case['records']['metrics']['value']=12
        with pytest.raises(Exception,match='(?i)(drift|fingerprint|identity|mismatch)'):
            recover_case(case,config=p.config,output=tmp_path,sample_id='drift')
        assert p.requests==calls


def test_scoring_cannot_certify_a_blocked_valid_trajectory_or_changed_counts(tmp_path):
    from lab_runner.handoffs.fixture import example_case,fixture_provider
    from lab_runner.handoffs.execution import execute_case
    from lab_runner.handoffs.scoring import score_trajectory
    case=example_case()
    with fixture_provider(case) as p:
        original=execute_case(case,config=p.config,output=tmp_path,sample_id='score')
    blocked=deepcopy(original);blocked['checkpoint']['status']='blocked'
    assert score_trajectory(case,blocked)['firstFailure']=='trajectory'
    counts=deepcopy(original);counts['counts']['providerRequests']=0
    assert score_trajectory(case,counts)['firstFailure']=='accounting'


@pytest.mark.parametrize('saved',[True,False])
def test_interrupted_critic_recovery_never_dispatches(tmp_path,saved):
    from prosaic_harness import Harness,FileRunStore
    from lab_runner.handoffs.execution import materials,recover_case
    from lab_runner.handoffs.fixture import example_case,fixture_provider
    from lab_runner.quality.contracts import digest
    from lab_runner.quality.recovery import InjectedInterruption
    class CrashOnCritic:
        def __init__(self,store):self.store=store
        def __getattr__(self,name):return getattr(self.store,name)
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            if receipt['step']=='critic' and not saved:raise InjectedInterruption()
            self.store.save_receipt(run_id,invocation_id,receipt,lease)
            if receipt['step']=='critic':raise InjectedInterruption()
    case=example_case()
    with fixture_provider(case) as p:
        workflow,request,_=materials(case,p.config,tmp_path,'crash')
        store=FileRunStore(tmp_path/'store',namespace='typed-handoffs');store.initialize()
        try:
            h=Harness(workflow,store=CrashOnCritic(store),run_id=digest(dict(sampleId='crash'))[:32])
            with pytest.raises(InjectedInterruption):h.run(request)
        finally:store.close()
        assert p.requests==4;p.deny=True
        e=recover_case(case,config=p.config,output=tmp_path,sample_id='crash')
        assert p.requests==4
    assert e['checkpoint']['status']==('completed' if saved else 'blocked')
    assert e['counts']['reportedTokens']==(600 if saved else None)

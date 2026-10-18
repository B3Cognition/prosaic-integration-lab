"""Bounded consumer behavior through real public SDKs and scripted transport."""
import importlib.util
from copy import deepcopy
import pytest
from lab_runner.quality.contracts import decode,digest


def modules():
    assert importlib.util.find_spec('lab_runner.handoffs.correction'),'correction graph missing'
    assert importlib.util.find_spec('lab_runner.handoffs.correction_fixture'),'correction fixture missing'
    from lab_runner.handoffs import correction as c,correction_fixture as f
    return c,f


@pytest.mark.parametrize('provider',['openai','anthropic'])
@pytest.mark.parametrize('scenario',['correct','wrong_decision','missing','unread','critic_partial','critic_false','ignore_feedback','regress'])
def test_matched_arms_share_grounding_and_never_accept_an_incorrect_correction(tmp_path,provider,scenario):
    c,f=modules();case=f.example_case(scenario);scores=[];evidence=[]
    with f.fixture_provider(case,provider=provider,scenario=scenario) as p:
        for arm in ('no-critic','critic'):
            out=tmp_path/arm
            e=c.execute_correction(case,config=p.config,output=out,sample_id=arm,arm=arm)
            before=deepcopy(e);score=c.score_correction(case,e);assert e==before
            assert e['counts']['providerRequests']<=(2 if scenario=='correct' else 3 if arm=='no-critic' else 4)
            assert e['counts']['toolCalls']==1 and e['counts']['reportedTokens']<=8192
            assert score['safe'] and score['matchedEligible']
            if scenario=='correct':
                assert not score['correctionReached'] and score['taskAccepted']
                assert [r['step'] for r in e['receipts']]==['worker']
            elif scenario in ('ignore_feedback','regress'):
                assert score['correctionReached'] and not score['finalArtifactCorrect'] and not score['taskAccepted']
            else:
                assert score['correctionReached'] and score['finalArtifactCorrect']
                assert score['taskAccepted']==(scenario not in ('missing','unread'))
            scores.append(score);evidence.append(e)
        assert not p.errors
        p.deny=True;requests=p.requests
        for arm,original in zip(('no-critic','critic'),evidence):
            restored=c.recover_correction(case,config=p.config,output=tmp_path/arm,sample_id=arm,arm=arm)
            assert restored['receiptDigests']==original['receiptDigests'] and p.requests==requests
            assert c.score_correction(case,restored)==c.score_correction(case,original)
        from lab_runner.bounded_correction import compare_corrections
        pair=compare_corrections(*scores)
        assert pair['matched'] and pair['answerGain']==0
        assert pair['marginalCounts']['providerRequests']==(0 if scenario=='correct' else 1)
        assert not pair['causalModelBenefitEstablished']
        assert all('expected' not in str(value) and 'gold' not in str(value) for value in p.feedbacks)


@pytest.mark.parametrize('arm',['no-critic','critic'])
@pytest.mark.parametrize('scenario',['invalid_worker','unknown_usage','overrun','input_breach','output_breach','corrector_tools','invalid_correction'])
def test_unusable_or_overbudget_work_cannot_trigger_unbounded_correction(tmp_path,arm,scenario):
    c,f=modules();case=f.example_case(scenario)
    with f.fixture_provider(case,scenario=scenario) as p:
        e=c.execute_correction(case,config=p.config,output=tmp_path,sample_id='fault',arm=arm)
        score=c.score_correction(case,e)
        assert e['counts']['providerRequests']<=4 and e['counts']['toolCalls']<=1
        assert not score['taskAccepted'] and not p.errors
        correction=[r for r in e['receipts'] if r['step']=='corrector']
        assert len(correction)<=1
        if correction:
            assert correction[0]['result']['metadata']['invocation_budgets_v1']['provider_requests']<=1
        if scenario=='unknown_usage':assert e['counts']['reportedTokens'] is None and not correction
        if scenario=='overrun':assert e['counts']['reportedTokens']>8192 and not correction
        if scenario in ('input_breach','output_breach'):assert e['admissionViolation'] and not correction
        p.deny=True;requests=p.requests
        with pytest.raises(ValueError):c.execute_correction(case,config=p.config,output=tmp_path,sample_id='fault',arm=arm)
        assert p.requests==requests


def test_changed_journal_and_pair_draft_cannot_become_a_success(tmp_path):
    c,f=modules();case=f.example_case('wrong_decision')
    with f.fixture_provider(case,scenario='wrong_decision') as p:
        e=c.execute_correction(case,config=p.config,output=tmp_path,sample_id='changed',arm='critic')
    e['journal'][0]['recordsSha256']='0'*64
    with pytest.raises(ValueError):c.score_correction(case,e)


def test_exhausted_continuation_reservation_stops_before_corrector(tmp_path):
    c,f=modules();case=f.example_case('wrong_decision')
    from prosaic_runtime import TokenCounterRegistration,TokenCounterDescriptor
    class Counter:
        def __init__(self):self.calls=0
        def count_tokens(self,native):self.calls+=1;return 8000 if self.calls==4 else 100
    with f.fixture_provider(case,scenario='wrong_decision') as p:
        ep=p.config.profiles[p.config.default_profile]
        reg=TokenCounterRegistration(TokenCounterDescriptor(identity='bounded-test',provider=ep.provider,
            model=ep.model,framing_revision='openai-chat-v1',context_capacity_tokens=32768,
            implementation_version='fixture-v1',tokenizer_assets_digest='a'*64,template_assets_digest='b'*64,
            counting_kind='exact',guarantee='Synthetic units only.'),Counter())
        e=c.execute_correction(case,config=p.config,output=tmp_path,sample_id='admission',arm='critic',token_counter=reg)
        assert p.requests==3 and e['counts']['providerRequests']==3
    assert not c.score_correction(case,e)['taskAccepted']
    score=c.score_correction(case,e)
    assert not score['correctionCalled'] and score['correctionEffect']=='not_dispatched'


def test_new_errors_are_reported_as_regression(tmp_path):
    c,f=modules();case=f.example_case('regress')
    with f.fixture_provider(case,scenario='regress') as p:
        e=c.execute_correction(case,config=p.config,output=tmp_path,sample_id='regressed')
    score=c.score_correction(case,e)
    assert score['correctionEffect']=='regressed'
    assert score['newIssueFields']==['citations','facts'] and score['resolvedIssueFields']==['decision']


@pytest.mark.parametrize('scenario',['invalid_critic','critic_unknown'])
def test_baseline_comparison_retains_critic_failures_and_unknown_costs(tmp_path,scenario):
    c,f=modules();case=f.example_case(scenario);scores=[]
    with f.fixture_provider(case,scenario=scenario) as p:
        for arm in ('no-critic','critic'):
            e=c.execute_correction(case,config=p.config,output=tmp_path/arm,sample_id=arm,arm=arm)
            scores.append(c.score_correction(case,e))
        assert not p.errors
    assert scores[0]['taskAccepted'] and not scores[1]['correctionReached'] and not scores[1]['taskAccepted']
    from lab_runner.bounded_correction import compare_corrections
    result=compare_corrections(*scores)
    assert result['matched']
    if scenario=='invalid_critic':assert result['answerGain']==-1 and result['marginalCounts']['providerRequests']==0
    else:assert not result['accountingKnown'] and result['answerGain'] is result['marginalCounts'] is None


def test_final_component_breach_cannot_accept_a_corrected_answer(tmp_path):
    c,f=modules();case=f.example_case('final_breach')
    with f.fixture_provider(case,scenario='final_breach') as p:
        e=c.execute_correction(case,config=p.config,output=tmp_path,sample_id='final-breach',arm='critic')
        assert p.requests==4 and not p.errors
    score=c.score_correction(case,e)
    assert e['admissionViolation'] and not score['taskAccepted'] and not score['withinLimits']


def test_interrupted_critic_observation_is_not_lost_from_recovery_or_costs(tmp_path):
    c,f=modules();case=f.example_case('wrong_decision')
    def stop(event):
        if event.get('event')=='completed' and event.get('step')=='critic':raise KeyboardInterrupt('host interrupted')
    with f.fixture_provider(case,scenario='wrong_decision') as p:
        with pytest.raises(KeyboardInterrupt):
            c.execute_correction(case,config=p.config,output=tmp_path,sample_id='interrupted',arm='critic',on_event=stop)
        assert p.requests==3;p.deny=True
        restored=c.recover_correction(case,config=p.config,output=tmp_path,sample_id='interrupted',arm='critic')
        score=c.score_correction(case,restored)
        assert p.requests==3 and restored['counts']['reportedTokens'] is None
        assert score['criticCalled'] and not score['correctionCalled']
        assert score['roleCosts']['critic']['observedRequests']==1 and score['roleCosts']['critic']['observedTokens']==150
        assert score['roleCosts']['critic']['unreceiptedObservations']==1
        assert not score['withinLimits'] and score['safeStopped'] and not score['taskAccepted']


def test_unresolved_critic_intent_is_visible_without_inventing_usage(tmp_path):
    from lab_runner.quality.contracts import encode
    c,f=modules();case=f.example_case('wrong_decision')
    def stop(event):
        if event.get('event')=='completed' and event.get('step')=='critic':raise KeyboardInterrupt
    with f.fixture_provider(case,scenario='wrong_decision') as p:
        with pytest.raises(KeyboardInterrupt):
            c.execute_correction(case,config=p.config,output=tmp_path,sample_id='unresolved',arm='critic',on_event=stop)
        path=tmp_path/'unresolved-context-trace.json';trace=decode(path.read_bytes())
        critic_call=next(k for k,v in trace['intents'].items() if v['context']['step_id']=='critic')
        trace['observations'].pop(critic_call);path.write_bytes(encode(trace))
        p.deny=True
        e=c.recover_correction(case,config=p.config,output=tmp_path,sample_id='unresolved',arm='critic')
        score=c.score_correction(case,e)
        assert score['criticReached'] and not score['criticCalled']
        assert score['roleCosts']['critic']['unresolvedIntents']==1
        assert score['roleCosts']['critic']['observedTokens'] is None and not score['accountingComplete']
        assert p.requests==3

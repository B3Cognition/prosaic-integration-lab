import json
import pytest


def test_corrector_provider_input_is_projected_but_receipt_and_usage_are_preserved(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    case=load_suite()['cases'][8]
    with fixture_provider(scenario='public_check_once') as provider:
        e=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                       sample_id='projected-corrector',limits=provider.case_limits)
        arguments=[json.loads(next(m['content'] for m in p['messages'] if m['role']=='user').rsplit('## Arguments\n',1)[1])
                   for p in provider.payloads if not any(m['role']=='tool' for m in p['messages'])]
        requests=provider.requests
    assert e['completed'] is True
    correction=arguments[1]
    assert set(correction)=={'caseId','correctionTarget','recordIndex'}
    assert correction['correctionTarget']=={'approved':False,'issues':['decision','facts','citations']}
    assert correction['recordIndex']==case['recordIndex']
    assert arguments[0]['request']['task']==case['task']
    assert e['receipts'][1]['arguments']['request']['draft']==case['draft']
    assert e['counts']['providerRequests']==requests==6
    assert e['counts']['toolCalls']==len(e['journal'])==3
    assert len(e['receipts'][1]['result']['metadata']['runtime_adapter_v1']['attempts'])==1


def test_rejected_critic_uses_a_distinct_correction_step_and_binds_it_to_author(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    with fixture_provider(scenario='public_check_once') as provider:
        e=execute_case(load_suite()['cases'][8],config=provider.config,profile='fixture',output=tmp_path,
                       sample_id='distinct-correction',limits=provider.case_limits)
    assert e['completed'] is True
    assert [r['step'] for r in e['receipts']]==['critic','review-correction','author']
    assert e['receipts'][1]['result']['metadata']['artifact_id']=='quality-review-corrector'
    assert e['receipts'][1]['arguments']['artifacts']['critic']=={'approved':True,'issues':[]}
    assert e['receipts'][-1]['arguments']['artifacts']['review-correction']=={
        'approved':False,'issues':['decision','facts','citations']}


def test_bad_dedicated_correction_stays_blocked_without_an_author_call(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    with fixture_provider(scenario='stubborn_review') as provider:
        e=execute_case(load_suite()['cases'][8],config=provider.config,profile='fixture',output=tmp_path,
                       sample_id='bad-correction',limits=provider.case_limits)
    assert e['completed'] is False and e['reason']=='attempt_limit'
    assert [r['step'] for r in e['receipts']]==['critic','review-correction']
    assert e['criticDetected'] is False
    assert e['counts']['providerRequests']==4 and e['counts']['toolCalls']==2


@pytest.mark.parametrize('case_id,target',[
    ('missing-01',{'decision':'insufficient','facts':['success'],
                   'citations':[{'factId':'success','recordId':'metrics'}]}),
    ('repair-01',{'approved':False,'issues':['decision','facts','citations']})])
def test_retry_feedback_has_one_compact_public_target(tmp_path,case_id,target):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    case=next(c for c in load_suite()['cases'] if c['caseId']==case_id)
    with fixture_provider(scenario='public_check_once') as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='compact-retry',limits=provider.case_limits)
    feedback=evidence['receipts'][1]['arguments']['validation_feedback']
    value=json.loads(feedback.removeprefix('publicCheck '))
    assert value.get('target')==target
    assert 'assessment' not in value
    assert len(feedback.encode())<768


def test_critic_feedback_names_only_the_mismatched_review_field(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    with fixture_provider(scenario='partial_critic_once') as provider:
        e=execute_case(load_suite()['cases'][8],config=provider.config,profile='fixture',output=tmp_path,
                       sample_id='partial-review',limits=provider.case_limits)
    feedback=json.loads(e['receipts'][1]['arguments']['validation_feedback'].removeprefix('publicCheck '))
    assert feedback['fields']==['issues']
    assert feedback['target']=={'approved':False,'issues':['decision','facts','citations']}


def test_private_expected_answer_cannot_control_host_validation(tmp_path):
    from copy import deepcopy
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    case=deepcopy(load_suite()['cases'][0]);case['expected']['decision']='reject'
    with fixture_provider() as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='no-answer-key',limits=provider.case_limits)
    assert evidence['completed'] is True
    assert evidence['answer']['decision']=='approve'


@pytest.mark.parametrize('case_id',['missing-01','repair-01'])
def test_public_check_feedback_corrects_wrong_decision_or_missed_critic(tmp_path,case_id):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case=next(c for c in load_suite()['cases'] if c['caseId']==case_id)
    with fixture_provider(scenario='public_check_once') as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='public-retry',limits=provider.case_limits)
        feedback=[json.dumps(p) for p in provider.payloads if 'publicCheck ' in json.dumps(p) or 'correctionTarget' in json.dumps(p)]
    assert score_case(case,evidence)['state']=='passed'
    assert evidence['taskRepairs']==1 and evidence['schemaRepairs']==0
    assert feedback
    assert 'target' in feedback[0] or 'correctionTarget' in feedback[0]
    if case_id.startswith('repair'):
        assert evidence['criticDetected'] is True
        assert [a['step'] for a in evidence['attempts']]==['critic','review-correction','author']
    else:assert evidence['answer']['decision']=='insufficient'


def test_correct_draft_is_accepted_as_control_without_forcing_disapproval(tmp_path):
    from copy import deepcopy
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    case=deepcopy(load_suite()['cases'][8]);case['draft']=deepcopy(case['expected'])
    with fixture_provider(scenario='correct_draft') as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='correct-control',limits=provider.case_limits)
    assert evidence['completed'] is True and evidence['taskRepairs']==0
    review=json.loads(evidence['receipts'][0]['result']['stdout'])
    assert review=={'approved':True,'issues':[]}


def test_retry_cannot_borrow_records_from_previous_attempt(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    with fixture_provider(scenario='stale_attempt') as provider:
        evidence=execute_case(load_suite()['cases'][0],config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='stale-attempt',limits=provider.case_limits)
    assert evidence['completed'] is False and evidence['reason']=='attempt_limit'
    assert evidence['counts']['toolCalls']==2


def test_missing_current_records_never_offer_a_copyable_correction_target(tmp_path):
    from lab_runner.quality.suite import load_suite,public_case
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import materials
    from prosaic_harness import Harness,FileRunStore
    case=load_suite()['cases'][0]
    with fixture_provider(scenario='stale_attempt') as provider:
        workflow,_,events=materials(case,provider.config,'fixture','target-free',provider.case_limits)
        store=FileRunStore(tmp_path/'store',namespace='target-free');store.initialize()
        try:state=Harness(workflow,store=store,run_id='f'*32,on_event=events).run(public_case(case))
        finally:store.close()
    feedback=json.loads(state['feedback'].removeprefix('publicCheck '))
    assert state['status']=='blocked'
    assert feedback=={'error':'fetchCurrentRecordsBeforeDeciding','missingRecords':['incident']}


@pytest.mark.parametrize('index',range(10))
def test_fixture_executes_lookup_and_scores_receipt(tmp_path,index):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][index]
    with fixture_provider(scenario='correct') as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='sample-'+str(index),limits=provider.case_limits)
        assert provider.requests==evidence['counts']['providerRequests']
        assert len(evidence['journal'])==evidence['counts']['toolCalls']
        # Expected answers live only in the fixture oracle, never in request JSON.
        for request in provider.payloads:
            assert 'requiredRecords' not in json.dumps(request)
            assert '"expected"' not in json.dumps(request)
    assert score_case(case,evidence)['state']=='passed',evidence
    assert evidence['counts']['reportedTokens']>0
    assert all(a['elapsedSeconds']>=0 for a in evidence['attempts'])
    if case['kind']=='repair':assert evidence['criticDetected'] is True


@pytest.mark.parametrize('scenario',['wrong','simulated','missing_usage','invalid_json','wrong_record'])
def test_failure_cannot_be_accepted_as_task_success(tmp_path,scenario):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][0]
    with fixture_provider(scenario=scenario) as provider:
        evidence=execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                              sample_id='failed',limits=provider.case_limits)
    assert score_case(case,evidence)['state']=='failed'
    if scenario=='missing_usage':assert evidence['counts']['reportedTokens'] is None


def test_repair_succeeds_after_one_schema_rejection(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][0]
    with fixture_provider(scenario='repair_once') as p:
        e=execute_case(case,config=p.config,profile='fixture',output=tmp_path,
                       sample_id='repair-once',limits=p.case_limits)
    assert score_case(case,e)['state']=='passed'
    assert e['firstPass'] is False and e['schemaRepairs']==1


def test_semantically_equal_fact_and_citation_order_is_accepted(tmp_path):
    from lab_runner.quality.suite import load_suite
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.scoring import score_case
    case=load_suite()['cases'][0]
    with fixture_provider(scenario='permuted') as p:
        e=execute_case(case,config=p.config,profile='fixture',output=tmp_path,
                       sample_id='permuted',limits=p.case_limits)
    assert score_case(case,e)['state']=='passed'
    assert e['taskRepairs']==0


@pytest.mark.parametrize('index',[0,8])
def test_provider_receives_the_complete_public_output_schema(tmp_path,index):
    from lab_runner.quality.suite import load_suite,resource
    from lab_runner.quality.fixture import fixture_provider
    from lab_runner.quality.execution import execute_case
    from lab_runner.quality.contracts import encode
    case=load_suite()['cases'][index]
    with fixture_provider() as provider:
        execute_case(case,config=provider.config,profile='fixture',output=tmp_path,
                     sample_id='visible-schema',limits=provider.case_limits)
        for payload in provider.payloads:
            text='\n'.join(m.get('content') or '' for m in payload['messages'] if m['role']!='tool')
            schema='review' if 'supplied flawed draft' in text or 'correctionTarget' in text else 'answer'
            assert encode(json.loads(resource(schema+'.schema.json'))).decode() in text
            assert '"expected"' not in text and 'requiredRecords' not in text


def test_provenance_binds_the_effective_schema_bearing_instructions():
    from lab_runner.quality.suite import agent_prose,load_suite,resource
    from lab_runner.quality.runner import identity
    from lab_runner.quality.execution import CASE_LIMITS
    from lab_runner.quality.contracts import digest
    prose={name:agent_prose(name) for name in ('reviewer','critic','author','review-corrector')}
    assert identity(load_suite(),CASE_LIMITS)['proseDigest']==digest(prose)
    assert all(prose[name]!=resource(name+'.md') for name in prose)

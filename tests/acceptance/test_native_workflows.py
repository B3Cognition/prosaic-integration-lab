"""Required actual HTTP native SDK flows through alternating fresh workers."""
import copy
import json
import uuid

import httpx
import psycopg
from psycopg.types.json import Jsonb
import pytest

from lab_runner.native_scenarios import approved_proposal,control,calls,replace_worker
from test_approval import headers


def http(lab,method,path,*,actor='alice',worker='a',status=200,**kwargs):
    result=httpx.request(method,lab[worker]+path,headers={**headers(lab,actor),**kwargs.pop('headers',{})},
                        timeout=35,**kwargs)
    assert result.status_code==status,result.status_code
    return result.json()


def propose(lab,body=None,*,actor='alice',key=None,worker='a',status=200):
    return http(lab,'POST','/workflow-proposals',actor=actor,worker=worker,status=status,
        headers={'Idempotency-Key':key or uuid.uuid4().hex},json=body or approved_proposal())


def start(lab,proposal=None,*,entity=None,key=None,actor='alice',worker='a',status=200):
    proposal=proposal or propose(lab,actor=actor)
    return http(lab,'POST','/native-runs',actor=actor,worker=worker,status=status,
        headers={'Idempotency-Key':key or uuid.uuid4().hex},
        json={'proposal_id':proposal['proposal_id'],'inputs':{'entity_id':entity or uuid.uuid4().hex}})


def pause():
    return {'definition':{'version':1,'start':'ask','steps':{
        'ask':{'kind':'pause','question':'Synthetic confirmation?',
               'choices':{'accept':'done','reject':'done'},'response_schema':'decision'},
        'done':{'kind':'finish'}}}}


def resume(lab,run,*,worker='b',status=200,**body):
    return http(lab,'POST','/runs/'+run['run_id']+'/resume',worker=worker,status=status,
        json={'expected_revision':run['revision'],'choice':'accept','response':{'confirmed':True},**body})


@pytest.fixture(autouse=True)
def native_model(lab):
    control(lab,scenario='native')
    yield
    control(lab)


def test_native_graph_cross_worker_fresh_process_pause_approval_and_provenance(lab):
    before=calls(lab)
    stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
    provenance=stats.json()['provenance_calls']
    run=start(lab,entity='sample-1')
    assert run['status']=='waiting' and set(run['interaction']['choices'])=={'accept','reject'}
    assert run['interaction']['reviewOutputs']=={'review':{'entity_id':'sample-1','approved':True}}
    replace_worker(lab)
    assert resume(lab,run)['status']=='completed'
    assert calls(lab)==before+2
    stats=httpx.get(lab['model']+'/stats',timeout=5);stats.raise_for_status()
    assert stats.json()['provenance_calls']==provenance+1
    usage=http(lab,'GET','/runs/'+run['run_id']+'/usage',worker='b')
    assert usage['total_calls']==2 and usage['complete_calls']==2


def test_native_adoption_demo_runs_public_protocol_and_filtered_receipt(lab):
    from lab_runner.native_demo import capture_native
    before=calls(lab)
    report=capture_native(lab)
    assert report['status']=='completed' and report['independent_model_calls']==2
    assert calls(lab)==before+2
    assert report['usage']=={'total_calls':2,'complete_calls':2,'unresolved_calls':0,'billing_eligible':False}
    assert report['checks']=={'admission_without_model_calls':True,'proposal_replay':True,
        'start_replay':True,'invalid_response_unchanged':True,'stale_revision_unchanged':True,
        'owner_isolation':True,'resume_without_model_calls':True}
    assert report['interaction']['stepId']=='confirm'
    assert report['interaction']['reviewOutputs']=={'review':{'entity_id':'sample-1','approved':True}}
    exported=json.dumps(report)
    assert all(token not in exported for token in lab['principals'])
    assert all(lab[name] not in exported for name in ('a','b','model','app_dsn','harness_dsn','accounting_dsn'))
    assert set(report)=={'version','fixture','status','catalogue','steps','proposal_id','run_id',
                        'interaction','checks','usage','independent_model_calls'}


@pytest.mark.parametrize('response',[{'confirmed':'bad'},{'confirmed':True,'private':'injected'}])
def test_invalid_structured_response_preserves_committed_revision(lab,response):
    run=start(lab);before=calls(lab)
    resume(lab,run,status=422,response=response)
    assert http(lab,'GET','/runs/'+run['run_id'],worker='b')==run
    assert calls(lab)==before


def test_stale_response_cannot_record_human_decision(lab):
    run=start(lab);before=calls(lab)
    resume(lab,run,status=409,expected_revision='stale')
    assert http(lab,'GET','/runs/'+run['run_id'],worker='b')==run
    assert calls(lab)==before


def test_owner_isolation_catalogue_proposal_run_interaction_usage(lab):
    a=http(lab,'GET','/workflow-catalogue');b=http(lab,'GET','/workflow-catalogue',actor='carol')
    assert a['manifest']!=b['manifest'] and 'http://model' not in json.dumps(a)
    proposal=propose(lab);run=start(lab,proposal);before=calls(lab)
    start(lab,proposal,actor='bob',status=404)
    for suffix in ('','/usage'):
        http(lab,'GET','/runs/'+run['run_id']+suffix,actor='bob',worker='b',status=404)
    http(lab,'POST','/runs/'+run['run_id']+'/resume',actor='bob',status=404,
        json={'expected_revision':run['revision'],'choice':'accept','response':{'confirmed':True}})
    assert calls(lab)==before


def test_same_operation_keys_are_independent_between_tenant_owners(lab):
    key=uuid.uuid4().hex;before=calls(lab)
    one=propose(lab,pause(),key=key);two=propose(lab,pause(),actor='carol',key=key)
    a=start(lab,one,key=key);b=start(lab,two,actor='carol',key=key)
    assert one['proposal_id']!=two['proposal_id'] and a['run_id']!=b['run_id']
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT count(DISTINCT tenant_id) FROM lab_app.runs WHERE idempotency_key=%s',(key,)).fetchone()==(2,)
    assert calls(lab)==before


def inline(*,tools=None,tier=None):
    fm={'name':'inline','description':'Synthetic inline fixture','tools':tools or []}
    if tier is not None:fm['model_tier']=tier
    return {'definition':{'version':1,'start':'one','steps':{
        'one':{'kind':'agent','agent':'inline','schema':'found','next':'done'},
        'done':{'kind':'finish','requires':['one']}}},
        'inline_agents':{'inline':{'type':'subagent','frontmatter':fm,
            'body':'ALWAYS return the request entity_id as JSON. NEVER use external data.'}}}


def test_inline_grant_never_implies_composition(lab):
    before=calls(lab)
    propose(lab,actor='carol',status=422)
    assert calls(lab)==before


def test_omitted_model_tier_uses_host_default_with_empty_explicit_allowlist(lab):
    before=calls(lab);proposal=propose(lab,inline(),actor='carol')
    assert start(lab,proposal,actor='carol')['status']=='completed'
    assert calls(lab)==before+1


def test_inline_grant_never_implies_tools(lab):
    before=calls(lab)
    # Prose requests are independently denied by current host entitlement.
    body=inline(tools=['fixture_apply'])
    propose(lab,body,actor='carol',status=403)
    # Explicit graph capability requests are denied during SDK admission.
    body['definition']['steps']['one']['tools']=['fixture_apply']
    propose(lab,body,actor='carol',status=422)
    assert calls(lab)==before


@pytest.mark.parametrize('field,value',[('operation_namespace','attacker'),('reference',{'bundleIdentity':'fake'}),
                                      ('endpoint','http://attacker.invalid'),('assets','/private')])
def test_client_registration_references_never_hydrate_host_code(lab,field,value):
    before=calls(lab);body=approved_proposal();body[field]=value
    propose(lab,body,status=422)
    assert calls(lab)==before


def test_check_failure_and_rejected_output_usage(lab):
    control(lab,scenario='native_rejected');before=calls(lab)
    run=start(lab)
    assert run['status']=='rejected' and calls(lab)==before+2
    assert http(lab,'GET','/runs/'+run['run_id']+'/usage')['total_calls']==2


def test_gate_failure_is_observable_without_running_pause(lab):
    body=approved_proposal();body['definition']['steps']['checked']['pass']='gate'
    body['definition']['steps']['gate']['equals']=False
    before=calls(lab);run=start(lab,propose(lab,body))
    assert run['status']=='rejected' and run['interaction'] is None and calls(lab)==before+2


def test_graph_revisit_rejects_stale_dependent_artifact_before_next_call(lab):
    control(lab,scenario='native_revisit')
    body=approved_proposal();steps=body['definition']['steps']
    steps['confirm']['choices']['accept']='find';steps['find']['next']='route'
    steps['route']={'kind':'gate','from':'find','field':['entity_id'],'equals':'first',
                    'pass':'review','fail':'confirm'}
    before=calls(lab);run=start(lab,propose(lab,body),entity='first')
    assert run['status']=='waiting'
    assert resume(lab,run)['status']=='blocked' and calls(lab)==before+3


def test_finish_requires_cannot_accept_missing_specialist(lab):
    body=approved_proposal();body['definition']['steps']['find']['next']='done'
    before=calls(lab);run=start(lab,propose(lab,body))
    assert run['status']=='blocked' and calls(lab)==before+1


def test_run_budget_prevents_next_provider_dispatch(lab):
    body=approved_proposal();body['definition']['limits']={'max_calls':1}
    before=calls(lab);run=start(lab,propose(lab,body))
    assert run['status']=='blocked' and calls(lab)==before+1


def test_current_revocation_prevents_resume_on_fresh_worker(lab):
    run=start(lab);before=calls(lab);settings=copy.deepcopy(lab['native'])
    revoked=copy.deepcopy(settings);revoked['tenants']['tenant-a']['schemas']=[]
    try:
        replace_worker(lab,native=revoked)
        resume(lab,run,status=403)
        assert calls(lab)==before
    finally:replace_worker(lab,native=settings)
    assert http(lab,'GET','/runs/'+run['run_id'],worker='b')==run


@pytest.mark.parametrize('field,value',[('operation_namespace','altered-namespace'),
    ('journal_identity','altered-journal'),('model_url','http://model:8000/altered'),('policies',{}),
    ('fixture_effect_version','v2')])
def test_changed_retained_binding_never_falls_back_or_dispatches(lab,field,value):
    proposal=propose(lab,pause());run=start(lab,proposal);before=calls(lab)
    settings=copy.deepcopy(lab['native']);changed=copy.deepcopy(settings)
    target=next(bundle for bundle in changed['bundles'] if 'tenant-a' in bundle['policies'])
    if field=='policies':target['policies']['tenant-a']['composition']=False
    else:target[field]=value
    try:
        replace_worker(lab,native=changed)
        http(lab,'GET','/runs/'+run['run_id'],worker='b',status=409)
        assert calls(lab)==before
    finally:replace_worker(lab,native=settings)


def test_original_proposal_replay_new_bundle_and_reordered_reference_json(lab):
    key=uuid.uuid4().hex;body=pause();original=propose(lab,body,key=key)
    with psycopg.connect(lab['migration_dsn']) as connection:
        connection.execute('UPDATE lab_app.proposals SET reference=%s WHERE proposal_id=%s',
            (Jsonb(dict(reversed(list(original['reference'].items())))),original['proposal_id']))
    settings=copy.deepcopy(lab['native']);new=copy.deepcopy(settings)
    for bundle in copy.deepcopy(new['bundles']):
        bundle['version']='synthetic-v2'
        # A label alone preserves identity. Change actual retained host material
        # to exercise replay across a different semantic bundle.
        bundle['fixture_effect_version']='v2'
        new['bundles'].append(bundle)
    for grant in new['tenants'].values():grant['bundle_version']='synthetic-v2'
    try:
        replace_worker(lab,native=new)
        assert propose(lab,body,key=key,worker='b')==original
        fresh=propose(lab,body,worker='b')
        assert fresh['reference']['bundleVersion']=='synthetic-v2'
        assert fresh['reference']['bundleIdentity']!=original['reference']['bundleIdentity']
        assert start(lab,original,worker='b')['status']=='waiting'
    finally:replace_worker(lab,native=settings)


def test_missing_retained_bundle_is_operator_condition_without_default_fallback(lab):
    proposal=propose(lab,pause());run=start(lab,proposal);before=calls(lab)
    settings=copy.deepcopy(lab['native']);changed=copy.deepcopy(settings)
    for bundle in changed['bundles']:bundle['version']='synthetic-v2'
    for grant in changed['tenants'].values():grant['bundle_version']='synthetic-v2'
    try:
        replace_worker(lab,native=changed)
        http(lab,'GET','/runs/'+run['run_id'],worker='b',status=409)
        assert calls(lab)==before
    finally:replace_worker(lab,native=settings)

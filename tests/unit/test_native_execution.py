import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


@pytest.fixture
def native(tmp_path, monkeypatch):
    from persistence_sql import database
    from prosaic_harness import FileRunStore
    from prosaic_integration_lab.native_execution import NativeExecution
    from prosaic_integration_lab.identity import Principal
    from prosaic_integration_lab.metadata import Metadata
    from prosaic_integration_lab.capacity import policy
    root = __import__('pathlib').Path(__file__).resolve().parents[2]
    config = {'assets':str(root/'assets'), 'app_dsn':'unused', 'namespace':'host-scope',
        'environment':'sandbox', 'native':{'bundles':[{'version':'synthetic-v1',
        'model_url':'http://127.0.0.1:9/v1', 'operation_namespace':'private-operation-scope',
        'policies':{'a':{'composition':True},'b':{'composition':False}}}],
        'tenants':{'a':{'bundle_version':'synthetic-v1','composition':True},
                   'b':{'bundle_version':'synthetic-v1','composition':False}}}}
    metadata = Metadata('unused')
    connect = database(tmp_path/'app.sqlite')
    monkeypatch.setattr(metadata,'connection',connect)
    host = SimpleNamespace(config=config,metadata=metadata,capacity=policy({}),
        store=FileRunStore(tmp_path/'runs'),recorder=None,
        check_scope=lambda reservation:None,fixture_event=lambda event:None,observer=None)
    result = NativeExecution(host)
    monkeypatch.setattr(result.proposals,'connection',connect)
    return result, Principal('a','alice','payer'), Principal('b','bob','other')


def text(kind='pause'):
    steps = {'done':{'kind':'finish'}}
    start = 'done'
    if kind == 'pause':
        start = 'ask'
        steps['ask'] = {'kind':'pause','question':'Accept synthetic output?',
            'choices':{'accept':'done','reject':'done'},'response_schema':'decision'}
    return json.dumps({'definition':{'version':1,'start':start,'steps':steps}})


def test_catalogue_is_projected_and_contains_no_private_host_values(native):
    execution,a,b = native
    one,two = execution.catalogue(a),execution.catalogue(b)
    assert one['bundle_version'] == 'synthetic-v1'
    assert one['manifest'] != two['manifest']
    encoded = json.dumps(one)
    assert 'private-operation-scope' not in encoded and '127.0.0.1' not in encoded


def test_proposal_replay_precedes_changed_policy_and_new_bundle(native):
    execution,a,_ = native
    first = execution.propose(a,'key',text())
    execution.host.config['native']['tenants']['a']['schemas'] = []
    assert execution.propose(a,'key',text()) == first
    with pytest.raises(HTTPException) as error:
        execution.start_request(a,'run',first['proposal_id'],{})
    assert error.value.status_code == 403


@pytest.mark.parametrize('inputs',[float('inf'), {'x':float('nan')}, 'x'*8193],ids=['infinity','nan','bytes'])
def test_invalid_input_allocates_no_run_or_harness_state(native,inputs):
    execution,a,_ = native
    proposal = execution.propose(a,'key',text())
    with pytest.raises(ValueError): execution.start_request(a,'bad',proposal['proposal_id'],inputs)
    with execution.host.metadata.connection() as connection:
        assert connection.execute('SELECT count(*) AS count FROM lab_app.runs').fetchone()['count'] == 0
    assert not list(execution.host.store.root.glob('*'))


def test_native_owner_resume_validation_revision_and_revocation(native):
    execution,a,b = native
    proposal = execution.propose(a,'key',text())
    with pytest.raises(HTTPException) as error: execution.start_request(b,'run',proposal['proposal_id'],{})
    assert error.value.status_code == 404
    run = execution.start_request(a,'run',proposal['proposal_id'],{'private':'PRIVATE_INPUT'})
    reservation = execution.host.metadata.owned(a,run['run_id'])
    assert run['interaction']['choices'] == ['accept','reject']
    assert 'PRIVATE_INPUT' not in json.dumps(run)
    from prosaic_harness import HumanResponseError, RevisionConflict
    with pytest.raises(HumanResponseError): execution.resume(reservation,run['revision'],'accept',{'confirmed':'bad'},False)
    assert execution.status(reservation) == run
    with pytest.raises(RevisionConflict): execution.resume(reservation,'a'*64,'accept',{'confirmed':True},False)
    assert execution.status(reservation) == run
    execution.host.config['native']['tenants']['a']['schemas'] = []
    with pytest.raises(HTTPException) as error: execution.resume(reservation,run['revision'],'accept',{'confirmed':True},False)
    assert error.value.status_code == 403
    execution.host.config['native']['tenants']['a']['schemas'] = ['found','reviewed','decision']
    assert execution.resume(reservation,run['revision'],'accept',{'confirmed':True},False)['status'] == 'completed'


def test_uncertain_start_never_redispatches_and_retained_bundle_is_required(native):
    execution,a,_ = native
    proposal = execution.propose(a,'key',text('finish'))
    row = execution.proposals.owned(a,proposal['proposal_id'])
    reservation = execution.host.metadata.reserve_native(a,'run',row,{},namespace='host-scope',environment='sandbox')
    execution.host.metadata.claim_start(reservation['run_id'])
    assert execution.start_request(a,'run',proposal['proposal_id'],{})['status'] == 'start_uncertain'
    assert not list(execution.host.store.root.glob('*'))
    execution.registry._bundles.clear()
    with pytest.raises(HTTPException) as error: execution.status(reservation)
    assert error.value.status_code == 409


def test_catalogue_changes_with_current_revocation_without_mutating_retained_bundle(native):
    execution,a,_ = native
    first = execution.catalogue(a)
    execution.host.config['native']['tenants']['a']['agents'] = []
    current = execution.catalogue(a)
    assert current['manifest']['agents'] == {}
    assert first['manifest']['agents']


def test_committed_pause_observer_revision_and_noncritical_failure(native):
    execution,a,_ = native
    records = []
    def observe(record):
        records.append(record)
        raise RuntimeError('PRIVATE_MONITORING_FAILURE')
    execution.host.observer = observe
    proposal = execution.propose(a,'key',text())
    run = execution.start_request(a,'run',proposal['proposal_id'],{})
    committed = [record for record in records if record['event']=='waiting_committed']
    assert len(committed) == 1 and committed[0]['revision'] == run['revision']
    assert 'PRIVATE_MONITORING_FAILURE' not in str(run)


@pytest.mark.parametrize('tier,configured,allowed,success',[
    (None,False,False,True),('fast',True,True,True),
    ('fast',False,True,False),('fast',True,False,False)],
    ids=['host-default','explicit-granted','unconfigured','ungranted'])
def test_inline_independent_grant_and_configured_explicit_tiers(native,tier,configured,allowed,success):
    from prosaic_harness import WorkflowAdmissionError
    from prosaic_integration_lab.native_execution import NativeExecution
    execution,a,_ = native
    config = execution.host.config['native']
    definition = config['bundles'][0]
    definition['routes'] = {'fast':'fixture'} if configured else {}
    setting = {'composition':False,'inline':True,'model_tiers':['fast'] if allowed else []}
    definition['policies']['a'] = setting
    config['tenants']['a'] = {'bundle_version':'synthetic-v1',**setting}
    current = NativeExecution(execution.host)
    current.proposals.connection = execution.proposals.connection
    frontmatter = {'name':'inline','description':'Synthetic inline','tools':[]}
    if tier is not None: frontmatter['model_tier'] = tier
    body = {'definition':{'version':1,'start':'one','steps':{'one':{
        'kind':'agent','agent':'inline','schema':'found','next':'done'},'done':{'kind':'finish'}}},
        'inline_agents':{'inline':{'type':'subagent','frontmatter':frontmatter,
            'body':'ALWAYS return synthetic JSON. NEVER access product data.'}}}
    if success:
        assert current.propose(a,'tier',json.dumps(body))['proposal_id']
    else:
        with pytest.raises(WorkflowAdmissionError): current.propose(a,'tier',json.dumps(body))


def test_input_snapshot_and_reservation_attribution_survive_replay(native):
    execution,a,_ = native
    proposal = execution.propose(a,'key',text())
    original = {'nested':[{'text':'original'}]}
    run = execution.start_request(a,'run',proposal['proposal_id'],original)
    original['nested'][0]['text']='caller-mutation'
    from prosaic_integration_lab.identity import Principal
    replay = execution.start_request(Principal('a','alice','changed-payer'),'run',proposal['proposal_id'],
        {'nested':[{'text':'original'}]})
    assert replay == run
    row = execution.host.metadata.owned(a,run['run_id'])
    assert row['billing_account_id']=='payer' and row['namespace']=='host-scope'
    assert row['request']['inputs']=={'nested':[{'text':'original'}]}


def test_single_verified_waiting_interaction_snapshot(native,monkeypatch):
    from prosaic_harness import Harness
    execution,a,_ = native
    proposal = execution.propose(a,'key',text())
    run = execution.start_request(a,'run',proposal['proposal_id'],{})
    counts={'interaction':0,'status':0}
    interaction,status=Harness.interaction,Harness.status
    def observed_interaction(self,**kwargs):
        counts['interaction']+=1
        return interaction(self,**kwargs)
    def observed_status(self):
        counts['status']+=1
        return status(self)
    monkeypatch.setattr(Harness,'interaction',observed_interaction)
    monkeypatch.setattr(Harness,'status',observed_status)
    assert execution.status(execution.host.metadata.owned(a,run['run_id'])) == run
    assert counts=={'interaction':1,'status':1}


def test_fresh_worker_reconstructs_original_assets_and_bindings_after_upgrade(native,tmp_path):
    from prosaic_integration_lab.native_execution import NativeExecution
    import shutil
    execution,a,_ = native
    proposal = execution.propose(a,'key',text())
    config = execution.host.config['native']
    old = config['bundles'][0]
    original_directory = tmp_path/'retained'
    shutil.copytree(__import__('pathlib').Path(execution.host.config['assets'])/'native',original_directory)
    old['assets'] = str(original_directory)
    new_directory = tmp_path/'current'
    shutil.copytree(original_directory,new_directory)
    (new_directory/'agents/finder.md').write_text('ALWAYS return the new synthetic fixture. NEVER access product data.')
    newer = {**old,'version':'synthetic-v2','assets':str(new_directory),
        'model_url':'http://127.0.0.1:19/v1','operation_namespace':'new-operation-scope'}
    config['bundles'].append(newer)
    config['tenants']['a']['bundle_version'] = 'synthetic-v2'
    fresh = NativeExecution(execution.host)
    fresh.proposals.connection = execution.proposals.connection
    assert fresh.propose(a,'key',text()) == proposal
    run = fresh.start_request(a,'run',proposal['proposal_id'],{})
    assert run['status']=='waiting'
    row = execution.host.metadata.owned(a,run['run_id'])
    assert row['assets_hash'] == proposal['reference']['bundleIdentity']


def test_native_execution_checks_frozen_scope_before_sdk_access(native,monkeypatch):
    from prosaic_integration_lab.execution import Execution
    execution,a,_ = native
    proposal = execution.propose(a,'key',text())
    run = execution.start_request(a,'run',proposal['proposal_id'],{})
    row = execution.host.metadata.owned(a,run['run_id'])
    execution.host.check_scope = lambda reservation:Execution.check_scope(execution.host,reservation)
    execution.host.config['namespace']='different'
    def forbidden(*args,**kwargs): raise AssertionError('SDK queried after scope drift')
    monkeypatch.setattr(execution.host.store,'load_run',forbidden)
    with pytest.raises(HTTPException) as error: execution.status(row)
    assert error.value.status_code==409 and error.value.detail=='scope_conflict'


def test_current_permission_expansion_does_not_expand_retained_catalogue_or_schema(native):
    from prosaic_harness import WorkflowAdmissionError
    from prosaic_integration_lab.native_execution import approved_proposal
    execution,_,b=native
    setting=execution.host.config['native']['tenants']['b']
    setting.update(composition=True,inline=True)
    view=execution.catalogue(b)
    assert view['manifest']['allowAgentComposition'] is False
    assert view['manifest']['allowInlineAgents'] is False
    assert view['proposal_schema']['properties']['inline_agents']['maxProperties']==0
    with pytest.raises(WorkflowAdmissionError) as error:
        execution.propose(b,'expanded',json.dumps(approved_proposal()))
    assert error.value.code=='policy_denied'
    with execution.proposals.connection() as connection:
        assert connection.execute('SELECT count(*) AS count FROM lab_app.proposals').fetchone()['count']==0


def test_alias_and_tier_expansions_intersect_frozen_host_grants(native):
    from prosaic_integration_lab.native_execution import NativeExecution
    from prosaic_harness import WorkflowAdmissionError
    execution,_,b=native
    definition=execution.host.config['native']['bundles'][0]
    definition['routes']={'fast':'fixture'}
    definition['policies']['b']={'composition':True,'inline':True,'agents':['finder'],
        'schemas':['found'],'validators':[],'model_tiers':[]}
    execution.host.config['native']['tenants']['b'].update(composition=True,inline=True,
        agents=['finder','reviewer'],schemas=['found','reviewed','decision'],
        validators=['approved'],model_tiers=['fast'])
    fresh=NativeExecution(execution.host)
    fresh.proposals.connection=execution.proposals.connection
    view=fresh.catalogue(b)
    assert set(view['manifest']['agents'])=={'finder'}
    assert set(view['manifest']['schemas'])=={'found'}
    assert view['manifest']['validators']=={} and view['manifest']['modelTiers']==[]
    inline_schema=view['proposal_schema']['properties']['inline_agents']
    assert inline_schema['additionalProperties']['properties']['frontmatter']['properties']['model_tier'] is False
    step_schemas=view['proposal_schema']['properties']['definition']['properties']['steps']['additionalProperties']['oneOf']
    agent_schema=next(branch for branch in step_schemas if branch['properties']['kind']['const']=='agent')
    check_schema=next(branch for branch in step_schemas if branch['properties']['kind']['const']=='check')
    assert agent_schema['properties']['schema']['enum']==['found']
    assert check_schema['properties']['validators']['items'] is False
    body={'definition':{'version':1,'start':'review','steps':{
        'review':{'kind':'agent','agent':'reviewer','schema':'found','next':'done'},'done':{'kind':'finish'}}}}
    with pytest.raises(WorkflowAdmissionError): fresh.propose(b,'alias-expansion',json.dumps(body))


def test_catalogue_uses_registered_material_snapshot_without_file_reads(native,tmp_path):
    import shutil
    from pathlib import Path
    from prosaic_integration_lab.native_execution import NativeExecution
    execution,a,_=native
    directory=tmp_path/'native'
    shutil.copytree(Path(execution.host.config['assets'])/'native',directory)
    execution.host.config['native']['bundles'][0]['assets']=str(directory)
    fresh=NativeExecution(execution.host)
    before=fresh.catalogue(a)
    (directory/'schemas/found.json').write_text('invalid post-registration physical schema')
    (directory/'agents/finder.md').unlink()
    assert fresh.catalogue(a)==before


def test_frozen_projection_grants_do_not_alias_mutable_config(native):
    execution,_,b=native
    original=execution.catalogue(b)
    execution.host.config['native']['bundles'][0]['policies']['b']['composition']=True
    execution.host.config['native']['tenants']['b']['composition']=True
    assert execution.catalogue(b)['manifest']['allowAgentComposition'] is False
    execution.host.config['native']['bundles'][0]['policies']['b']['agents']=[]
    assert execution.catalogue(b)['manifest']['agents']==original['manifest']['agents']


def test_restrictive_current_grants_project_and_deny_then_new_registered_bundle_expands(native):
    from prosaic_integration_lab.native_execution import NativeExecution,approved_proposal
    from prosaic_harness import WorkflowAdmissionError
    execution,a,b=native
    saved=execution.propose(a,'original',text())
    execution.host.config['native']['tenants']['a'].update(composition=False,agents=['finder'],
        schemas=['found'],validators=[])
    reduced=execution.catalogue(a)['manifest']
    assert reduced['allowAgentComposition'] is False and set(reduced['agents'])=={'finder'}
    assert set(reduced['schemas'])=={'found'} and reduced['validators']=={}
    with pytest.raises(HTTPException) as error: execution.propose(a,'reduced',json.dumps(approved_proposal()))
    assert error.value.status_code==403
    positive={'definition':{'version':1,'start':'one','steps':{
        'one':{'kind':'agent','agent':'finder','schema':'found','next':'done'},'done':{'kind':'finish'}}}}
    assert execution.propose(a,'still-granted',json.dumps(positive))['proposal_id']
    definition=execution.host.config['native']['bundles'][0]
    newer=json.loads(json.dumps(definition))
    newer['version']='synthetic-v2'
    newer['policies']['b']={'composition':True,'inline':True}
    execution.host.config['native']['bundles'].append(newer)
    execution.host.config['native']['tenants']['b'].update(bundle_version='synthetic-v2',composition=True,inline=True)
    execution.host.config['native']['tenants']['a'].update(bundle_version='synthetic-v2')
    fresh=NativeExecution(execution.host)
    fresh.proposals.connection=execution.proposals.connection
    assert fresh.catalogue(b)['manifest']['allowAgentComposition'] is True
    expanded=fresh.propose(b,'new-bundle',json.dumps(approved_proposal()))
    assert expanded['reference']['bundleVersion']=='synthetic-v2'
    assert fresh.propose(a,'original',text())==saved

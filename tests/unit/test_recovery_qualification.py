"""Missing measurements cannot be mistaken for zero-loss restoration."""
import pytest
import hashlib
import json

def identity():
    from test_qualification import profile
    return {'suite':'synthetic-capacity-v1','profile_sha256':hashlib.sha256(json.dumps(profile(),sort_keys=True,
        separators=(',',':'),ensure_ascii=False).encode()).hexdigest()}

def test_recovery_requires_owned_stack_before_any_effect():
    from lab_runner.recovery_qualification import run
    from test_qualification import profile
    with pytest.raises(ValueError):run(object(),profile())

@pytest.mark.parametrize('patch',[{'acknowledged':[]},{'restored':[]},{'ready_at':None},{'calls_after':3},
    {'restored':[999]}])
def test_missing_or_redispatched_restore_evidence_fails(patch):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10}],restored=[1],loss_at=11,ready_at=12,
        calls_before=2,calls_after=2,owner_verified=True,revision_verified=True,
        receipt_verified=True,unknown_usage_verified=True)
    evidence.update(patch)
    evidence.update(identity())
    assert evaluate(profile(),evidence)['qualification']=='not_qualified'

def test_observed_missing_marker_rpo_is_measured():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=dict(acknowledged=[{'sequence':1,'time':10},{'sequence':2,'time':15}],restored=[1],
        loss_at=16,ready_at=20,calls_before=2,calls_after=2,owner_verified=True,
        revision_verified=True,receipt_verified=True,unknown_usage_verified=True)
    evidence.update(identity())
    result=evaluate(profile(),evidence)
    assert result['observed_rpo_s']==5 and result['observed_rto_s']==4
    assert result['qualification']=='not_qualified'

def test_restore_identity_mismatch_cannot_qualify():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    assert evaluate(profile(),{'suite':'other-suite'})['reason']=='evidence_identity_mismatch'


def native_evidence():
    return {**identity(), 'acknowledged':[{'sequence':1,'time':10},{'sequence':2,'time':11}],
        'restored':[1,2], 'loss_at':12, 'ready_at':13, 'calls_before':8,'calls_after':8,
        'owner_verified':True,'revision_verified':True,'receipt_verified':True,'unknown_usage_verified':True,
        'native_mode':True,'native_runs':4,'native_proposals':3,'native_verified':True,
        'proposal_verified':True,'reference_verified':True,'bundle_verified':True,
        'reservation_verified':True,'snapshot_verified':True,'receipt_document_verified':True,
        'interaction_verified':True,'native_usage_verified':True,'journal_verified':True,
        'domain_verified':True,'completed_claim_verified':True,'uncertain_claim_verified':True,
        'handlers_before':2,'handlers_after':2}


@pytest.mark.parametrize('marker',['missing',False,0,1,None,'native'])
@pytest.mark.parametrize('damaged_field',[None,'snapshot_verified'])
def test_trusted_native_mode_cannot_be_downgraded_by_submitted_marker(marker,damaged_field):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=native_evidence()
    if marker=='missing':evidence.pop('native_mode')
    else:evidence['native_mode']=marker
    if damaged_field:evidence[damaged_field]=False
    result=evaluate(profile(),evidence,native_mode=True)
    assert result['qualification']=='not_qualified' and result['fixture_passed'] is False


@pytest.mark.parametrize('marker',['missing',False,0,1,None,'native',True])
def test_legacy_evaluation_rejects_unexpected_native_contract_even_with_changed_marker(marker):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=native_evidence()
    if marker=='missing':evidence.pop('native_mode')
    else:evidence['native_mode']=marker
    assert evaluate(profile(),evidence)['qualification']=='not_qualified'


def test_matching_legacy_restore_qualifies_without_native_contract():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence={**identity(),'acknowledged':[{'sequence':1,'time':10},{'sequence':2,'time':11}],
        'restored':[1,2],'loss_at':12,'ready_at':13,'calls_before':2,'calls_after':2,
        'owner_verified':True,'revision_verified':True,'receipt_verified':True,'unknown_usage_verified':True}
    result=evaluate(profile(),evidence)
    assert result['qualification']=='qualified' and result['fixture_passed'] is True


@pytest.mark.parametrize('field',['native_verified','proposal_verified','reference_verified','bundle_verified',
    'reservation_verified','snapshot_verified','receipt_document_verified','interaction_verified',
    'native_usage_verified','journal_verified','domain_verified','completed_claim_verified',
    'uncertain_claim_verified'])
@pytest.mark.parametrize('value',[False,None,1])
def test_native_restore_missing_false_or_non_boolean_contract_evidence_fails(field,value):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=native_evidence();evidence[field]=value
    result=evaluate(profile(),evidence,native_mode=True)
    assert result['qualification']=='not_qualified'


@pytest.mark.parametrize('patch',[{'native_runs':0},{'native_runs':True},{'native_proposals':2},
    {'handlers_after':3},{'handlers_before':None},{'handlers_before':True,'handlers_after':True},
    {'handlers_after':2.0},{'calls_after':8.0}])
def test_native_restore_requires_populated_counts_and_unchanged_handler_counter(patch):
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=native_evidence();evidence.update(patch)
    result=evaluate(profile(),evidence,native_mode=True)
    assert result['qualification']=='not_qualified'


def test_native_restore_returns_only_fixed_verification_fields():
    from lab_runner.recovery_qualification import evaluate
    from test_qualification import profile
    evidence=native_evidence();evidence['snapshots']={'private':'do not export'}
    result=evaluate(profile(),evidence,native_mode=True)
    assert result['qualification']=='qualified' and result['native_verified'] is True
    assert result['native_runs']==4 and result['native_proposals']==3
    assert result['redispatch_detected'] is False and result['logical_restore_only'] is True
    assert 'snapshots' not in result and 'private' not in json.dumps(result)


@pytest.mark.parametrize('calls,records',[(7,100),(8,5)])
def test_native_restore_budget_preflight_happens_before_database_or_provider_mutation(monkeypatch,calls,records):
    from lab_runner import recovery_qualification as recovery
    from lab_runner.stack import OwnedStack
    from test_qualification import profile
    stack=object.__new__(OwnedStack);stack.native_fixture=True
    monkeypatch.setattr(OwnedStack,'verify_owned',lambda self:True)
    settings=profile();settings.update(maximum_calls=calls,maximum_records=records)
    with pytest.raises(ValueError,match='eight bounded calls/six records'):
        recovery.run(stack,settings)


@pytest.mark.parametrize('field',['proposals','reservations','native_runs','snapshots','receipts','views','usage','journal','domain'])
def test_native_verifier_detects_changed_restored_contract_without_dispatch(monkeypatch,field,prepared_v1):
    import copy
    import httpx
    from lab_runner import native_restore
    original=populated_capture(prepared_v1)
    restored=copy.deepcopy(original);restored[field]=[]
    fixture={'capture':original,'run_ids':['a','b','c','d'],'proposal_ids':['p','q','r'],
        'calls_before':8,'handlers_before':2}
    monkeypatch.setattr(native_restore,'capture',lambda *args:restored)
    def service(request):
        if request.url.path=='/stats':return httpx.Response(200,json={'calls':8,'barriers':{'tool-handler':2}})
        assert request.method=='GET'
        return httpx.Response(404,json={})
    with httpx.Client(transport=httpx.MockTransport(service)) as client:
        result=native_restore.verify({'b':'http://fixture','model':'http://model','principals':{'owner':{},'other':{}}},fixture,client)
    assert result['native_verified'] is False


def test_native_capture_rejects_empty_native_snapshot_even_when_dump_matches(monkeypatch):
    from lab_runner import native_restore
    with pytest.raises(ValueError,match='populated native restore evidence'):
        native_restore.validate_capture({'proposals':[],'reservations':[],'native_runs':[],
            'snapshots':[],'receipts':[],'views':[],'usage':[],'journal':[],'domain':[]},
            ['a','b','c','d'],['p','q','r'])


def populated_capture(prepared):
    run_ids=['a','b','c','d'];proposal_ids=['p','q','r']
    reference=prepared.reference.to_dict();document='{"synthetic":"snapshot"}'
    proposals=[{'proposal_id':p,'tenant_id':'tenant','actor_id':'actor','proposal_json':prepared.proposal_json,
        'bundle_identity':reference['bundleIdentity'],'bundle_version':reference['bundleVersion'],
        'policy_digest':reference['bundleIdentity'],'workflow_fingerprint':reference['workflowFingerprint'],
        'request_digest':reference['proposalSha256'],'reference':reference} for p in proposal_ids]
    reservations=[{'run_id':r,'workflow':'native','namespace':'native','environment':'sandbox','billing_account_id':'account',
        'tenant_id':'tenant','actor_id':'actor','assets_hash':reference['bundleIdentity'],
        'request':{'proposal_id':p,'inputs':{'entity_id':r}}} for r,p in zip(run_ids,['p','q','r','r'])]
    links=[{'run_id':r,'proposal_id':p,'tenant_id':'tenant','actor_id':'actor'} for r,p in zip(run_ids,['p','q','r','r'])]
    return {'proposals':proposals,'reservations':reservations,'native_runs':links,
        'snapshots':[{'run_id':r,'revision':1,'document':document} for r in run_ids],
        'receipts':[{'run_id':r,'document':document,'sha256':hashlib.sha256(document.encode()).hexdigest()} for r in ['a','a','b','c']],
        'views':[{'run_id':r} for r in run_ids],'usage':[{} for _ in run_ids],
        'journal':[{'operation_namespace':'native','operation_key':r,'signature':'a'*64,
            'claim_token':'original-token','state':state,'outcome':outcome} for r,state,outcome in
                [('c','completed',{'status':'ok','result':{'applied':True}}),('d','uncertain',None)]],
        'domain':[{'namespace':'native','business_key':r,'amount':1} for r in ['c','d']]}


def test_native_capture_accepts_actual_public_reference_without_private_policy_field(prepared_v1):
    from lab_runner.native_restore import validate_capture
    assert 'policyDigest' not in prepared_v1.reference.to_dict()
    validate_capture(populated_capture(prepared_v1),['a','b','c','d'],['p','q','r'])


@pytest.mark.parametrize('state,outcome',[('uncertain',{'status':'ok','result':{}}),('completed',None)])
def test_native_capture_requires_committed_or_uncertain_outcome_contract(prepared_v1,state,outcome):
    from lab_runner.native_restore import validate_capture
    captured=populated_capture(prepared_v1)
    next(row for row in captured['journal'] if row['state']==state)['outcome']=outcome
    with pytest.raises(ValueError,match='populated native restore evidence'):
        validate_capture(captured,['a','b','c','d'],['p','q','r'])


def test_native_verifier_uses_public_journal_replay_and_uncertain_claim_without_permission(monkeypatch,prepared_v1):
    import copy
    import httpx
    from types import SimpleNamespace
    from lab_runner import native_restore
    from prosaic_integration_lab.tool_journal import PgToolJournal
    original=populated_capture(prepared_v1);restored=copy.deepcopy(original)
    monkeypatch.setattr(native_restore,'capture',lambda *args:copy.deepcopy(restored))
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query,parameters):
            if query.lstrip().startswith('INSERT'):return SimpleNamespace(fetchone=lambda:None)
            namespace,key=parameters
            row=next(row for row in restored['journal'] if row['operation_namespace']==namespace and row['operation_key']==key)
            return SimpleNamespace(fetchone=lambda:copy.deepcopy(row))
    monkeypatch.setattr(PgToolJournal,'connection',lambda self:Connection())
    fixture={'capture':original,'run_ids':['a','b','c','d'],'proposal_ids':['p','q','r'],
        'calls_before':8,'handlers_before':2}
    def service(request):
        assert request.method=='GET'
        if request.url.path=='/stats':return httpx.Response(200,json={'calls':8,'barriers':{'tool-handler':2}})
        return httpx.Response(404,json={})
    with httpx.Client(transport=httpx.MockTransport(service)) as client:
        result=native_restore.verify({'b':'http://fixture','model':'http://model','app_dsn':'dbname=fixture',
            'principals':{'owner':{},'other':{}}},fixture,client)
    assert result['native_verified'] is True
    assert result['completed_claim_verified'] is True and result['uncertain_claim_verified'] is True
    assert restored==original
    assert all(value is True for field,value in result.items() if field.endswith('_verified'))

@pytest.mark.parametrize('restore_fails',[False,True])
def test_restore_refreshes_owned_port_through_readiness_and_final_restart(tmp_path,monkeypatch,restore_fails):
    """Engine restart may reassign the same verified container's published port."""
    import httpx
    from types import SimpleNamespace
    from lab_runner import recovery_qualification as recovery
    from lab_runner.stack import OwnedStack
    from test_qualification import profile
    stack=object.__new__(OwnedStack)
    stack.directory=tmp_path;stack.secrets=tmp_path;stack.owner='a'*32;stack.engine='fixture-engine'
    stack.manifest={'owner':stack.owner,'database_id':'db','replica_ids':{'b':'replica-b'},
        'runtime_config_job':'delivery','endpoints':{'a':'http://127.0.0.1:1001',
        'b':'http://127.0.0.1:1002','model':'http://127.0.0.1:1003'}}
    config={'migration_dsn':'dbname=lab','principals':{'owner':{},'other':{}},
        'harness_dsn':'dbname=lab','accounting_dsn':'dbname=lab','app_dsn':'dbname=lab'}
    (tmp_path/'host.json').write_text(json.dumps(config));(tmp_path/'service.json').write_text(json.dumps(config))
    monkeypatch.setattr(OwnedStack,'verify_owned',lambda self:True)
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def execute(self,query,*args):
            if 'SELECT count' in query:return SimpleNamespace(fetchone=lambda:(0,))
            if 'SELECT sequence' in query:return [(1,10.0),(2,11.0)]
    monkeypatch.setattr(recovery.psycopg,'connect',lambda *a,**k:Connection())
    def subprocess_run(arguments,**kwargs):
        return SimpleNamespace(returncode=int(restore_fails and 'pg_restore' in arguments),stdout=b'fixture dump')
    monkeypatch.setattr(recovery.subprocess,'run',subprocess_run)
    clock={'value':0};port={'value':1002}
    def monotonic():clock['value']+=.1;return clock['value']
    monkeypatch.setattr(recovery,'time',SimpleNamespace(monotonic=monotonic,time=lambda:10,sleep=lambda _:None))
    def command(engine,*args):
        if args==('start','replica-b'):port['value']+=1000
        return json.dumps([{'Id':'replica-b','Config':{'Labels':{'io.prosaic.lab.owner':stack.owner}},
            'NetworkSettings':{'Ports':{'8080/tcp':[{'HostIp':'127.0.0.1','HostPort':str(port['value'])}]}}}])
    monkeypatch.setattr(recovery,'command',command)
    seen=[];states=[]
    def service(request):
        seen.append(str(request.url));path=request.url.path
        if path=='/control':return httpx.Response(200,json={})
        if path=='/stats':return httpx.Response(200,json={'calls':2})
        if path=='/runs':
            state={'status':'waiting','run_id':str(len(states)),'revision':'v1','review':{},'choices':['approve']}
            if states:
                state.update(status='blocked',recovery_status='usage_reconciliation_required',review=None,choices=[])
            states.append(state);return httpx.Response(200,json=state)
        if request.url.port!=2002:raise httpx.ConnectError('closed previous ephemeral port',request=request)
        if path=='/readyz':return httpx.Response(200,json={})
        if request.headers.get('Authorization')=='Bearer other':return httpx.Response(404,json={})
        if path.endswith('/usage'):return httpx.Response(200,json={'unresolved_calls':1,'fully_costed':False})
        return httpx.Response(200,json=states[int(path.split('/')[2])])
    real_client=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:real_client(transport=httpx.MockTransport(service),**kwargs))
    if restore_fails:
        with pytest.raises(ValueError,match='logical restore failed'):recovery.run(stack,profile())
        assert stack.manifest['endpoints']['b']=='http://127.0.0.1:2002'
        assert json.loads((tmp_path/'service.json').read_text())==config
        return
    result=recovery.run(stack,profile())
    assert result['qualification']=='qualified' and result['observed_rto_s']>0
    assert 'http://127.0.0.1:2002/readyz' in seen
    assert not any(':1002/' in url for url in seen)
    assert stack.manifest['endpoints']['b']=='http://127.0.0.1:3002'
    assert json.loads((tmp_path/'ownership.json').read_text())['endpoints']['b']=='http://127.0.0.1:3002'

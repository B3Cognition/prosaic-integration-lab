import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def native_client(tmp_path,monkeypatch):
    from prosaic_harness import FileRunStore
    from prosaic_integration_lab import app as service
    from prosaic_integration_lab.execution import Execution
    from prosaic_integration_lab.metadata import Metadata
    from prosaic_integration_lab.native_execution import NativeExecution
    from prosaic_integration_lab.capacity import policy
    import importlib.util
    spec = importlib.util.spec_from_file_location('native_sql',Path(__file__).parents[1]/'unit/persistence_sql.py')
    sql = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sql)
    settings = {'composition':True,'review_outputs':True,'response_schema':True}
    config = {'assets':str(Path(__file__).resolve().parents[2]/'assets'),'app_dsn':'unused',
        'namespace':'host-scope','environment':'sandbox','native':{
        'bundles':[{'version':'synthetic-v1','model_url':'http://127.0.0.1:9/v1',
            'operation_namespace':'PRIVATE_HOST_NAMESPACE','journal_identity':'PRIVATE_JOURNAL_ID',
            'policies':{'a':settings,'b':{'composition':False}}}],
        'tenants':{'a':{'bundle_version':'synthetic-v1',**settings},
            'b':{'bundle_version':'synthetic-v1','composition':False}}},
        'principals':{'tenant-a-token':{'tenant_id':'a','actor_id':'alice','billing_account_id':'payer'},
            'tenant-b-token':{'tenant_id':'b','actor_id':'bob','billing_account_id':'other'},
            'stranger-token':{'tenant_id':'a','actor_id':'stranger','billing_account_id':'payer'}}}
    counters = {'reservations':0,'models':0,'validators':0,'store':0}
    from prosaic_integration_lab import native_execution as native_module
    check = native_module.approved
    def observed_check(output,context):
        counters['validators'] += 1
        return check(output,context)
    monkeypatch.setattr(native_module,'approved',observed_check)
    connect = sql.database(tmp_path/'app.sqlite')
    metadata = Metadata('unused')
    monkeypatch.setattr(metadata,'connection',connect)
    host = SimpleNamespace(config=config,metadata=metadata,capacity=policy({}),
        store=FileRunStore(tmp_path/'runs'),recorder=None,check_scope=lambda reservation:None,
        observer=None,fixture_event=lambda event:None)
    native = NativeExecution(host)
    monkeypatch.setattr(native.proposals,'connection',connect)
    reserve = metadata.reserve_native
    def observed_reserve(*args,**kwargs):
        counters['reservations'] += 1
        return reserve(*args,**kwargs)
    monkeypatch.setattr(metadata,'reserve_native',observed_reserve)
    class Consumer(Execution):
        def __init__(self,*args,**kwargs): self.__dict__.update(vars(host)); self.native=native
        def ready(self): pass
        def close(self): pass
        async def admitted(self,function,*args): return function(*args)
        async def inspected(self,function,*args): return function(*args)
        def read(self,function,*args): return function(*args)
    monkeypatch.setattr(service,'Execution',Consumer)
    monkeypatch.setattr(service,'load_config',lambda:config)
    with TestClient(service.create_app()) as client:
        yield client,native,counters


HEADERS = {'Authorization':'Bearer tenant-a-token','Idempotency-Key':'proposal','Content-Type':'application/json'}


def proposal(client):
    from prosaic_integration_lab.native_execution import approved_proposal
    response = client.post('/workflow-proposals',json=approved_proposal(),headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def test_catalogue_proposal_are_pure_and_owner_replays_original(native_client,monkeypatch):
    client,native,counters = native_client
    def forbidden(*args,**kwargs): raise AssertionError('execution during admission')
    monkeypatch.setattr(native.host.store,'load_run',forbidden)
    monkeypatch.setattr(native.host.store,'create_run',forbidden)
    import urllib.request
    monkeypatch.setattr(urllib.request.OpenerDirector,'open',forbidden)
    one = client.get('/workflow-catalogue',headers=HEADERS)
    two = client.get('/workflow-catalogue',headers={'Authorization':'Bearer tenant-b-token'})
    assert one.status_code == two.status_code == 200 and one.json() != two.json()
    assert 'PRIVATE_HOST_NAMESPACE' not in one.text and 'PRIVATE_JOURNAL_ID' not in one.text
    saved = proposal(client)
    native.host.config['native']['tenants']['a']['composition'] = False
    assert proposal(client) == saved
    assert counters == {'reservations':0,'models':0,'validators':0,'store':0}


@pytest.mark.parametrize('body',[
    '{"definition":{},"endpoint":"PRIVATE_ENDPOINT"}',
    '{"definition":{"version":1,"start":"bad","steps":{}}}',
    '{"definition":{},"tenant_id":"a"}',
    '{"definition":{},"definition":{}}',
    '{"definition":NaN}'])
def test_invalid_graph_privilege_envelope_has_zero_writes(native_client,body):
    client,native,counters = native_client
    response = client.post('/workflow-proposals',content=body,headers=HEADERS)
    assert response.status_code == 422
    assert 'PRIVATE_ENDPOINT' not in response.text
    with native.proposals.connection() as connection:
        assert connection.execute('SELECT count(*) AS count FROM lab_app.proposals').fetchone()['count'] == 0
    assert counters['reservations'] == counters['models'] == counters['validators'] == 0


@pytest.mark.parametrize('inputs',['{"x":Infinity}','"'+ 'x'*8100 +'"'],ids=['infinity','finite-bytes'])
def test_invalid_inputs_allocate_no_run(native_client,inputs):
    client,native,counters = native_client
    saved = proposal(client)
    response = client.post('/native-runs',content='{"proposal_id":"'+saved['proposal_id']+'","inputs":'+inputs+'}',
        headers={**HEADERS,'Idempotency-Key':'bad-input'})
    assert response.status_code == 422, response.text
    assert counters['reservations'] == counters['models'] == counters['validators'] == 0


def test_owner_invalid_response_stale_revision_and_revocation(native_client):
    client,native,counters = native_client
    body = {'definition':{'version':1,'start':'ask','steps':{
        'ask':{'kind':'pause','question':'Accept synthetic output?','choices':{'accept':'done'},'response_schema':'decision'},
        'done':{'kind':'finish'}}}}
    saved = client.post('/workflow-proposals',json=body,headers=HEADERS).json()
    started = client.post('/native-runs',json={'proposal_id':saved['proposal_id'],'inputs':{'private':'PRIVATE_INPUT'}},
        headers={**HEADERS,'Idempotency-Key':'run'})
    assert started.status_code == 200, started.text
    run = started.json()
    route = '/runs/'+run['run_id']
    assert run['interaction']['responseSchema']['additionalProperties'] is False
    assert 'PRIVATE_INPUT' not in started.text
    assert client.get(route,headers={'Authorization':'Bearer stranger-token'}).status_code == 404
    invalid = client.post(route+'/resume',json={'expected_revision':run['revision'],'choice':'accept',
        'response':{'confirmed':'PRIVATE_INVALID'}},headers=HEADERS)
    assert invalid.status_code == 422 and 'PRIVATE_INVALID' not in invalid.text
    assert invalid.json()['detail']['code'] == 'response_schema_invalid'
    assert client.get(route,headers=HEADERS).json() == run
    stale = client.post(route+'/resume',json={'expected_revision':'a'*64,'choice':'accept',
        'response':{'confirmed':True}},headers=HEADERS)
    assert stale.status_code == 409
    native.host.config['native']['tenants']['a']['schemas'] = []
    assert client.post(route+'/resume',json={'expected_revision':run['revision'],'choice':'accept',
        'response':{'confirmed':True}},headers=HEADERS).status_code == 403
    native.host.config['native']['tenants']['a']['schemas'] = ['found','reviewed','decision']
    completed = client.post(route+'/resume',json={'expected_revision':run['revision'],'choice':'accept',
        'response':{'confirmed':True}},headers=HEADERS)
    assert completed.status_code == 200 and completed.json()['status'] == 'completed'


def test_proposal_only_body_ceiling_exact_path_and_authentication(native_client):
    client,_,_ = native_client
    raw = ' '*9000+'{"definition":{"version":1,"start":"done","steps":{"done":{"kind":"finish"}}}}'
    assert client.post('/workflow-proposals',content=raw,headers=HEADERS).status_code == 200
    for path in ('/native-runs','/runs','/workflow-proposals/','/workflow-proposals-extra'):
        assert client.post(path,content=raw,headers=HEADERS).status_code == 413
    assert client.post('/workflow-proposals',content=' '*65537,headers=HEADERS).status_code == 413
    assert client.post('/workflow-proposals',content=raw).status_code == 401


def test_two_specialists_check_gate_pause_use_actual_runtime_transport(native_client,monkeypatch):
    import io
    import urllib.request
    from lab_runner import model
    from prosaic_integration_lab.native_execution import approved_proposal
    client,native,counters = native_client
    observed = []
    observations = []
    native.host.observer = observations.append
    with TestClient(model.app) as fixture:
        fixture.post('/control',json={'scenario':'normal'})
        def transport(request, *, timeout):
            counters['models'] += 1
            payload = json.loads(request.data)
            observed.append(payload)
            response = fixture.post('/v1/chat/completions',json=payload)
            assert response.status_code == 200
            class Response(io.BytesIO):
                status = 200
                headers = {'content-type':'application/json'}
            return Response(response.content)
        monkeypatch.setattr(urllib.request.OpenerDirector,'open',
            lambda self,request,timeout:transport(request,timeout=timeout))
        saved = proposal(client)
        started = client.post('/native-runs',json={'proposal_id':saved['proposal_id'],'inputs':{'task':'synthetic'}},
            headers={**HEADERS,'Idempotency-Key':'run'})
        assert started.status_code == 200, started.text
        run = started.json()
        assert run['status'] == 'waiting', run
        assert run['interaction']['reviewOutputs'] == {'review':{'entity_id':'synthetic-entity','approved':True}}
        assert counters['models'] == 2
        assert counters['validators'] == 1
        scopes = [record for record in observations if record['event']=='invocation_started' and record['source']=='runtime']
        assert len(scopes)==2
        assert {record['run_id'] for record in scopes} == {run['run_id']}
        assert {record['step_id'] for record in scopes} == {'find','review'}
        assert {record['operation_namespace'] for record in scopes} == {'PRIVATE_HOST_NAMESPACE'}
        assert len({record['invocation_id'] for record in scopes})==2
        assert all(payload['model']=='test-model' and payload.get('tools',[])==[] for payload in observed)
        # The same host reservation replays without another dispatch even when
        # the live defaults/capacity change; input and billing remain frozen.
        native.host.capacity['max_runs'] = native.host.capacity['max_tenant_runs'] = 1
        replay = client.post('/native-runs',json={'proposal_id':saved['proposal_id'],'inputs':{'task':'synthetic'}},
            headers={**HEADERS,'Idempotency-Key':'run'})
        assert replay.json() == run and counters['models']==2
        response = client.post('/runs/'+run['run_id']+'/resume',json={'expected_revision':run['revision'],
            'choice':'accept','response':{'confirmed':True}},headers=HEADERS)
        assert response.status_code == 200 and response.json()['status']=='completed'
        assert counters['models']==2


def test_composition_denial_and_inline_denial_are_independent(native_client):
    client,native,counters = native_client
    from prosaic_integration_lab.native_execution import approved_proposal
    denied = client.post('/workflow-proposals',json=approved_proposal(),
        headers={**HEADERS,'Authorization':'Bearer tenant-b-token'})
    assert denied.status_code == 422 and denied.json()['detail']['code']=='policy_denied'
    inline = {'definition':{'version':1,'start':'one','steps':{'one':{'kind':'agent','agent':'inline',
        'schema':'found','next':'done'},'done':{'kind':'finish'}}},'inline_agents':{'inline':{
        'type':'subagent','frontmatter':{'name':'inline','description':'Synthetic inline','tools':[]},
        'body':'ALWAYS return synthetic JSON. NEVER access product data.'}}}
    denied = client.post('/workflow-proposals',json=inline,headers=HEADERS)
    assert denied.status_code == 422 and denied.json()['detail']['code']=='policy_denied'
    assert counters['models']==counters['reservations']==0


def test_native_strict_body_and_utf8_key_bounds(native_client):
    client,_,counters = native_client
    saved = proposal(client)
    for extra in ({'tenant_id':'a'},{'billing_account_id':'a'},{'operation_namespace':'a'},{'retry_interrupted':True}):
        response = client.post('/native-runs',json={'proposal_id':saved['proposal_id'],'inputs':{},**extra},
            headers={**HEADERS,'Idempotency-Key':'bad'})
        assert response.status_code == 422
    assert client.post('/workflow-proposals',content='{}',headers={**HEADERS,'Idempotency-Key':'x'*129}).status_code == 422
    assert counters['reservations']==0


def test_native_receipt_crash_replay_adopts_without_first_call_redispatch(native_client,monkeypatch):
    import io
    import urllib.request
    from lab_runner import model
    client,native,counters = native_client
    crashed = []
    def critical(event):
        if event['event']=='accepted' and not crashed:
            crashed.append(True)
            raise RuntimeError('PRIVATE_RECEIPT_CRASH')
    native.host.config['fixture_events_url']='synthetic-critical-gate'
    native.host.fixture_event=critical
    with TestClient(model.app) as fixture:
        fixture.post('/control',json={'scenario':'normal'})
        def transport(self,request,timeout):
            counters['models']+=1
            response=fixture.post('/v1/chat/completions',json=json.loads(request.data))
            class Response(io.BytesIO):
                status=200
                headers={'content-type':'application/json'}
            return Response(response.content)
        monkeypatch.setattr(urllib.request.OpenerDirector,'open',transport)
        saved=proposal(client)
        payload={'proposal_id':saved['proposal_id'],'inputs':{}}
        response=client.post('/native-runs',json=payload,headers={**HEADERS,'Idempotency-Key':'crash'})
        assert response.status_code==503 and 'PRIVATE_RECEIPT_CRASH' not in response.text
        assert counters['models']==1
        replay=client.post('/native-runs',json=payload,headers={**HEADERS,'Idempotency-Key':'crash'})
        assert replay.status_code==200 and counters['models']==1
        pending=replay.json()
        recovered=client.post('/runs/'+pending['run_id']+'/resume',json={'expected_revision':pending['revision']},headers=HEADERS)
        assert recovered.status_code==200 and recovered.json()['status']=='waiting'
        assert counters['models']==2


def test_large_waiting_view_can_start_status_replay_and_resume(native_client):
    client,_,counters = native_client
    question='q'*9000
    body={'definition':{'version':1,'start':'ask','steps':{
        'ask':{'kind':'pause','question':question,'choices':{'accept':'done'},'response_schema':'decision'},
        'done':{'kind':'finish'}}}}
    proposal_response=client.post('/workflow-proposals',json=body,headers=HEADERS)
    assert proposal_response.status_code==200
    payload={'proposal_id':proposal_response.json()['proposal_id'],'inputs':{}}
    headers={**HEADERS,'Idempotency-Key':'large-view'}
    started=client.post('/native-runs',json=payload,headers=headers)
    assert started.status_code==200,started.text
    run=started.json()
    assert run['status']=='waiting' and run['interaction']['question']==question
    assert len(started.content)>8192
    assert client.get('/runs/'+run['run_id'],headers=HEADERS).json()==run
    assert client.post('/native-runs',json=payload,headers=headers).json()==run
    resumed=client.post('/runs/'+run['run_id']+'/resume',json={'expected_revision':run['revision'],
        'choice':'accept','response':{'confirmed':True}},headers=HEADERS)
    assert resumed.status_code==200 and resumed.json()['status']=='completed'
    assert counters['models']==counters['validators']==0
    # The expanded public view does not expand incoming run/resume body limits.
    assert client.post('/runs/'+run['run_id']+'/resume',content=' '*8193,headers=HEADERS).status_code==413

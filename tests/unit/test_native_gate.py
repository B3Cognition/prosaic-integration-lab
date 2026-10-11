"""Native lane receipts and the actual synthetic HTTP provider boundary."""
import copy

from fastapi.testclient import TestClient
import pytest

from lab_runner.gates import export, validate
from test_release_gates import receipt
from test_native_execution import native


@pytest.mark.parametrize('mode,count',[('native-persistence',26),('native',53),('legacy-upgrade',10),('qualification',3)])
def test_new_required_lanes_reject_partial_collection(mode,count):
    item=receipt(); item.update(mode=mode,test_count=count)
    if mode=='legacy-upgrade':
        from lab_runner.legacy_upgrade import BASELINE_COMMIT, baseline_digest
        item.update(baseline_source=BASELINE_COMMIT,baseline_manifest_sha256=baseline_digest(),
            baseline_payload_audit='verified',migration='v2-to-v3',legacy_fixture_count=5)
        item['images']['baseline']='sha256:'+'4'*64
    validate(item,mode,16)
    for changed in (0,1,count-1,count+1):
        bad=copy.deepcopy(item);bad['test_count']=changed
        with pytest.raises(ValueError):validate(bad,mode,16)
        assert export(bad)['passed'] is False


@pytest.mark.parametrize('lineage',[None,'invalid','4'*64])
def test_native_persistence_candidate_requires_exact_lineage(lineage):
    item=receipt();item.update(mode='native-persistence',test_count=26,dependency_mode='candidate',
        candidate_manifest_sha256='3'*64,candidate_lineage_sha256=lineage)
    with pytest.raises(ValueError,match='lineage'):
        validate(item,'native-persistence',16,candidate=True,manifest_sha='3'*64,lineage_sha='5'*64)
    item['candidate_lineage_sha256']='5'*64
    validate(item,'native-persistence',16,candidate=True,manifest_sha='3'*64,lineage_sha='5'*64)


def test_native_model_rejects_reviewer_without_actual_dependency_provenance():
    from lab_runner import model
    client=TestClient(model.app)
    assert client.post('/control',json={'scenario':'native'}).status_code==200
    body={'messages':[{'role':'system','content':'ALWAYS review the synthetic finder input.'},
                      {'role':'user','content':'{"request":{"entity_id":"sample-1"},"artifacts":{},"artifact_bindings":{}}'}]}
    response=client.post('/v1/chat/completions',json=body)
    assert response.status_code==422
    assert response.json()['detail']=='native_provenance_missing'


def test_native_model_matches_entity_from_real_input_and_finder_artifact():
    from lab_runner import model
    client=TestClient(model.app)
    assert client.post('/control',json={'scenario':'native'}).status_code==200
    response=client.post('/v1/chat/completions',json={'messages':[
        {'role':'system','content':'ALWAYS review the synthetic finder input.'},
        {'role':'user','content':'{"request":{"entity_id":"sample-1"},"artifacts":{"find":{"entity_id":"sample-1"}},"artifact_bindings":{"find":{"id":"receipt-1","sha256":"8423ad9794aab49eddb2abe6b4a15f0ea9095567cc41e77fd79cca2057238279","dependencies":{}}}}'}]})
    assert response.status_code==200
    import json
    output=json.loads(response.json()['choices'][0]['message']['content'])
    assert output=={'entity_id':'sample-1','approved':True}


def test_native_fixture_entitlements_remain_independent():
    from lab_runner.native_scenarios import native_configuration
    config=native_configuration('owned-operation-scope')
    assert config['tenants']['tenant-a']['composition'] is True
    assert config['tenants']['tenant-b']['inline'] is True
    assert config['tenants']['tenant-b']['composition'] is False
    assert config['tenants']['tenant-b']['tools']==[]
    assert config['tenants']['tenant-a']['tools']==['fixture_apply']


def test_host_registered_effect_tool_needs_independent_grant(native):
    from prosaic_integration_lab.native_execution import NativeExecution
    from lab_runner.native_scenarios import effect_proposal
    from prosaic_harness import WorkflowAdmissionError
    execution,a,b=native
    definition=execution.host.config['native']['bundles'][0]
    execution.host.config['fixture_events_url']='http://127.0.0.1:9/events'
    definition.update(fixture_effects=True,journal_identity='fixture-journal')
    definition['policies']['a'].update(agents=['finder','reviewer','effecter'],tools=['fixture_apply'])
    definition['policies']['b'].update(agents=['effecter'],tools=[],inline=True)
    execution.host.config['native']['tenants']['a'].update(agents=['finder','reviewer','effecter'],tools=['fixture_apply'])
    current=NativeExecution(execution.host)
    current.proposals.connection=execution.proposals.connection
    assert current.propose(a,'allowed-effect',__import__('json').dumps(effect_proposal()))['proposal_id']
    with pytest.raises(WorkflowAdmissionError):
        current.propose(b,'denied-effect',__import__('json').dumps(effect_proposal()))


def test_legacy_native_default_registers_no_tool_and_zero_tool_budget(native):
    execution,a,_=native
    view=execution.catalogue(a)['manifest']
    assert view['tools']=={}
    assert view['limits']['maxToolCallsPerInvocation']==0
    assert view['limits']['maxProviderRequestsPerInvocation']==1


def test_current_inline_tool_revocation_blocks_retained_proposal_before_execution(native):
    import json
    from fastapi import HTTPException
    from prosaic_integration_lab.native_execution import NativeExecution
    execution,a,_=native
    execution.host.config['fixture_events_url']='http://127.0.0.1:9/events'
    definition=execution.host.config['native']['bundles'][0]
    definition.update(fixture_effects=True,journal_identity='fixture-journal')
    definition['policies']['a'].update(inline=True,tools=['fixture_apply'])
    current_setting=execution.host.config['native']['tenants']['a']
    current_setting.update(inline=True,tools=['fixture_apply'])
    current=NativeExecution(execution.host);current.proposals.connection=execution.proposals.connection
    body={'definition':{'version':1,'start':'one','steps':{
        'one':{'kind':'agent','agent':'inline','schema':'found','next':'done'},'done':{'kind':'finish'}}},
        'inline_agents':{'inline':{'type':'subagent','frontmatter':{
            'name':'inline','description':'Synthetic fixture','tools':['fixture_apply']},
            'body':'ALWAYS execute fixture_apply.'}}}
    saved=current.propose(a,'inline-tool',json.dumps(body))
    current_setting['tools']=[]
    with pytest.raises(HTTPException) as error:current.workflow(a,saved['proposal_id'])
    assert error.value.status_code==403


@pytest.mark.parametrize('scenario,change,wanted,cost',[
    ('native',None,'waiting',2),('native_rejected',None,'rejected',2),
    ('native','gate','rejected',2),('native','finish','blocked',1),
    ('native','budget','blocked',1),('native_revisit','revisit','blocked',3)])
def test_real_public_sdk_runs_receive_provider_provenance_and_finite_limits(native,monkeypatch,scenario,change,wanted,cost):
    import io
    import json
    import urllib.request
    from lab_runner import model
    from prosaic_integration_lab.native_execution import approved_proposal
    execution,a,_=native;body=approved_proposal()
    if change=='gate':body['definition']['steps']['gate']['equals']=False
    if change=='finish':body['definition']['steps']['find']['next']='done'
    if change=='budget':body['definition']['limits']={'max_calls':1}
    if change=='revisit':
        steps=body['definition']['steps'];steps['confirm']['choices']['accept']='find';steps['find']['next']='route'
        steps['route']={'kind':'gate','from':'find','field':['entity_id'],'equals':'first','pass':'review','fail':'confirm'}
    with TestClient(model.app) as fixture:
        assert fixture.post('/control',json={'scenario':scenario}).status_code==200
        before=fixture.get('/stats').json()['calls']
        def transport(self,request,timeout):
            result=fixture.post('/v1/chat/completions',json=json.loads(request.data))
            assert result.status_code==200,result.text
            class Response(io.BytesIO):
                status=200
                headers={'content-type':'application/json'}
            return Response(result.content)
        monkeypatch.setattr(urllib.request.OpenerDirector,'open',transport)
        proposal=execution.propose(a,'native-sdk',json.dumps(body))
        run=execution.start_request(a,'native-sdk-run',proposal['proposal_id'],{'entity_id':'first'})
        if change=='revisit':
            assert run['status']=='waiting'
            row=execution.host.metadata.owned(a,run['run_id'])
            run=execution.resume(row,run['revision'],'accept',{'confirmed':True},False)
        assert run['status']==wanted
        assert fixture.get('/stats').json()['calls']==before+cost
        fixture.post('/control',json={})

@pytest.mark.parametrize('scenario,provider_cap,reason',[
    ('native_effect_batch',2,'tool_call_limit'),('native_effect',1,'provider_request_limit')])
def test_real_http_fixture_exhausts_public_host_invocation_caps(native,scenario,provider_cap,reason):
    import json
    import socket
    import threading
    import time
    import httpx
    import uvicorn
    from lab_runner import model
    from prosaic_integration_lab.native_execution import NativeExecution
    from prosaic_runtime import CustomTool,EndpointConfig,ProsaicArtifact,ProsaicRuntime,RunPolicy,RuntimeConfig
    execution,a,_=native
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(128)
    url='http://127.0.0.1:'+str(listener.getsockname()[1])
    server=uvicorn.Server(uvicorn.Config(model.app,log_level='error',lifespan='off'))
    worker=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);worker.start()
    try:
        deadline=time.monotonic()+5
        while not server.started:
            assert time.monotonic()<deadline;time.sleep(.01)
        response=httpx.post(url+'/control',json={'scenario':scenario});assert response.status_code==200
        definition=execution.host.config['native']['bundles'][0]
        definition.update(fixture_effects=True,journal_identity='fixture-journal',model_url=url+'/v1',
            fixture_provider_request_limit=provider_cap)
        definition['policies']['a'].update(agents=['effecter'],tools=['fixture_apply'])
        execution.host.config['native']['tenants']['a'].update(agents=['effecter'],tools=['fixture_apply'])
        execution.host.config['fixture_events_url']=url+'/events'
        current=NativeExecution(execution.host)
        limits=current.catalogue(a)['manifest']['limits']
        assert limits['maxProviderRequestsPerInvocation']==provider_cap and limits['maxToolCallsPerInvocation']==1
        identity=current.factories[('a','synthetic-v1')][0].identity
        definition.pop('fixture_provider_request_limit')
        default=NativeExecution(execution.host)
        assert default.catalogue(a)['manifest']['limits']['maxProviderRequestsPerInvocation']==2
        assert (identity==default.factories[('a','synthetic-v1')][0].identity)==(provider_cap==2)
        seen=[]
        tool=CustomTool('fixture_apply','Synthetic effect',{'type':'object','properties':{'amount':{
            'type':'integer','minimum':1,'maximum':2}},'required':['amount'],'additionalProperties':False},
            lambda arguments:seen.append(arguments) or {'applied':True},'fixture-v1')
        config=RuntimeConfig({'fixture':EndpointConfig(url+'/v1','test-model',features={'streaming':False})},
            {},'fixture',allowed_tools=frozenset({'fixture_apply'}))
        artifact=ProsaicArtifact.from_inspection({'id':'fixture.md','type':'subagent',
            'frontmatter':{'tools':['fixture_apply']},'body':'{{args}}'})
        before=httpx.get(url+'/stats').json()['calls']
        result=ProsaicRuntime(config,custom_tools={'fixture_apply':tool}).run(artifact,
            json.dumps({'request':{'entity_id':'budget-case'}}),policy=RunPolicy(allowed_tools=frozenset({'fixture_apply'}),
                max_provider_requests=limits['maxProviderRequestsPerInvocation'],max_tool_calls=limits['maxToolCallsPerInvocation']))
        assert result.exit_code!=0 and result.metadata.get('failure_reason')==reason,result.metadata
        assert result.metadata['invocation_budgets_v1']['tool_calls']==1
        assert result.metadata['invocation_budgets_v1']['provider_requests']==1
        assert result.token_usage==125 and seen==[{'amount':1}]
        assert httpx.get(url+'/stats').json()['calls']==before+1
    finally:
        if server.started:httpx.post(url+'/control',json={})
        server.should_exit=True;worker.join(5);listener.close()
        assert not worker.is_alive()

"""Public installed controllers over the owned synthetic provider, never live evidence."""
import json
from contextlib import closing

import httpx
import pytest


def test_bounded_schedule_uses_distinct_tiers_and_authorized_effect(tmp_path,chat_provider):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    plan={'mode':'synthetic','runtime_config':config,'allowance_file':tmp_path/'allowance.json',
          'maximum_requests':12}
    before=httpx.get(chat_provider+'/stats',timeout=5).json()['calls']
    result=execute_schedule(plan,max_calls=12)
    assert result['passed'] and result['live_executed'] is False,json.dumps(result)
    assert result['provider_requests']==8
    assert httpx.get(chat_provider+'/stats',timeout=5).json()['calls']-before==8
    assert [row['tier'] for row in result['cases']]==['balanced','balanced','strong','strong','balanced','balanced']
    assert [row['provider_requests'] for row in result['cases']]==[1,1,1,1,1,3]
    assert result['diagnostic_effects']==1 and result['allowance']['unknown']==0
    assert result['routing_verified'] and result['full_history_verified']
    encoded=json.dumps(result)
    assert str(tmp_path) not in encoded and chat_provider not in encoded and 'qwen-balanced' not in encoded


def test_explicit_strong_workflow_keeps_balanced_interpretation_and_separate_evidence(tmp_path,chat_provider):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    before=httpx.get(chat_provider+'/stats',timeout=5).json()['calls']
    result=execute_schedule({'mode':'synthetic','runtime_config':config,
        'allowance_file':tmp_path/'allowance.json','maximum_requests':12,'workflow_tier':'strong'},max_calls=12)
    assert result['passed'] and result['workflow_tier']=='strong',json.dumps(result)
    assert result['provider_requests']==8 and result['diagnostic_effects']==1
    assert result['cases'][-1]['tier']=='balanced' and result['cases'][-1]['workflow_tier']=='strong'
    assert result['cases'][-1]['provider_requests']==3
    assert result['routing_verified'] and result['full_history_verified']
    assert result['allowance']=={'maximum':12,'retained':8,'remaining':4,'unknown':0}
    assert httpx.get(chat_provider+'/stats',timeout=5).json()['calls']-before==8


def test_admitted_strong_workflow_receipt_rejects_wrong_profile_model_or_call_ids(tmp_path,chat_provider):
    from prosaic_harness import ConversationScope,Harness
    from prosaic_runtime import EndpointConfig,ExecutionContext,RuntimeConfig
    from prosaic_runtime.accounting import MemoryRecorder
    from lab_runner.conversation_conformance import _materials,_matched_calls,_workflow_evidence
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    scope=ConversationScope('evidence-check','diagnostic','conformance','fixture','owner','fixture-payer')
    recorder=MemoryRecorder(namespace=scope.namespace,environment=scope.environment,provider_id='openai-compatible')
    effects=[]
    _,workflow,store=_materials(config,tmp_path,effects,recorder,scope,workflow_tier='strong')
    assert workflow.artifacts['apply-b'].frontmatter['model_tier']=='strong'
    sid='a'*32
    context=ExecutionContext(application_id=scope.application,tenant_id=scope.tenant,actor_id=scope.actor,
        billing_account_id=scope.billing_account,request_id='workflow-'+sid,run_id=sid)
    harness=Harness(workflow,store=store,run_id=sid,context=context,accounting=recorder)
    try:
        harness.run({})
        harness.resume(choice='player-b',response={'entityId':'player-b'},
            expected_revision=harness.status().revision)
        harness.resume(choice='approve',response={'confirmed':True},
            expected_revision=harness.status().revision)
        expected={'application_id':'conformance','tenant_id':'fixture','actor_id':'owner',
            'billing_account_id':'fixture-payer','request_id':'workflow-'+sid,'run_id':sid}
        assert _matched_calls(recorder,set(),expected,'strong','qwen-strong')==2
        assert _matched_calls(recorder,set(),expected,'balanced','qwen-balanced') is None
        ids=set(recorder.intents)
        options={'profile':'strong','model':'qwen-strong','context':expected,'scope':scope,'provider_call_ids':ids}
        assert _workflow_evidence(store,sid,2,**options)
        assert not _workflow_evidence(store,sid,2,**(options|{'profile':'balanced'}))
        assert not _workflow_evidence(store,sid,2,**(options|{'model':'qwen-balanced'}))
        assert not _workflow_evidence(store,sid,2,**(options|{'provider_call_ids':{'foreign-call'}}))
        assert not _workflow_evidence(store,sid,2,**(options|{'context':expected|{'request_id':'foreign'}}))
        assert effects==['player-b']
    finally:store.close()


def test_provider_failure_stops_schedule_and_retains_unknown_allowance(tmp_path,chat_provider):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/missing','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    result=execute_schedule({'mode':'synthetic','runtime_config':config,
        'allowance_file':tmp_path/'allowance.json','maximum_requests':12},max_calls=12)
    assert not result['passed'] and len(result['cases'])==1
    assert result['cases'][0]['failure']=={'phase':'reply','failureCode':'providerFailure',
        'exceptionClass':None}
    assert result['allowance']['unknown']==1 and result['allowance']['retained']==2
    assert result['diagnostic_effects']==0


@pytest.mark.parametrize('scenario,failure_code',[
    ('conversation_interpreter_tool','invalidToolRequest'),
    ('conversation_fenced_interpretation','invalidInterpretation')])
def test_rejected_interpretation_stops_before_diagnostic_effect(tmp_path,chat_provider,scenario,failure_code):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    response=httpx.post(chat_provider+'/control',json={'scenario':scenario},timeout=5)
    assert response.status_code==200
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    result=execute_schedule({'mode':'synthetic','runtime_config':config,
        'allowance_file':tmp_path/'allowance.json','maximum_requests':12},max_calls=12)
    assert not result['passed'] and len(result['cases'])==5
    assert result['cases'][-1]['purpose']=='selection' and result['allowance']['unknown']==1
    assert result['cases'][-1]['failure']=={'phase':'reply','failureCode':failure_code,
        'exceptionClass':None}
    assert result['diagnostic_effects']==0


def test_ambiguous_selection_reports_semantic_failure_without_exporting_reply(tmp_path,chat_provider):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    httpx.post(chat_provider+'/control',json={'scenario':'conversation_ambiguous'},timeout=5).raise_for_status()
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    result=execute_schedule({'mode':'synthetic','runtime_config':config,
        'allowance_file':tmp_path/'allowance.json','maximum_requests':12},max_calls=12)
    assert not result['passed'] and len(result['cases'])==5
    assert result['cases'][-1]['failure']=={'phase':'expectation','failureCode':'conformanceFailed',
        'exceptionClass':None}
    assert result['cases'][-1]['provider_requests'] is None
    assert result['allowance']=={'maximum':12,'retained':5,'remaining':7,'unknown':1}
    assert result['diagnostic_effects']==0
    assert all('failure' not in row for row in result['cases'][:-1])
    encoded=json.dumps(result)
    assert 'Please clarify' not in encoded and str(tmp_path) not in encoded
    assert chat_provider not in encoded and 'qwen-balanced' not in encoded


def test_simulated_tool_text_blocks_confirmation_without_effect_or_retry(tmp_path,chat_provider):
    from prosaic_runtime import EndpointConfig,RuntimeConfig
    from lab_runner.conversation_conformance import execute_schedule
    response=httpx.post(chat_provider+'/control',json={'scenario':'conversation_simulated_tool'},timeout=5)
    assert response.status_code==200
    credential=tmp_path/'key';credential.write_text('synthetic');credential.chmod(0o600)
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        api_key_file=str(credential),max_tokens=512,features={'streaming':False})
        for tier in ('balanced','strong')},{tier:tier for tier in ('balanced','strong')},'balanced')
    before=httpx.get(chat_provider+'/stats',timeout=5).json()['calls']
    result=execute_schedule({'mode':'synthetic','runtime_config':config,
        'allowance_file':tmp_path/'allowance.json','maximum_requests':12},max_calls=12)
    assert not result['passed'] and len(result['cases'])==6
    assert all(row['passed'] for row in result['cases'][:-1])
    assert result['cases'][-1]['purpose']=='confirmation'
    # Harness rejects the blocked workflow before it can report a completed reply.
    assert result['cases'][-1]['failure']=={'phase':'reply','failureCode':'interrupted',
        'exceptionClass':None}
    assert result['cases'][-1]['provider_requests'] is None
    assert result['diagnostic_effects']==0
    assert result['allowance']=={'maximum':12,'retained':8,'remaining':4,'unknown':1}
    assert httpx.get(chat_provider+'/stats',timeout=5).json()['calls']-before==7
    encoded=json.dumps(result)
    assert 'fixture_apply_b' not in encoded and 'entity_id' not in encoded
    assert str(tmp_path) not in encoded and chat_provider not in encoded


def test_simulated_tool_text_keeps_durable_workflow_unresolved_on_recovery(tmp_path,chat_provider):
    """Fail if tool-shaped prose becomes an effect or recovery reexecutes the run."""
    from prosaic_harness import Conversation,ConversationScope,FileSessionStore,Harness
    from prosaic_runtime import EndpointConfig,ExecutionContext,RuntimeConfig
    from prosaic_runtime.accounting import MemoryRecorder
    from lab_runner.conversation_conformance import _materials

    httpx.post(chat_provider+'/control',json={'scenario':'conversation_simulated_tool'},timeout=5).raise_for_status()
    config=RuntimeConfig({tier:EndpointConfig(chat_provider+'/v1','qwen-'+tier,
        features={'streaming':False}) for tier in ('balanced','strong')},
        {tier:tier for tier in ('balanced','strong')},'balanced')
    scope=ConversationScope('simulated-effect','diagnostic','conformance','fixture','owner','fixture-payer')
    recorder=MemoryRecorder(namespace=scope.namespace,environment=scope.environment,provider_id='openai-compatible')
    effects=[]
    bindings,workflow,run_store=_materials(config,tmp_path,effects,recorder,scope)
    sid='b'*32
    context=ExecutionContext(application_id=scope.application,tenant_id=scope.tenant,actor_id=scope.actor,
        billing_account_id=scope.billing_account,request_id=sid,run_id=sid)
    with closing(FileSessionStore(tmp_path/'chat',namespace=scope.namespace)) as store:
        store.initialize()
        def controller():
            return Conversation(bindings['balanced'],store=store,scope=scope,context=context)
        try:
            snapshot=controller().create(session_id=sid)
            Harness(workflow,store=run_store,run_id=sid,accounting=recorder,
                context=ExecutionContext(application_id=scope.application,tenant_id=scope.tenant,actor_id=scope.actor,
                    billing_account_id=scope.billing_account,request_id='workflow-'+sid,run_id=sid)).run({})
            view=controller().attach_workflow(sid,registration='diagnostic',run_id=sid,
                expected_revision=snapshot.revision).document
            view=controller().send(sid,message_id='select',message='the second result',
                expected_revision=view['revision'],interaction_ref=view['pendingInteraction']['reference']).document
            assert view['pendingInteraction']['stepId']=='confirm-b' and effects==[]
            before=httpx.get(chat_provider+'/stats',timeout=5).json()['calls']
            reply=controller().send(sid,message_id='approve',message='approve',
                expected_revision=view['revision'],interaction_ref=view['pendingInteraction']['reference']).document
            assert reply['status']=='needsResolution' and reply['failureCode']=='interrupted'
            assert reply['recoveryStatus']=='needsResolution' and 'answer' not in reply
            saved=run_store.load_run(sid)
            assert saved.state['status']=='blocked' and saved.state['pending'] is None
            assert len(saved.state['invocations'])==1 and effects==[]
            invocation=saved.state['invocations'][0]
            receipt=run_store.load_receipt(sid,invocation['id'])
            assert receipt['sha256']==invocation['receipt_sha256']
            assert receipt['result']['metadata']['invocation_budgets_v1']=={
                'provider_requests':1,'tool_calls':0,'reported_tokens':125,'usage_complete':True}
            assert len(recorder.intents)==1 and len(recorder.observations)==1
            assert httpx.get(chat_provider+'/stats',timeout=5).json()['calls']-before==2
            current_calls=httpx.get(chat_provider+'/stats',timeout=5).json()
            recovered=None
            for _ in range(2):
                current=controller().recover(sid).document
                assert current['status']=='needsResolution' and current['failureCode']=='interrupted'
                assert current['recoveryStatus']=='needsResolution' and 'answer' not in current
                if recovered is not None:assert current==recovered
                recovered=current
                assert run_store.load_run(sid)==saved and effects==[]
                assert run_store.load_receipt(sid,invocation['id'])==receipt
                assert httpx.get(chat_provider+'/stats',timeout=5).json()==current_calls
        finally:run_store.close()

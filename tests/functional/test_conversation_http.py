"""Lost acknowledgements at application boundaries use genuine installed SDKs."""
import pytest
from prosaic_harness import RunNotFound

from tests.functional.test_conversation_journey import HEADERS,create,send,stats


def fail_once(registry,name,monkeypatch):
    original=getattr(registry,name);failed=[]
    def uncertain(*args,**kwargs):
        if not failed:
            failed.append(True)
            raise RuntimeError('application acknowledgement lost')
        return original(*args,**kwargs)
    monkeypatch.setattr(registry,name,uncertain)


def test_create_acknowledgement_loss_reuses_same_reserved_and_sdk_session(chat_client,monkeypatch):
    chat=chat_client;registry=chat.client.app.state.execution.conversation.registry
    fail_once(registry,'adopt_creation',monkeypatch)
    before=stats(chat)['calls']
    response=chat.client.post('/conversations',json={},headers={**HEADERS,'Idempotency-Key':'unknown-create'})
    assert response.status_code==503
    from prosaic_integration_lab.identity import Principal
    reserved=registry.creation(Principal('tenant-a','alice','payer'),'unknown-create')
    result=create(chat,'unknown-create')
    assert result['sessionId']==reserved['session_id'] and stats(chat)['calls']==before


@pytest.mark.parametrize('boundary',['workflow_started','workflow_attached'])
def test_started_or_attached_acknowledgement_loss_reconciles_without_second_dispatch(chat_client,monkeypatch,boundary):
    chat=chat_client;initial=create(chat);registry=chat.client.app.state.execution.conversation.registry
    fail_once(registry,boundary,monkeypatch)
    send(chat,initial,'find','Find players',status=503)
    before=stats(chat)
    saved=chat.host.store.load_run(initial['sessionId'])
    reply=send(chat,initial,'find','Find players')
    assert reply['pendingInteraction']['stepId']=='select' and stats(chat)==before
    assert chat.host.store.load_run(initial['sessionId']).revision==saved.revision


def test_unknown_start_marker_without_run_never_grants_automatic_start(chat_client,monkeypatch):
    chat=chat_client;initial=create(chat);registry=chat.client.app.state.execution.conversation.registry
    original=registry.claim_workflow_start;failed=[]
    def lost_ack(row):
        result=original(row)
        if not failed:
            failed.append(True);raise RuntimeError('start marker acknowledgement lost')
        return result
    monkeypatch.setattr(registry,'claim_workflow_start',lost_ack)
    send(chat,initial,'find','Find players',status=503)
    before=stats(chat)
    reply=send(chat,initial,'find','Find players',status=409)
    assert reply=={'detail':{'code':'needsResolution'}} and stats(chat)==before
    with pytest.raises(RunNotFound):chat.host.store.load_run(initial['sessionId'])
    for method,route in (('get',''),('post','/recover')):
        operation=getattr(chat.client,method)
        result=operation('/conversations/'+initial['sessionId']+route,headers=HEADERS,
            **({'json':{}} if method=='post' else {}))
        assert result.status_code==200,result.text
        assert result.json()['status']=='needsResolution'
        assert result.json()['recoveryStatus']=='needsResolution'
        assert stats(chat)==before
        with pytest.raises(RunNotFound):chat.host.store.load_run(initial['sessionId'])


@pytest.mark.parametrize('completed',[False,True],ids=['advanced','completed'])
def test_lost_attachment_ack_replays_after_workflow_advancement_without_effect_or_revision_change(chat_client,monkeypatch,completed):
    chat=chat_client;initial=create(chat);registry=chat.client.app.state.execution.conversation.registry
    fail_once(registry,'workflow_attached',monkeypatch)
    send(chat,initial,'find','Find players',status=503)
    current=chat.client.get('/conversations/'+initial['sessionId'],headers=HEADERS).json()
    current=send(chat,current,'second','the second result',reference=current['pendingInteraction']['reference'])
    if completed:
        current=send(chat,current,'approve','approve',reference=current['pendingInteraction']['reference'])
        assert current['pendingInteraction'] is None
    before=stats(chat);run=chat.host.store.load_run(initial['sessionId'])
    replay=send(chat,initial,'find','Find players')
    assert replay['messageId']=='find' and replay['status']=='completed'
    assert stats(chat)==before and chat.host.store.load_run(initial['sessionId']).revision==run.revision
    assert chat.client.get('/conversations/'+initial['sessionId'],headers=HEADERS).json()==current


def test_uncertain_attachment_reads_still_check_current_grant_before_host_or_sdk_lookup(chat_client,monkeypatch):
    chat=chat_client;initial=create(chat);api=chat.client.app.state.execution.conversation
    chat.host.config['conversation']['tenants']['tenant-a']['enabled']=False
    monkeypatch.setattr(api.registry,'owned',lambda *args:pytest.fail('revoked read touched host registry'))
    for method,route in (('get',''),('post','/recover')):
        result=getattr(chat.client,method)('/conversations/'+initial['sessionId']+route,headers=HEADERS,
            **({'json':{}} if method=='post' else {}))
        assert result.status_code==403


@pytest.mark.parametrize('phase,effects',[
    ('workflowCommandPrepared',0),('workflowCommandReturned',1)],ids=['before-effect','after-effect'])
def test_public_approval_phase_failure_retains_real_journal_and_never_resumes(chat_client,monkeypatch,phase,effects):
    import sqlite3
    import prosaic_integration_lab.conversation_execution as api
    chat=chat_client;session=send(chat,create(chat),'find','Find players')
    session=send(chat,session,'second','the second result',reference=session['pendingInteraction']['reference'])
    original=api.phase_observer
    def lose_ack(config,on_event=None):
        callback=original(config,on_event)
        def observed(event):
            callback(event)
            if event['event']==phase:raise RuntimeError('host phase acknowledgement lost')
        return observed
    monkeypatch.setattr(api,'phase_observer',lose_ack)
    send(chat,session,'approve','approve',reference=session['pendingInteraction']['reference'],status=503)
    before=stats(chat);run=chat.host.store.load_run(session['sessionId'])
    with sqlite3.connect(chat.effects_path) as connection:
        domain=connection.execute('SELECT * FROM effects').fetchall()
    with sqlite3.connect(chat.journal_path) as connection:
        journal=connection.execute('SELECT * FROM tool_operations').fetchall()
    assert len(domain)==effects and len(journal)==effects
    if effects:assert journal[0][4]=='completed'
    assert run.state['status']==('completed' if effects else 'waiting')
    from prosaic_harness import ConversationScope
    scope=ConversationScope('owned-chat','sandbox','integration-lab-chat','tenant-a','alice','payer')
    consumer=chat.client.app.state.execution.conversation
    pending=consumer.store.load_session(session['sessionId'],scope=scope).state['pending']
    assert pending['phase']=='workflowCommand'
    command=pending['command']
    assert command['sourceMessageId']=='approve' and command['choice']=='approve'
    assert command['response']=={'confirmed':True}
    assert command['revision']==session['pendingInteraction']['revision']
    assert command['runId']==session['sessionId']
    matches=[event for event in run.state['history'] if event.get('decision_id')==command['decisionId']]
    assert len(matches)==effects
    if effects:
        assert matches[0]['decision_revision']==command['revision']
        assert matches[0]['choice']==command['choice'] and matches[0]['response']==command['response']
        assert run.state['pending'] is None
    chat.restore()
    recovered=None
    for _ in range(2):
        result=chat.client.post('/conversations/'+session['sessionId']+'/recover',json={},headers=HEADERS)
        assert result.status_code==200
        current=result.json()
        # Only the exact committed decision can be adopted; a prepared command stays unresolved.
        assert current['status']==('completed' if effects else 'needsResolution')
        assert current['recoveryStatus']==(None if effects else 'needsResolution')
        assert current['failureCode']==(None if effects else 'interrupted')
        if effects:assert current['answer']=='Workflow completed.' and current['pendingInteraction'] is None
        if recovered is not None:assert current==recovered
        recovered=current
        assert stats(chat)==before and chat.host.store.load_run(session['sessionId'])==run
        with sqlite3.connect(chat.effects_path) as connection:assert connection.execute('SELECT * FROM effects').fetchall()==domain
        with sqlite3.connect(chat.journal_path) as connection:assert connection.execute('SELECT * FROM tool_operations').fetchall()==journal


@pytest.mark.parametrize('decision_id',[None,'f'*32],ids=['missing-id','different-id'])
def test_recovery_does_not_adopt_an_unrelated_completed_approval(chat_client,monkeypatch,decision_id):
    """Terminal state and matching choice/response cannot establish this command's completion."""
    from prosaic_harness import Harness
    from prosaic_runtime import ExecutionContext
    import sqlite3
    import prosaic_integration_lab.conversation_execution as api

    chat=chat_client;session=send(chat,create(chat),'find','Find players')
    session=send(chat,session,'second','the second result',reference=session['pendingInteraction']['reference'])
    original=api.phase_observer
    def lose_ack(config,on_event=None):
        callback=original(config,on_event)
        def observed(event):
            callback(event)
            if event['event']=='workflowCommandPrepared':raise RuntimeError('host acknowledgement lost')
        return observed
    monkeypatch.setattr(api,'phase_observer',lose_ack)
    send(chat,session,'approve','approve',reference=session['pendingInteraction']['reference'],status=503)
    workflow,_=chat.client.app.state.execution.conversation.workflow_materials['balanced-v1']
    sid=session['sessionId']
    harness=Harness(workflow,store=chat.host.store,run_id=sid,context=ExecutionContext(
        application_id='integration-lab-chat',tenant_id='tenant-a',actor_id='alice',billing_account_id='payer',
        request_id='workflow-'+sid,run_id=sid))
    harness.resume(choice='approve',response={'confirmed':True},expected_revision=session['pendingInteraction']['revision'],
        decision_id=decision_id)
    saved=chat.host.store.load_run(sid)
    assert saved.state['status']=='completed' and saved.state['pending'] is None
    before=stats(chat)
    with sqlite3.connect(chat.effects_path) as connection:domain=connection.execute('SELECT * FROM effects').fetchall()
    with sqlite3.connect(chat.journal_path) as connection:journal=connection.execute('SELECT * FROM tool_operations').fetchall()
    assert len(domain)==len(journal)==1 and journal[0][4]=='completed'
    chat.restore()
    recovered=None
    for _ in range(2):
        result=chat.client.post('/conversations/'+sid+'/recover',json={},headers=HEADERS)
        assert result.status_code==200
        current=result.json()
        assert current['status']=='needsResolution' and current['recoveryStatus']=='needsResolution'
        assert current['failureCode']=='interrupted' and 'answer' not in current
        if recovered is not None:assert current==recovered
        recovered=current
        assert stats(chat)==before and chat.host.store.load_run(sid)==saved
        with sqlite3.connect(chat.effects_path) as connection:assert connection.execute('SELECT * FROM effects').fetchall()==domain
        with sqlite3.connect(chat.journal_path) as connection:assert connection.execute('SELECT * FROM tool_operations').fetchall()==journal

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
    for _ in range(2):
        result=chat.client.post('/conversations/'+session['sessionId']+'/recover',json={},headers=HEADERS)
        assert result.status_code==200
        recovered = result.json()
        # A saved matching decision can now be reconciled after return without
        # resuming the workflow; a merely prepared command remains uncertain.
        assert recovered['status'] == ('completed' if effects else 'needsResolution')
        assert recovered['recoveryStatus'] == (None if effects else 'needsResolution')
        assert stats(chat)==before and chat.host.store.load_run(session['sessionId']).revision==run.revision
        with sqlite3.connect(chat.effects_path) as connection:assert connection.execute('SELECT * FROM effects').fetchall()==domain
        with sqlite3.connect(chat.journal_path) as connection:assert connection.execute('SELECT * FROM tool_operations').fetchall()==journal

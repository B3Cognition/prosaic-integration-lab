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

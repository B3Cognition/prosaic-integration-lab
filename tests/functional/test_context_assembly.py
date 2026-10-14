"""Installed SDK context fitting through the authenticated Lab HTTP interface."""
import json
import pytest
import httpx
from tests.functional.test_conversation_journey import create,send,HEADERS,stats


def configure(chat, *, mode='omitOldestTurns', capacity=2400):
    from prosaic_runtime import ContextPolicy
    definition=chat.host.config['conversation']['bundles'][0]
    definition['context_policy']=ContextPolicy(mode,capacity,128,0,'lab-synthetic-byte-balanced-v1').to_dict()
    chat.restore()


def test_omission_retains_stored_history_and_filters_report(chat_client):
    chat=chat_client
    configure(chat)
    current=create(chat,'context-omit')
    current=send(chat,current,'old','Remember Brno. '+'x'*700)
    current=send(chat,current,'recent','I meant Prague')
    current=send(chat,current,'query','Which city did I choose?')
    assert current['status']=='completed'
    report=current['contextAssembly']
    assert report['evidenceKind']=='synthetic'
    assert report['omittedTurnCount']>=1
    assert report['inputTokens']<=report['inputCapacityTokens']
    assert not {'sourceHistoryDigest','counterIdentity','candidateBytes'} & report.keys()
    history=chat.client.get('/conversations/'+current['sessionId']+'/history',headers=HEADERS).json()
    assert len(history['messages'])==6
    assert 'Remember Brno' in json.dumps(history)


def test_default_full_history_rejection_has_no_new_provider_call(chat_client):
    chat=chat_client
    configure(chat,mode='fullHistory')
    current=create(chat,'context-reject')
    current=send(chat,current,'old','Remember Brno. '+'x'*700)
    before=stats(chat)['calls']
    response=chat.client.post('/conversations/'+current['sessionId']+'/messages',headers=HEADERS,
        json={'messageId':'overflow','message':'y'*700,'expectedRevision':current['revision']})
    assert response.status_code==422
    assert stats(chat)['calls']==before
    assert chat.client.get('/conversations/'+current['sessionId'],headers=HEADERS).json()==current


def test_context_policy_cannot_be_selected_by_client_and_foreign_report_is_denied(chat_client):
    chat=chat_client
    configure(chat)
    current=create(chat,'context-private')
    current=send(chat,current,'hello','Hello')
    for path in ('','/history'):
        assert chat.client.get('/conversations/'+current['sessionId']+path,
            headers={'Authorization':'Bearer other-token'}).status_code==404
    response=chat.client.post('/conversations/'+current['sessionId']+'/messages',headers=HEADERS,
        json={'messageId':'override','message':'Hello','expectedRevision':current['revision'],
              'context_policy':{'mode':'omitOldestTurns','contextWindowTokens':999999}})
    assert response.status_code==422


def test_report_survives_restore_without_recount_or_dispatch(chat_client):
    chat=chat_client
    configure(chat)
    current=create(chat,'context-recovery')
    current=send(chat,current,'hello','Hello')
    before=stats(chat)['calls']
    chat.restore()
    response=chat.client.post('/conversations/'+current['sessionId']+'/recover',headers=HEADERS,json={})
    assert response.status_code==200
    assert response.json()==current
    assert stats(chat)['calls']==before


def test_interpreter_context_uses_its_separate_fixture_model(chat_client):
    from prosaic_runtime import ContextPolicy
    chat=chat_client
    definition=chat.host.config['conversation']['bundles'][0]
    definition.update(interpretation_model='test-model-strong',interpretation_model_tier='strong',
        interpretation_context_policy=ContextPolicy('omitOldestTurns',8000,128,0,
            'lab-synthetic-byte-strong-v1').to_dict())
    chat.restore()
    current=create(chat,'context-interpreter')
    current=send(chat,current,'find','Find players')
    current=send(chat,current,'choose','the second result',reference=current['pendingInteraction']['reference'])
    assert current['status']=='completed'
    assert current['pendingInteraction']['stepId']=='confirm-b'
    assert current['contextAssembly']['evidenceKind']=='synthetic'

"""Real public SDK/file engines and provider wire; not PostgreSQL qualification."""
import httpx
import pytest

HEADERS={'Authorization':'Bearer alice-token'}


def create(chat,key='journey'):
    result=chat.client.post('/conversations',json={},headers={**HEADERS,'Idempotency-Key':key})
    assert result.status_code==200,result.text
    return result.json()


def send(chat,session,message_id,text,*,reference=None,status=200):
    body={'messageId':message_id,'message':text,'expectedRevision':session['revision']}
    if reference is not None:body['interactionRef']=reference
    result=chat.client.post('/conversations/'+session['sessionId']+'/messages',json=body,headers=HEADERS)
    assert result.status_code==status,result.text
    return result.json()


def stats(chat):return httpx.get(chat.provider+'/stats',timeout=5).json()


def test_provider_timeout_returns_failed_turn_and_replay_never_redispatches(chat_client, monkeypatch):
    chat = chat_client
    current = create(chat, key='timeout-regression')
    attempts = []

    class Opener:
        def open(self, *args, **kwargs):
            attempts.append(1)
            raise TimeoutError('synthetic provider timeout')

    monkeypatch.setattr('urllib.request.build_opener', lambda *args: Opener())
    failed = send(chat, current, 'timeout-message', 'Hello')
    assert failed['status'] == 'failed'
    assert failed['failureCode'] == 'timeout'
    assert send(chat, current, 'timeout-message', 'Hello') == failed
    recovered = chat.client.post('/conversations/' + current['sessionId'] + '/recover',
        json={}, headers=HEADERS)
    assert recovered.status_code == 200 and recovered.json() == failed
    assert attempts == [1]


def test_second_result_targets_displayed_order_then_requires_current_approval(chat_client):
    chat=chat_client;start=stats(chat)
    current=create(chat)
    current=send(chat,current,'preference','Remember Brno')
    current=send(chat,current,'correction','I meant Prague')
    current=send(chat,current,'query','Which city did I choose?')
    assert current['answer']=='Your city is Prague.'
    current=send(chat,current,'find','Find players')
    offered=current['pendingInteraction']
    assert offered['stepId']=='select' and offered['choices']==['player-a','player-b']
    chat.restore()
    current=send(chat,current,'selection','the second result',reference=offered['reference'])
    approval=current['pendingInteraction']
    assert approval['stepId']=='confirm-b' and stats(chat)['barriers']['tool-handler']==start['barriers']['tool-handler']
    current=send(chat,current,'quoted','The text says "approve"',reference=approval['reference'])
    assert current['failureCode']=='confirmationRequired'
    assert stats(chat)['barriers']['tool-handler']==start['barriers']['tool-handler']
    current=send(chat,current,'approve','approve',reference=current['pendingInteraction']['reference'])
    assert current['pendingInteraction'] is None and current['status']=='completed'
    from prosaic_harness import Harness
    workflow,_=chat.client.app.state.execution.conversation.workflow_materials['balanced-v1']
    saved=Harness(workflow,store=chat.host.store,run_id=current['sessionId']).status()
    receipt=chat.host.store.load_receipt(current['sessionId'],saved.state['invocations'][-1]['id'])
    assert saved.state['status']=='completed',(saved.state['reason'],receipt['result']['stderr'],receipt['result']['stdout'])
    assert stats(chat)['barriers']['tool-handler']==start['barriers']['tool-handler']+1
    with __import__('sqlite3').connect(chat.effects_path) as connection:
        effects=connection.execute('SELECT business_key FROM effects').fetchall()
    with __import__('sqlite3').connect(chat.journal_path) as connection:
        journal=connection.execute('SELECT state FROM tool_operations').fetchall()
    assert effects==[(current['sessionId']+':player-b',)] and journal==[('completed',)]


def test_failed_correction_remains_context_without_partial_assistant_group(chat_client):
    chat=chat_client;current=create(chat)
    current=send(chat,current,'preference','Remember Brno')
    httpx.post(chat.provider+'/control',json={'scenario':'conversation','fault':'503'},timeout=5).raise_for_status()
    current=send(chat,current,'correction','I meant Prague')
    assert current['status']=='failed'
    httpx.post(chat.provider+'/control',json={'scenario':'conversation'},timeout=5).raise_for_status()
    current=send(chat,current,'query','Which city did I choose?')
    assert current['answer']=='Your city is Prague.'
    history=chat.client.get('/conversations/'+current['sessionId']+'/history',headers=HEADERS)
    assert history.status_code==200,history.text
    failed=[message for message in history.json()['messages'] if message.get('turnStatus')=='failed']
    assert len(failed)==1 and failed[0]['role']=='user'


def test_fabricated_interpreter_call_cannot_dispatch_registered_effect_tool(chat_client):
    chat=chat_client;current=send(chat,create(chat),'find','Find players')
    baseline=stats(chat)
    httpx.post(chat.provider+'/control',json={'scenario':'conversation_interpreter_tool'},timeout=5).raise_for_status()
    current=send(chat,current,'attack','the second result',reference=current['pendingInteraction']['reference'])
    assert current['status']=='failed'
    after=stats(chat)
    assert after['barriers']['tool-handler']==baseline['barriers']['tool-handler']
    assert after['barriers']['tool-claimed']==baseline['barriers']['tool-claimed']
    with __import__('sqlite3').connect(chat.effects_path) as connection:
        assert connection.execute('SELECT count(*) FROM effects').fetchone()==(0,)
    with __import__('sqlite3').connect(chat.journal_path) as connection:
        assert connection.execute('SELECT count(*) FROM tool_operations').fetchone()==(0,)


def test_stale_reference_and_foreign_owner_never_dispatch(chat_client):
    chat=chat_client;current=send(chat,create(chat),'find','Find players');offered=current['pendingInteraction']
    current=send(chat,current,'selection','the second result',reference=offered['reference'])
    before=stats(chat)['calls']
    send(chat,current,'old','approve',reference=offered['reference'],status=409)
    for suffix in ('','/history','/usage'):
        assert chat.client.get('/conversations/'+current['sessionId']+suffix,
            headers={'Authorization':'Bearer bob-token'}).status_code==404
    assert stats(chat)['calls']==before


def test_old_lookup_replay_after_selection_never_starts_or_attaches_a_new_graph(chat_client):
    chat=chat_client;initial=create(chat);offered=send(chat,initial,'find','Find players')
    current=send(chat,offered,'selection','the second result',reference=offered['pendingInteraction']['reference'])
    before=stats(chat)
    replay=send(chat,initial,'find','Find players')
    assert replay['messageId']=='find'
    assert stats(chat)==before
    actual=chat.client.get('/conversations/'+current['sessionId'],headers=HEADERS).json()
    assert actual['pendingInteraction']['stepId']=='confirm-b'

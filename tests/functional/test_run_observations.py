from prosaic_integration_lab.run_observations import RunObservations, install_observation_routes
from tests.functional.test_conversation_journey import create, send, HEADERS
from tests.functional.test_conversation_journey import stats


def test_actual_sdk_events_are_owner_filtered_and_never_expose_chat_content(chat_client):
    sink = RunObservations()
    chat_client.host.observations = sink
    install_observation_routes(chat_client.client.app, sink)
    session = create(chat_client, 'observatory')
    reply = send(chat_client, session, 'find', 'Find players')
    path = '/conversations/' + session['sessionId'] + '/observations'
    assert chat_client.client.get(path).status_code == 401
    assert chat_client.client.get(path, headers={'Authorization': 'Bearer bob-token'}).status_code == 404
    assert chat_client.client.get(path, headers={'Authorization': 'Bearer other-token'}).status_code == 404
    response = chat_client.client.get(path, headers=HEADERS)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    payload = response.json()
    events = payload['events']
    assert any(item['event'] == 'provider_request_started' for item in events)
    assert any(item['event'] == 'provider_request_completed' for item in events)
    assert any(item['event'] == 'tool_started' for item in events)
    assert any(item['event'] == 'invocation_completed' for item in events)
    assert events[-1]['event'] == 'waiting_committed'
    assert payload['waiting'] is True
    assert payload['usage']['available'] is False  # this file-store fixture has no recorder
    assert payload['usage']['input'] is None
    assert 'Find players' not in response.text
    assert 'First result' not in response.text
    assert 'alice-token' not in response.text
    assert all(set(item) <= {'source', 'event', 'id', 'at', 'sequence', 'turn',
        'invocation_id', 'outcome', 'status', 'duration_ms', 'http_status', 'name',
        'token_usage', 'tool_call_count', 'provider_request_count', 'calls'} for item in events)


def test_observations_preserve_uncertain_workflow_start_without_redispatch(chat_client, monkeypatch):
    chat = chat_client
    sink = RunObservations()
    chat.host.observations = sink
    install_observation_routes(chat.client.app, sink)
    session = create(chat, 'observation-lost-start')
    registry = chat.client.app.state.execution.conversation.registry
    original = registry.claim_workflow_start
    failed = []

    def lost_ack(row):
        result = original(row)
        if not failed:
            failed.append(True)
            raise RuntimeError('start marker acknowledgement lost')
        return result

    monkeypatch.setattr(registry, 'claim_workflow_start', lost_ack)
    send(chat, session, 'find', 'Find players', status=503)
    path = '/conversations/' + session['sessionId']
    before = stats(chat)
    ordinary = chat.client.get(path, headers=HEADERS).json()
    assert ordinary['status'] == ordinary['recoveryStatus'] == 'needsResolution'
    for _ in range(2):
        response = chat.client.get(path + '/observations', headers=HEADERS)
        assert response.status_code == 200
        assert response.json()['sessionStatus'] == ordinary['status']
        assert response.json()['active'] is False
    assert stats(chat) == before


def test_streamed_generation_uses_actual_sdk_deltas_and_retains_owner_filter(chat_client):
    chat=chat_client;sink=RunObservations();chat.host.observations=sink
    chat.host.config['conversation']['bundles'][0]['streaming']=True
    chat.restore();install_observation_routes(chat.client.app,sink)
    session=create(chat,'streamed-generation');before=stats(chat)['calls']
    reply=send(chat,session,'hello','Hello')
    assert reply['status']=='completed'
    path='/conversations/'+session['sessionId']+'/observations'
    response=chat.client.get(path,headers=HEADERS)
    trace=response.json()['generation'];call=trace['calls'][0]
    assert call['mode']=='streamed' and call['chunks']>1
    assert call['preview']==reply['answer']=='Preference recorded.'
    assert call['samples'][-1]['totalCharacters']==20
    assert call['firstOutputAt']>=call['start'] and call['end']>=call['lastOutputAt']
    assert chat.client.get(path,headers={'Authorization':'Bearer bob-token'}).status_code==404
    assert chat.client.get(path).status_code==401
    assert 'Hello' not in response.text and 'alice-token' not in response.text
    assert stats(chat)['calls']==before+1
    send(chat,session,'hello','Hello')
    assert stats(chat)['calls']==before+1


def test_stream_capture_does_not_preview_interpreter_or_tool_arguments(chat_client):
    chat=chat_client;sink=RunObservations();chat.host.observations=sink
    chat.host.config['conversation']['bundles'][0]['streaming']=True
    chat.restore();install_observation_routes(chat.client.app,sink)
    initial=create(chat,'streamed-tools');offered=send(chat,initial,'find','Find players')
    assert offered['pendingInteraction']['stepId']=='select'
    path='/conversations/'+initial['sessionId']+'/observations'
    trace=chat.client.get(path,headers=HEADERS).json()
    assert len(trace['generation']['calls'])==2
    assert trace['generation']['calls'][0]['preview']==''  # tool arguments never text
    assert trace['generation']['calls'][1]['preview']=='1. player-a\n2. player-b'
    selected=send(chat,offered,'select','the second result',reference=offered['pendingInteraction']['reference'])
    assert selected['pendingInteraction']['stepId']=='confirm-b'
    after=chat.client.get(path,headers=HEADERS).json()['generation']['calls']
    assert after[-1]['preview']=='' and after[-1]['chunks']==0


def test_optional_capture_failure_cannot_fail_or_redispatch_a_turn(chat_client):
    chat=chat_client
    class BrokenSink(RunObservations):
        def output(self,*args):raise RuntimeError('capture unavailable')
    chat.host.observations=BrokenSink()
    chat.host.config['conversation']['bundles'][0]['streaming']=True
    chat.restore()
    before=stats(chat)['calls'];initial=create(chat,'broken-stream-capture')
    assert send(chat,initial,'hello','Hello')['status']=='completed'
    assert stats(chat)['calls']==before+1


def test_launcher_stream_bindings_keep_tenant_and_retained_version_references_valid(chat_client):
    from lab_runner.chat import configure_conversations
    chat=chat_client
    settings=chat.host.config['conversation']
    settings['tenants']['tenant-a']['retained_versions']=['balanced-v1']
    configure_conversations(settings,model_url=chat.provider+'/v1',streaming=True)
    chat.restore()
    reply=send(chat,create(chat,'launcher-stream-versions'),'hello','Hello')
    assert reply['status']=='completed'


def test_generation_demo_exposes_chunks_while_the_real_sdk_is_still_running(chat_client):
    from concurrent.futures import ThreadPoolExecutor
    import time
    chat=chat_client;sink=RunObservations();chat.host.observations=sink
    chat.host.config['conversation']['bundles'][0]['streaming']=True
    chat.restore();initial=create(chat,'visible-generation')
    with ThreadPoolExecutor(max_workers=1) as worker:
        pending=worker.submit(send,chat,initial,'generation','Show generation')
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            calls=sink.snapshot(initial['sessionId'])['generation']['calls']
            if calls and calls[0]['chunks']>0:break
            time.sleep(.01)
        assert calls and calls[0]['chunks']>0 and not pending.done()
        reply=pending.result(timeout=15)
    assert reply['status']=='completed'
    assert len(reply['answer'])>100  # visible stream, unlike the old one-word demo


def test_one_request_local_allowance_can_admit_one_streamed_turn(chat_client):
    from types import SimpleNamespace
    from lab_runner.chat import configure_conversations
    chat=chat_client
    configure_conversations(chat.host.config['conversation'],model_url=chat.provider+'/v1',
        streaming=True,profile=SimpleNamespace(model='test-model'),maximum=1)
    chat.restore();before=stats(chat)['calls']
    reply=send(chat,create(chat,'one-request-stream'),'hello','Hello')
    assert reply['status']=='completed'
    assert stats(chat)['calls']==before+1

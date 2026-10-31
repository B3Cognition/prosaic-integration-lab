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

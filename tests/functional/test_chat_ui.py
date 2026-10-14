"""The public chat shell never relaxes authentication on conversation APIs."""
from tests.functional.test_conversation_journey import HEADERS


def test_chat_shell_is_public_but_conversation_data_stays_authenticated(chat_client):
    client = chat_client.client
    response = client.get('/chat')
    assert response.status_code == 200
    assert 'Prosaic Chat' in response.text
    assert 'Content-Security-Policy' in response.headers
    assert response.headers['cache-control'] == 'no-store'
    assert 'alice-token' not in response.text
    assert client.post('/conversations', json={}, headers={'Idempotency-Key': 'ui'}).status_code == 401
    result = client.post('/conversations', json={}, headers={**HEADERS, 'Idempotency-Key': 'ui'})
    assert result.status_code == 200
    assert client.get('/conversations/' + result.json()['sessionId'] + '/history').status_code == 401


def test_chat_public_exception_is_exact_get_only(chat_client):
    client = chat_client.client
    assert client.post('/chat', json={}).status_code == 401
    assert client.get('/chat/private').status_code == 401
    assert client.get('/chat?token=ignored').status_code == 200
    assert 'ignored' not in client.get('/chat?token=ignored').text

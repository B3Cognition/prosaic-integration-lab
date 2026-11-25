"""Authenticate and bound the actual Explorer HTTP boundary without model calls."""
import json

import pytest
from starlette.testclient import TestClient


ORIGIN = 'http://127.0.0.1:43123'
TOKEN = 'fixture-token-that-is-at-least-thirty-two-characters'
LAUNCH = 'fixture-launch-code-that-is-private'


class Host:
    def __init__(self):
        self.calls = []
        self.closed = False

    def status(self):
        return {'liveEnabled': True, 'runs': [], 'blocked': False}

    def submit(self, request_id, task, local_timeout_s=180):
        self.calls.append((request_id, task, local_timeout_s))
        return {'runId': 'a' * 32, 'state': 'running'}

    def get(self, run_id):
        if run_id != 'a' * 32:
            raise ValueError('not_found')
        return {'runId': run_id, 'state': 'running'}

    def cancel(self, run_id):
        self.calls.append(('cancel', run_id))
        return {'runId': run_id, 'state': 'uncertain'}

    def close(self):
        self.closed = True


@pytest.fixture
def surface(tmp_path):
    from lab_runner.explore.app import create_app
    web = tmp_path / 'web'
    web.mkdir()
    (web / 'index.html').write_text('<h1>Prosaic Explorer</h1>')
    (web / 'app.js').write_text('document.title="Prosaic"')
    host = Host()
    with TestClient(create_app(origin=ORIGIN, token=TOKEN, launch_code=LAUNCH,
                              coordinator=host, web_root=web), base_url=ORIGIN) as client:
        yield client, host
    assert host.closed


def headers(**extra):
    return {'Authorization': 'Bearer ' + TOKEN, 'Origin': ORIGIN, **extra}


def test_docs_and_reads_never_dispatch(surface):
    client, host = surface
    response = client.get('/')
    assert response.status_code == 200 and 'Prosaic Explorer' in response.text
    assert "script-src 'self'" in response.headers['content-security-policy']
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert client.get('/app.js').status_code == 200
    assert client.get('/api/status').status_code == 401
    assert client.get('/api/status', headers=headers()).status_code == 200
    assert not host.calls


def test_bootstrap_is_origin_checked_and_single_use(surface):
    client, _ = surface
    assert client.post('/api/bootstrap', headers={'X-Explorer-Launch': LAUNCH}).status_code == 403
    bad = {'Origin': ORIGIN, 'X-Explorer-Launch': 'wrong'}
    assert client.post('/api/bootstrap', headers=bad).status_code == 401
    good = {'Origin': ORIGIN, 'X-Explorer-Launch': LAUNCH}
    assert client.post('/api/bootstrap', headers=good).json() == {'token': TOKEN}
    assert client.post('/api/bootstrap', headers=good).status_code == 401


@pytest.mark.parametrize('origin', [None, 'https://attacker.invalid', 'null'])
def test_mutations_require_exact_origin(surface, origin):
    client, host = surface
    h = {'Authorization': 'Bearer ' + TOKEN}
    if origin is not None:
        h['Origin'] = origin
    assert client.post('/api/runs', headers=h, json={}).status_code == 403
    assert not host.calls


@pytest.mark.parametrize('body', [
    {}, {'requestId': 'r', 'task': 'invoice-sql', 'confirmed': True},
    {'requestId': 'a' * 32, 'task': '../secret', 'confirmed': True},
    {'requestId': 'a' * 32, 'task': [], 'confirmed': True},
    {'requestId': 'a' * 32, 'task': {}, 'confirmed': True},
    {'requestId': 'a' * 32, 'task': 'invoice-sql', 'confirmed': False},
    {'requestId': 'a' * 32, 'task': 'invoice-sql', 'confirmed': True, 'config': '/secret'},
    {'requestId': 'a' * 32, 'task': 'invoice-sql', 'confirmed': True, 'localTimeoutSeconds': True},
    {'requestId': 'a' * 32, 'task': 'invoice-sql', 'confirmed': True, 'localTimeoutSeconds': 301},
])
def test_browser_cannot_supply_extra_authority(surface, body):
    client, host = surface
    assert client.post('/api/runs', headers=headers(), json=body).status_code == 422
    assert not host.calls


def test_explicit_confirmed_run_and_cancel(surface):
    client, host = surface
    body = {'requestId': 'b' * 32, 'task': 'invoice-sql', 'confirmed': True, 'localTimeoutSeconds': 240}
    assert client.post('/api/runs', headers=headers(), json=body).status_code == 202
    assert host.calls == [('b' * 32, 'invoice-sql', 240)]
    assert client.get('/api/runs/' + 'a' * 32, headers=headers()).status_code == 200
    assert client.post('/api/runs/' + 'a' * 32 + '/cancel', headers=headers()).status_code == 200
    assert host.calls[-1] == ('cancel', 'a' * 32)


def test_oversize_duplicate_keys_wrong_host_and_private_errors(surface):
    client, host = surface
    h = headers(**{'Content-Type': 'application/json'})
    assert client.post('/api/runs', headers=h, content='x' * 4097).status_code == 413
    assert client.post('/api/runs', headers=h, content='{"task":"a","task":"b"}').status_code == 422
    assert client.get('/', headers={'Host': 'attacker.invalid'}).status_code == 400
    def fail(*args, **kwargs):
        raise ValueError('private provider error /secret/token')
    host.submit = fail
    body = {'requestId': 'c' * 32, 'task': 'invoice-sql', 'confirmed': True}
    response = client.post('/api/runs', headers=headers(), json=body)
    assert 'secret' not in response.text and response.status_code == 409


def test_default_application_has_no_live_authority(tmp_path):
    from lab_runner.explore.app import create_app
    with TestClient(create_app(origin=ORIGIN, token=TOKEN, launch_code=LAUNCH), base_url=ORIGIN) as client:
        assert client.get('/api/status', headers=headers()).json()['liveEnabled'] is False
        body = {'requestId': 'c' * 32, 'task': 'release-brief', 'confirmed': True}
        assert client.post('/api/runs', headers=headers(), json=body).status_code == 403

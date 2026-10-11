"""Real loopback HTTP and released Runtime: no copied engine or transport patch."""
import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from lab_runner import model


@pytest.fixture
def provider():
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0)); listener.listen(128)
    url = 'http://127.0.0.1:' + str(listener.getsockname()[1])
    server = uvicorn.Server(uvicorn.Config(model.app, log_level='critical', lifespan='off'))
    worker = threading.Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started:
            assert time.monotonic() < deadline
            time.sleep(.01)
        yield url
    finally:
        if server.started: httpx.post(url + '/control', json={}, timeout=2).raise_for_status()
        server.should_exit = True; worker.join(5); listener.close()
        assert not worker.is_alive()


def test_reset_really_closes_accepted_http_response_before_body(provider):
    httpx.post(provider + '/control', json={'fault': 'reset'}, timeout=2).raise_for_status()
    before = httpx.get(provider + '/stats', timeout=2).json()['calls']
    with pytest.raises(httpx.RemoteProtocolError):
        httpx.post(provider + '/v1/chat/completions', json={}, timeout=2)
    assert httpx.get(provider + '/stats', timeout=2).json()['calls'] == before + 1


@pytest.mark.parametrize('phase', ['first', 'post_tool'])
@pytest.mark.parametrize('fault', ['reset', 'truncated_json', '429', '503', 'malformed_shape', 'slow'])
def test_accepted_provider_fault_retains_unknown_usage_and_does_not_retry(provider, phase, fault):
    from prosaic_runtime import CustomTool, EndpointConfig, ProsaicArtifact, ProsaicRuntime, RunPolicy, RuntimeConfig
    from prosaic_runtime.accounting import MemoryRecorder
    recorder = MemoryRecorder()
    effects = []
    tool = CustomTool('fixture_apply', 'Synthetic operation', {'type': 'object', 'properties': {
        'amount': {'type': 'integer'}}, 'required': ['amount'], 'additionalProperties': False},
        lambda arguments: effects.append(arguments) or {'applied': True}, 'fixture-v1')
    config = RuntimeConfig({'fixture': EndpointConfig(provider + '/v1', 'test-model', features={'streaming': False})},
        {}, 'fixture', allowed_tools=frozenset({'fixture_apply'}))
    artifact = ProsaicArtifact.from_inspection({'id': 'fault.md', 'type': 'subagent',
        'frontmatter': {'tools': ['fixture_apply']}, 'body': '{{args}}'})
    runtime = ProsaicRuntime(config, custom_tools={'fixture_apply': tool}, accounting=recorder)
    httpx.post(provider + '/control', json={'scenario': 'native_effect', 'fault': fault,
        'fault_phase': phase, 'fault_delay_s': 1.0}, timeout=2).raise_for_status()
    before = httpx.get(provider + '/stats', timeout=2).json()
    began = time.monotonic()
    result = runtime.run(artifact, json.dumps({'request': {'entity_id': 'fault-case'}}),
        policy=RunPolicy(allowed_tools=frozenset({'fixture_apply'}), timeout_s=.5,
            max_provider_requests=2, max_tool_calls=1))
    assert result.exit_code != 0
    assert time.monotonic() - began < 2
    expected_calls = 1 if phase == 'first' else 2
    after = httpx.get(provider + '/stats', timeout=2).json()
    assert after['calls'] == before['calls'] + expected_calls
    assert after['fault_acceptances'][fault] == before['fault_acceptances'][fault] + 1
    assert len(recorder.intents) == len(recorder.observations) == expected_calls
    observations = list(recorder.observations.values())
    assert observations[-1]['usage']['status'] in {'unknown', 'untrusted'}
    assert observations[-1]['usage']['total_tokens'] is None
    assert len(effects) == (0 if phase == 'first' else 1)
    if phase == 'post_tool': assert observations[0]['usage']['total_tokens'] == 125
    httpx.post(provider + '/control', json={'scenario': 'native_effect'}, timeout=2).raise_for_status()
    healthy = runtime.run(artifact, json.dumps({'request': {'entity_id': 'healthy-next'}}),
        policy=RunPolicy(allowed_tools=frozenset({'fixture_apply'}), timeout_s=2,
            max_provider_requests=2, max_tool_calls=1))
    assert healthy.exit_code == 0
    assert httpx.get(provider + '/stats', timeout=2).json()['calls'] == after['calls'] + 2

"""Fault selection must be bounded and preserve independent acceptance evidence."""
import pytest
from fastapi.testclient import TestClient

from lab_runner import model


@pytest.fixture
def fixture():
    with TestClient(model.app) as client:
        client.post('/control', json={}).raise_for_status()
        yield client
        client.post('/control', json={}).raise_for_status()


@pytest.mark.parametrize('fault,status', [('truncated_json', 200), ('429', 429),
    ('503', 503), ('malformed_shape', 200)])
def test_accepted_fault_is_counted_before_invalid_response(fixture, fault, status):
    before = fixture.get('/stats').json()
    configured = fixture.post('/control', json={'fault': fault})
    assert configured.status_code == 200
    response = fixture.post('/v1/chat/completions', json={})
    assert response.status_code == status
    after = fixture.get('/stats').json()
    assert after['calls'] == before['calls'] + 1
    assert after['fault_acceptances'][fault] == before['fault_acceptances'][fault] + 1
    assert b'usage' not in response.content
    if fault == 'truncated_json':
        with pytest.raises(ValueError): response.json()
    elif fault == 'malformed_shape':
        assert response.json() == {'choices': []}


def test_post_tool_fault_waits_for_actual_tool_message(fixture):
    before = fixture.get('/stats').json()['fault_acceptances']['503']
    assert fixture.post('/control', json={'fault': '503', 'fault_phase': 'post_tool'}).status_code == 200
    assert fixture.post('/v1/chat/completions', json={}).status_code == 200
    assert fixture.get('/stats').json()['fault_acceptances']['503'] == before
    assert fixture.post('/v1/chat/completions', json={'messages': [
        {'role': 'tool', 'content': 'PRIVATE_SENTINEL'}]}).status_code == 503
    assert fixture.get('/stats').json()['fault_acceptances']['503'] == before + 1
    assert 'PRIVATE_SENTINEL' not in fixture.get('/stats').text


@pytest.mark.parametrize('settings', [{'fault': 'arbitrary'}, {'fault_phase': 'second'},
    {'fault_delay_s': 41}, {'fault_delay_s': -1}, {'fault_delay_s': True},
    {'accepted_wait_s': 61}, {'accepted_wait_s': 19}, {'accepted_wait_s': True}])
def test_fault_controls_reject_unbounded_or_unknown_settings(fixture, settings):
    assert fixture.post('/control', json=settings).status_code == 422


def test_accepted_wait_control_can_hold_through_lease_expiry(fixture):
    assert fixture.post('/control', json={'accepted_gate': True, 'accepted_wait_s': 60}).status_code == 200
    assert not model.receipt_gate.is_set()
    assert fixture.post('/control', json={}).status_code == 200
    assert model.receipt_gate.is_set()

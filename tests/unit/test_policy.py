import pytest

from prosaic_integration_lab.identity import authenticate
from prosaic_integration_lab.views import public_run
from prosaic_integration_lab.metadata import canonical_request


def test_authentication_uses_only_host_mapping():
    mapping = {'token': {'tenant_id': 'a', 'actor_id': 'alice', 'billing_account_id': 'payer-a'}}
    assert authenticate('Bearer token', mapping).actor_id == 'alice'


@pytest.mark.parametrize('header', [None, '', 'Bearer unknown', 'Basic token'])
def test_invalid_authentication_is_denied(header):
    with pytest.raises(ValueError):
        authenticate(header, {'token': {}})


def test_projection_does_not_expose_raw_state():
    state = {'status': 'waiting', 'current': 'approval', 'inputs': {'task': 'PRIVATE'},
             'history': [{'secret': 'PRIVATE'}], 'outputs': {'author': {'result': 'PRIVATE'}},
             'question': 'PRIVATE', 'choices': ['approve', 'reject']}
    public = public_run('run', state, 'revision')
    assert public == {'run_id': 'run', 'status': 'waiting', 'current_step': 'approval',
                      'revision': 'revision', 'choices': ['approve', 'reject'], 'recovery_status': None}
    assert 'PRIVATE' not in str(public)


def test_canonical_request_ignores_object_key_order():
    assert canonical_request({'task': 'x', 'workflow': 'approval'}) == canonical_request({'workflow': 'approval', 'task': 'x'})


@pytest.mark.parametrize('payload', [{'task': float('nan')}, {'task': 'x' * 9000}, {'task': {'deep': []}}])
def test_unbounded_or_nonfinite_request_is_rejected(payload):
    with pytest.raises(ValueError):
        canonical_request(payload)

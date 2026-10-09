import uuid

import httpx
import pytest

from test_approval import headers, start


@pytest.mark.parametrize('actor', ['bob', 'carol'])
def test_nonowner_cannot_read_resume_or_query_usage(lab, actor):
    run = start(lab).json()
    path = '/runs/' + run['run_id']
    for suffix in ('', '/usage'):
        response = httpx.get(lab['b'] + path + suffix, headers=headers(lab, actor), timeout=10)
        assert response.status_code == 404
        assert response.json() == {'detail': 'not_found'}
    response = httpx.post(lab['b'] + path + '/resume', headers=headers(lab, actor),
                         json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
    assert response.status_code == 404


def test_missing_auth_denied_and_body_identity_override_rejected(lab):
    assert httpx.post(lab['a'] + '/runs', json={'task': 'x'}, timeout=10).status_code == 401
    for field in ('tenant_id', 'actor_id', 'billing_account_id', 'namespace', 'model', 'base_url'):
        response = httpx.post(lab['a'] + '/runs', headers={**headers(lab), 'Idempotency-Key': uuid.uuid4().hex},
                             json={'task': 'x', field: 'spoofed'}, timeout=10)
        assert response.status_code == 422

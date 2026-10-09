from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import httpx

from test_approval import headers, start


def count(lab):
    return httpx.get(lab['model'] + '/stats', timeout=5).json()['calls']


def test_synthetic_dispatch_has_exact_accounting_and_no_call_on_resume(lab):
    before = count(lab)
    response = start(lab, workflow='synthetic')
    assert response.status_code == 200
    run = response.json()
    assert run['status'] == 'waiting'
    path = '/runs/' + run['run_id']
    usage = httpx.get(lab['b'] + path + '/usage', headers=headers(lab), timeout=10).json()
    assert usage['total_calls'] == 1
    assert usage['complete_calls'] == 1
    assert usage['fully_costed'] is True
    assert usage['billing_eligible'] is False
    assert Decimal(usage['estimated_amounts']['USD']) == Decimal('0.00037')
    assert count(lab) == before + 1
    done = httpx.post(lab['b'] + path + '/resume', headers=headers(lab),
                     json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
    assert done.status_code == 200
    assert done.json()['status'] == 'completed'
    assert count(lab) == before + 1


def test_parallel_users_have_owner_scoped_usage(lab):
    before = count(lab)
    # Two execution slots per replica; spread three users across A/B.
    def run(actor):
        alternate = {**lab, 'a': lab['b']} if actor == 'carol' else lab
        response = start(alternate, actor=actor, workflow='synthetic', task=f'PRIVATE-{actor}')
        assert response.status_code == 200
        return actor, response.json()
    with ThreadPoolExecutor(max_workers=3) as pool:
        runs = list(pool.map(run, ['alice', 'bob', 'carol']))
    for actor, run in runs:
        assert run['status'] == 'waiting'
        usage = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab, actor), timeout=10)
        assert usage.status_code == 200
        assert usage.json()['total_calls'] == 1
        assert 'PRIVATE-' not in str(run)
    assert count(lab) == before + 3


def test_denied_synthetic_requests_do_not_dispatch(lab):
    run = start(lab, workflow='synthetic').json()
    before = count(lab)
    path = '/runs/' + run['run_id']
    response = httpx.post(lab['b'] + path + '/resume', headers=headers(lab, 'carol'),
                         json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
    assert response.status_code == 404
    assert count(lab) == before

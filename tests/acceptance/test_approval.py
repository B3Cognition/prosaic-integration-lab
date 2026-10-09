import uuid

import httpx


def headers(lab, actor='alice'):
    token = next(token for token, principal in lab['principals'].items() if principal['actor_id'] == actor)
    return {'Authorization': 'Bearer ' + token}


def start(lab, actor='alice', workflow='approval', key=None, task='synthetic private request'):
    return httpx.post(lab['a'] + '/runs', headers={**headers(lab, actor), 'Idempotency-Key': key or uuid.uuid4().hex},
                      json={'workflow': workflow, 'task': task}, timeout=30)


def test_a_start_b_read_resume_and_stale_revision(lab):
    response = start(lab)
    assert response.status_code == 200
    run = response.json()
    assert run['status'] == 'waiting'
    path = '/runs/' + run['run_id']
    viewed = httpx.get(lab['b'] + path, headers=headers(lab), timeout=10)
    assert viewed.status_code == 200
    assert viewed.json()['revision'] == run['revision']
    rejected = httpx.post(lab['b'] + path + '/resume', headers=headers(lab),
                         json={'choice': 'approve', 'expected_revision': 'stale'}, timeout=10)
    assert rejected.status_code == 409
    completed = httpx.post(lab['b'] + path + '/resume', headers=headers(lab),
                          json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
    assert completed.status_code == 200
    assert completed.json()['status'] == 'completed'
    usage = httpx.get(lab['b'] + path + '/usage', headers=headers(lab), timeout=10)
    assert usage.status_code == 200
    assert usage.json()['total_calls'] == 0
    assert 'synthetic private request' not in str(completed.json())


def test_reject_pause_on_other_replica(lab):
    run = start(lab, 'bob').json()
    response = httpx.post(lab['b'] + '/runs/' + run['run_id'] + '/resume', headers=headers(lab, 'bob'),
                         json={'choice': 'reject', 'expected_revision': run['revision']}, timeout=10)
    assert response.status_code == 200
    assert response.json()['status'] == 'rejected'

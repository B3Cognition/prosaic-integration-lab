from concurrent.futures import ThreadPoolExecutor
import uuid

import httpx

from test_approval import headers, start


def test_parallel_same_key_has_one_run_and_changed_request_conflicts(lab):
    key = uuid.uuid4().hex
    def submit(url):
        return httpx.post(url + '/runs', headers={**headers(lab), 'Idempotency-Key': key},
                          json={'task': 'same', 'workflow': 'approval'}, timeout=20)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, [lab['a'], lab['b']]))
    assert all(response.status_code == 200 for response in responses)
    assert len({response.json()['run_id'] for response in responses}) == 1
    assert start(lab, key=key, task='different').status_code == 409


def test_same_key_different_owners_have_different_runs(lab):
    key = uuid.uuid4().hex
    alice = start(lab, key=key).json()
    bob = start(lab, actor='bob', key=key).json()
    assert alice['run_id'] != bob['run_id']

from concurrent.futures import ThreadPoolExecutor
import time
import httpx

from test_approval import start
from test_accounting import count


def test_two_admitted_calls_reject_excess_without_queueing(lab):
    before = count(lab)
    response = httpx.post(lab['model'] + '/control', json={'blocked': True}, timeout=5)
    assert response.status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(start, lab, 'alice', 'synthetic')
        second = pool.submit(start, lab, 'bob', 'synthetic')
        try:
            deadline = time.monotonic() + 5
            while count(lab) < before + 2:
                assert time.monotonic() < deadline, 'admission gate not reached'
                time.sleep(0.02)
            excess = start(lab, 'carol', 'synthetic')
            assert excess.status_code == 503
            assert excess.json() == {'detail': 'capacity_exhausted'}
            assert count(lab) == before + 2
            # B has independent capacity despite A's saturation.
            alternate = {**lab, 'a': lab['b']}
            assert start(alternate, 'carol', 'approval').status_code == 200
        finally:
            httpx.post(lab['model'] + '/control', json={'blocked': False}, timeout=5)
        assert first.result(timeout=20).json()['status'] == 'waiting'
        assert second.result(timeout=20).json()['status'] == 'waiting'
    assert start(lab, 'carol', 'synthetic').json()['status'] == 'waiting'


def test_same_run_concurrent_approval_only_one_advances(lab):
    from test_approval import headers
    run = start(lab).json()
    def resume(url):
        return httpx.post(url + '/runs/' + run['run_id'] + '/resume', headers=headers(lab),
                          json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(resume, [lab['a'], lab['b']]))
    assert sorted(r.status_code for r in responses) == [200, 409]

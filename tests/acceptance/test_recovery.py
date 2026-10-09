from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
import uuid

import httpx
import psycopg

from lab_runner.manifest import validate_resource
from lab_runner.stack import command
from test_approval import start, headers
from test_accounting import count


def fixture_identity(lab):
    return json.loads(Path(lab['fixture_manifest']).read_text())


def mutate_replica(lab, action, name='a'):
    manifest = fixture_identity(lab)
    identifier = manifest['replica_ids'][name]
    state = json.loads(command(manifest['engine'], 'inspect', identifier))[0]
    validate_resource(state, identifier, manifest['owner'])
    command(manifest['engine'], action, identifier)
    if action == 'start':
        state = json.loads(command(manifest['engine'], 'inspect', identifier))[0]
        validate_resource(state, identifier, manifest['owner'])
        port = state['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort']
        lab[name] = f'http://127.0.0.1:{port}'
        manifest['endpoints'][name] = lab[name]
        path = Path(lab['fixture_manifest'])
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(path)


def wait_for(predicate, timeout=35):
    deadline = time.monotonic() + timeout
    while True:
        try:
            value = predicate()
        except httpx.HTTPError:
            value = None
        if value:
            return value
        assert time.monotonic() < deadline, 'observable gate deadline expired'
        time.sleep(0.05)


def crash_during(lab, control, observed):
    key = uuid.uuid4().hex
    assert httpx.post(lab['model'] + '/control', json=control, timeout=5).status_code == 200
    def submit():
        try:
            return start(lab, workflow='synthetic', key=key)
        except httpx.HTTPError:
            return None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(submit)
        try:
            wait_for(observed, timeout=5)
            with psycopg.connect(lab['app_dsn']) as conn:
                run_id = conn.execute('SELECT run_id FROM lab_app.runs WHERE actor_id=%s AND idempotency_key=%s', ('alice', key)).fetchone()[0]
            mutate_replica(lab, 'kill')
        finally:
            httpx.post(lab['model'] + '/control', json={}, timeout=5)
        future.result(timeout=10)
    mutate_replica(lab, 'start')
    wait_for(lambda: httpx.get(lab['a'] + '/readyz', timeout=2).status_code == 200)
    return run_id


def resume_after_lease(lab, run_id):
    path = '/runs/' + run_id
    def attempt():
        viewed = httpx.get(lab['b'] + path, headers=headers(lab), timeout=5).json()
        response = httpx.post(lab['b'] + path + '/resume', headers=headers(lab),
                             json={'expected_revision': viewed['revision']}, timeout=10)
        if response.status_code == 409:
            assert response.json()['detail'] == 'run_busy'
            return None
        assert response.status_code == 200
        return response.json()
    return wait_for(attempt)


def test_loss_after_receipt_recovers_without_another_dispatch(lab):
    before = count(lab)
    accepted = httpx.get(lab['model'] + '/stats', timeout=5).json().get('accepted_events', 0)
    run_id = crash_during(lab, {'accepted_gate': True},
                         lambda: httpx.get(lab['model'] + '/stats', timeout=5).json().get('accepted_events', 0) > accepted)
    recovered = resume_after_lease(lab, run_id)
    assert recovered['status'] == 'waiting'
    assert count(lab) == before + 1
    usage = httpx.get(lab['b'] + '/runs/' + run_id + '/usage', headers=headers(lab), timeout=5).json()
    assert usage['total_calls'] == 1


def test_missing_receipt_blocks_then_requires_explicit_retry(lab):
    before = count(lab)
    run_id = crash_during(lab, {'blocked': True}, lambda: count(lab) == before + 1)
    recovered = resume_after_lease(lab, run_id)
    assert recovered['status'] == 'blocked'
    assert recovered['recovery_status'] == 'retry_consent_required'
    assert count(lab) == before + 1
    response = httpx.post(lab['b'] + '/runs/' + run_id + '/resume', headers=headers(lab),
                         json={'expected_revision': recovered['revision'], 'retry_interrupted': True}, timeout=20)
    assert response.status_code == 200
    assert response.json()['status'] == 'waiting'
    assert count(lab) == before + 2
    usage = httpx.get(lab['b'] + '/runs/' + run_id + '/usage', headers=headers(lab), timeout=5).json()
    assert usage['total_calls'] == 2
    assert usage['unresolved_calls'] == 1
    assert usage['fully_costed'] is False

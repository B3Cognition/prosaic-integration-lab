"""Required real-stack native provider faults and live SQL lease fencing."""
from concurrent.futures import ThreadPoolExecutor
import json
import time
import uuid

import httpx
import psycopg
import pytest

from lab_runner.accounting_report import accounting_snapshot
from lab_runner.manifest import validate_resource
from lab_runner.native_faults import partition_worker_a
from lab_runner.native_scenarios import control, calls, effect_proposal, owned
from lab_runner.stack import command
from test_approval import headers
from test_native_workflows import http, propose, start, approved_proposal
from test_recovery import wait_for


FAULTS = ('reset', 'truncated_json', '429', '503', 'malformed_shape', 'slow')


@pytest.fixture(autouse=True)
def release_faults(lab):
    control(lab)
    yield
    control(lab)


def provider_stats(lab):
    response = httpx.get(lab['model'] + '/stats', timeout=5)
    response.raise_for_status()
    return response.json()


def effect_rows(lab, key):
    with psycopg.connect(lab['app_dsn']) as connection:
        domain = connection.execute('SELECT namespace,business_key,amount FROM lab_fixture.effects '
            'WHERE business_key=%s ORDER BY namespace', (key,)).fetchall()
        journal = connection.execute('SELECT operation_namespace,operation_key,state,outcome '
            'FROM lab_app.tool_operations WHERE operation_key=%s ORDER BY operation_namespace', (key,)).fetchall()
    return domain, journal


def sanitized(lab, *views):
    text = json.dumps(views)
    assert all(secret not in text for secret in lab['principals'])
    assert all(lab[name] not in text for name in ('app_dsn', 'harness_dsn', 'accounting_dsn'))
    assert 'PRIVATE_PROVIDER_SENTINEL' not in text
    assert 'raw_response_headers' not in text and 'invocations' not in text


@pytest.mark.parametrize('phase', ['first', 'post_tool'], ids=['first', 'post-tool'])
@pytest.mark.parametrize('fault', FAULTS, ids=FAULTS)
def test_native_accepted_transport_fault_never_redispatches_or_duplicates_effect(lab, phase, fault):
    proposal = propose(lab, effect_proposal())
    key = uuid.uuid4().hex
    control(lab, scenario='native_effect', fault=fault, fault_phase=phase,
        result_text='PRIVATE_PROVIDER_SENTINEL')
    before = provider_stats(lab)
    began = time.monotonic()
    run = start(lab, proposal, entity=key)
    assert time.monotonic() - began < 35
    assert run['status'] == 'blocked'
    expected = 1 if phase == 'first' else 2
    after = provider_stats(lab)
    assert after['calls'] == before['calls'] + expected
    assert after['fault_acceptances'][fault] == before['fault_acceptances'][fault] + 1
    usage = http(lab, 'GET', '/runs/' + run['run_id'] + '/usage', worker='b')
    assert usage['total_calls'] == expected
    assert usage['complete_calls'] == expected - 1
    assert usage['unresolved_calls'] == 1
    assert usage['fully_costed'] is False and usage['billing_eligible'] is False
    if phase == 'first':assert usage['estimated_amounts'] == {}
    domain, journal = effect_rows(lab, key)
    namespace = next(bundle['operation_namespace'] for bundle in lab['native']['bundles']
        if 'tenant-a' in bundle['policies'])
    assert domain == ([] if phase == 'first' else [(namespace, key, 1)])
    assert journal == ([] if phase == 'first' else [
        (namespace, key, 'completed', {'status': 'ok', 'result': {'applied': True}})])
    # Receipt/usage reads and both resume choices lack authority to dispatch.
    for retry in (False, True):
        run = http(lab, 'POST', '/runs/' + run['run_id'] + '/resume', worker='b',
            json={'expected_revision': run['revision'], 'retry_interrupted': retry})
        assert run['status'] == 'blocked'
    assert provider_stats(lab)['calls'] == after['calls']
    assert effect_rows(lab, key) == (domain, journal)
    assert accounting_snapshot(http(lab, 'GET', '/runs/' + run['run_id'] + '/usage', worker='b')) == accounting_snapshot(usage)
    sanitized(lab, run, usage)
    # An unrelated run recovers after clearing the fixture, in the same worker.
    control(lab, scenario='native_effect')
    healthy_key = uuid.uuid4().hex
    healthy = start(lab, proposal, entity=healthy_key, worker='a')
    assert healthy['status'] == 'completed'
    assert calls(lab) == after['calls'] + 2
    assert effect_rows(lab, key) == (domain, journal)
    assert effect_rows(lab, healthy_key)[0] == [(namespace, healthy_key, 1)]
    healthy_usage = http(lab, 'GET', '/runs/' + healthy['run_id'] + '/usage')
    assert healthy_usage['total_calls'] == healthy_usage['complete_calls'] == 2
    assert healthy_usage['unresolved_calls'] == 0
    sanitized(lab, healthy, healthy_usage)


def lease(lab, run_id):
    with psycopg.connect(lab['harness_dsn']) as connection:
        return connection.execute('SELECT owner,generation,expires_at,expires_at <= pg_catalog.clock_timestamp() '
            'FROM prosaic_harness.leases WHERE namespace=%s AND run_id=%s',
            (lab['namespace'], run_id)).fetchone()


def sql_snapshot(lab, run_id):
    with psycopg.connect(lab['harness_dsn']) as connection:
        row = connection.execute('SELECT revision,document FROM prosaic_harness.runs '
            'WHERE namespace=%s AND run_id=%s', (lab['namespace'], run_id)).fetchone()
        receipts = connection.execute('SELECT invocation_id,sha256,document FROM prosaic_harness.receipts '
            'WHERE namespace=%s AND run_id=%s ORDER BY invocation_id', (lab['namespace'], run_id)).fetchall()
    return row, receipts


def live_worker(lab, identifier):
    manifest = owned(lab)
    state = json.loads(command(manifest['engine'], 'inspect', identifier))[0]
    validate_resource(state, identifier, manifest['owner'])
    assert state['State']['Running'] is True
    return state['State']['Pid'], state['State']['StartedAt']


def test_native_live_sql_partition_takeover_fences_late_a_and_allows_fresh_session(lab):
    with partition_worker_a(lab) as proxy:
        manifest = owned(lab)
        identifier = manifest['replica_ids']['a']
        alive = live_worker(lab, identifier)
        b_identifier = manifest['replica_ids']['b']
        proposal = propose(lab, approved_proposal())
        key = uuid.uuid4().hex
        initial = provider_stats(lab)
        control(lab, scenario='native', accepted_gate=True, accepted_wait_s=60)
        run_id = None
        with ThreadPoolExecutor(max_workers=2) as pool:
            def submit():
                return httpx.post(lab['a'] + '/native-runs', headers={**headers(lab), 'Idempotency-Key': key},
                    json={'proposal_id': proposal['proposal_id'], 'inputs': {'entity_id': key}}, timeout=75)
            a = pool.submit(submit)
            try:
                wait_for(lambda: provider_stats(lab)['accepted_events'] == initial['accepted_events'] + 1, timeout=10)
                with psycopg.connect(lab['app_dsn']) as connection:
                    run_id = connection.execute('SELECT run_id FROM lab_app.runs WHERE idempotency_key=%s', (key,)).fetchone()[0]
                a_lease = lease(lab, run_id)
                assert a_lease[0] is not None and a_lease[3] is False
                durable = sql_snapshot(lab, run_id)
                assert len(durable[1]) == 1
                assert proxy.stats()['active'] > 0
                blocked = proxy.control(True)
                assert blocked['blocked'] is True and blocked['active'] == 0
                assert blocked['closed'] > 0
                assert httpx.get(lab['a'] + '/readyz', timeout=10).status_code == 503
                # SQL time, not a guessed sleep, proves the original lease expired.
                wait_for(lambda: lease(lab, run_id)[3] is True, timeout=25)
                assert live_worker(lab, identifier) == alive
                assert httpx.get(lab['a'] + '/healthz', timeout=3).status_code == 200
                def recover():
                    run = http(lab, 'GET', '/runs/' + run_id, worker='b')
                    return httpx.post(lab['b'] + '/runs/' + run_id + '/resume', headers=headers(lab),
                        json={'expected_revision': run['revision']}, timeout=50)
                b = pool.submit(recover)
                def takeover():
                    current = lease(lab, run_id)
                    return current if current[1] > a_lease[1] and current[0] not in {None, a_lease[0]} else None
                recovered_lease = wait_for(takeover, timeout=10)
                assert recovered_lease[3] is False
                assert proxy.stats()['blocked'] is True and proxy.stats()['active'] == 0
                assert owned(lab)['replica_ids']['b'] == b_identifier
                proxy.control(False)
                control(lab, scenario='native')
                response = b.result(timeout=20)
                assert response.status_code == 200
                recovered = response.json()
                assert recovered['status'] == 'waiting'
                late = a.result(timeout=15)
                assert late.status_code == 503
                assert late.json()['detail'] == 'lease_lost'
                assert live_worker(lab, identifier) == alive
                assert owned(lab)['replica_ids']['a'] == identifier
                assert lease(lab, run_id)[1] == recovered_lease[1]
                final = sql_snapshot(lab, run_id)
                assert final[0][0] > durable[0][0]
                assert set(durable[1]) <= set(final[1])
                assert len(final[1]) == 2
                assert http(lab, 'GET', '/runs/' + run_id, worker='a') == recovered
                assert sql_snapshot(lab, run_id) == final
                assert calls(lab) == initial['calls'] + 2
                usage = http(lab, 'GET', '/runs/' + run_id + '/usage', worker='b')
                assert usage['total_calls'] == usage['complete_calls'] == 2 and usage['unresolved_calls'] == 0
                sanitized(lab, recovered, usage, late.json())
                # Same live A process must release the failed session's capacity.
                healthy = start(lab, proposal, entity=uuid.uuid4().hex, worker='a')
                assert healthy['status'] == 'waiting'
                assert lease(lab, healthy['run_id'])[1] > 0
                assert calls(lab) == initial['calls'] + 4
                assert live_worker(lab, identifier) == alive
                assert sql_snapshot(lab, run_id) == final
            finally:
                proxy.control(False)
                control(lab, scenario='native')
            a.result(timeout=15)

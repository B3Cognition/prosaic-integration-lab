"""Production properties: failures are findings, not expected-pass lab promises."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import socket
import shutil
import sys
import uuid

import httpx
import psycopg
from psycopg import sql
import pytest
from prosaic_runtime import AccountingError
from prosaic_runtime import ExecutionContext, RateCard
from prosaic_harness import Harness, Workflow
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime_postgres import PostgresRecorder
import yaml

from lab_runner.manifest import validate_resource
from lab_runner.stack import command
from test_approval import headers, start
from test_accounting import count
from test_recovery import wait_for


def replica_state(lab, replica='a'):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['replica_ids'][replica]
    state = json.loads(command(manifest['engine'], 'inspect', identifier))[0]
    validate_resource(state, identifier, manifest['owner'])
    return manifest, identifier, state


def test_unauthenticated_partial_post_is_rejected_before_waiting_for_body(lab):
    url = httpx.URL(lab['a'])
    with socket.create_connection((url.host, url.port), timeout=2) as connection:
        connection.settimeout(1)
        connection.sendall(b'POST /runs HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{')
        try:
            response = connection.recv(1024)
        except socket.timeout:
            pytest.fail('unauthenticated partial body held request open beyond rejection deadline')
        assert response.startswith(b'HTTP/1.1 401')


def test_service_container_runs_as_nonroot(lab):
    manifest, identifier, _ = replica_state(lab)
    effective_uid = command(manifest['engine'], 'exec', identifier, 'python', '-c', 'import os; print(os.geteuid())')
    assert effective_uid != '0', 'service container runs as root'


def test_service_assets_are_on_readonly_root_filesystem(lab):
    _, _, state = replica_state(lab)
    assert state['HostConfig']['ReadonlyRootfs'] is True, 'workflow assets live on a writable container root'


@pytest.mark.parametrize('payload', [[], None, {'task': 7}, {'task': 'x', 'workflow': '../private'},
    {'task': 'x', 'billingAccountId': 'spoof'}, {'task': 'x', 'retry_interrupted': True}])
def test_bad_start_input_never_dispatches(lab, payload):
    before = count(lab)
    response = httpx.post(lab['a'] + '/runs', content=json.dumps(payload),
        headers={**headers(lab), 'Idempotency-Key': uuid.uuid4().hex, 'Content-Type': 'application/json'}, timeout=5)
    assert response.status_code == 422
    assert response.json() == {'detail': 'invalid_request'}
    assert count(lab) == before


def test_body_and_idempotency_limits_never_dispatch(lab):
    before = count(lab)
    for replica in ('a', 'b'):
        response = httpx.post(lab[replica] + '/runs', content='x' * 8193,
            headers={**headers(lab), 'Idempotency-Key': uuid.uuid4().hex}, timeout=5)
        assert response.status_code == 413
        response = httpx.post(lab[replica] + '/runs', json={'task': 'x'},
            headers={**headers(lab), 'Idempotency-Key': 'x' * 129}, timeout=5)
        assert response.status_code == 422
    assert count(lab) == before


def test_identical_keys_are_scoped_to_owner_and_never_redispatch_after_completion(lab):
    before = count(lab)
    key = uuid.uuid4().hex
    run_ids = []
    for actor in ('alice', 'bob', 'carol'):
        response = start(lab, actor, 'synthetic', key=key)
        assert response.status_code == 200
        run = response.json()
        run_ids.append(run['run_id'])
        completed = httpx.post(lab['b'] + '/runs/' + run['run_id'] + '/resume', headers=headers(lab, actor),
            json={'choice': 'approve', 'expected_revision': run['revision']}, timeout=10)
        assert completed.status_code == 200
        duplicate = start({**lab, 'a': lab['b']}, actor, 'synthetic', key=key)
        assert duplicate.status_code == 200
        assert duplicate.json()['status'] == 'completed'
        assert duplicate.json()['run_id'] == run['run_id']
    assert len(set(run_ids)) == 3
    assert count(lab) == before + 3


@pytest.mark.parametrize('mutation', ['context', 'observation'])
def test_conflicting_accounting_replay_cannot_amend_attribution_or_amount(lab, mutation):
    run = start(lab, workflow='synthetic').json()
    recorder = PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment=lab['environment'])
    call = recorder.calls(run_id=run['run_id'])[0]
    before = recorder.report(run_id=run['run_id'])
    if mutation == 'context':
        conflicting = deepcopy(call['intent'])
        conflicting['context']['tenant_id'] = 'other-tenant'
        with pytest.raises(AccountingError):
            recorder.prepare(conflicting)
    else:
        conflicting = deepcopy(call['observation'])
        conflicting['usage']['output_tokens'] += 1
        conflicting['usage']['total_tokens'] += 1
        with pytest.raises(AccountingError):
            recorder.observe(call['intent']['provider_call_id'], conflicting)
    after = recorder.report(run_id=run['run_id'])
    assert after['total_calls'] == 1
    assert after['estimated_amounts'] == before['estimated_amounts']
    assert recorder.calls(run_id=run['run_id'])[0]['intent']['context'] == call['intent']['context']


def test_quarantined_evidence_is_visible_without_a_zero_or_second_estimate(lab):
    run = start(lab, workflow='synthetic').json()
    recorder = PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment=lab['environment'])
    call = recorder.calls(run_id=run['run_id'])[0]
    before = recorder.report(run_id=run['run_id'])
    intent, observation = deepcopy(call['intent']), deepcopy(call['observation'])
    intent['provider_call_id'] = observation['provider_call_id'] = uuid.uuid4().hex
    observation['usage']['status'] = 'untrusted'
    recorder.prepare(intent)
    recorder.observe(intent['provider_call_id'], observation)
    response = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab), timeout=10)
    assert response.status_code == 200
    usage = response.json()
    assert usage['total_calls'] == 2
    assert usage['quarantined_calls'] == 1
    assert usage['fully_costed'] is False
    assert usage['estimated_amounts'] == before['estimated_amounts']
    assert usage['billing_eligible'] is False


@pytest.mark.parametrize('scenario,budget,reason', [('missing_usage', 1000, 'usage_unknown'),
                                                   ('invalid_output', 100, 'token_limit')])
def test_public_sdk_token_budget_survives_reconstruction_without_retry_bypass(
        lab, tmp_path, monkeypatch, scenario, budget, reason):
    # Public SDK path with durable adapters, distinct from service HTTP policy.
    source = tmp_path / 'assets'
    shutil.copytree(Path(__file__).resolve().parents[2] / 'assets', source)
    runtime = yaml.safe_load((source / 'runtime.yml').read_text())
    runtime['profiles']['synthetic']['base_url'] = lab['model'] + '/v1'
    (source / 'runtime.yml').write_text(yaml.safe_dump(runtime))
    definition = yaml.safe_load((source / 'synthetic.yml').read_text())
    definition['limits']['max_tokens'] = budget
    (source / 'synthetic.yml').write_text(yaml.safe_dump(definition))
    monkeypatch.setenv('PATH', str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', ''))
    run_id = uuid.uuid4().hex
    context = ExecutionContext(application_id='integration-lab', tenant_id='tenant-a', actor_id='alice',
                               billing_account_id='account-a', request_id=run_id)
    recorder = PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment=lab['environment'],
                               rate_card=RateCard('synthetic-v1', 'test-model', '2', '8', '0.5'))
    before = count(lab)
    httpx.post(lab['model'] + '/control', json={'scenario': scenario}, timeout=5).raise_for_status()
    try:
        with PostgresRunStore(lab['harness_dsn'], namespace=lab['namespace']) as store:
            original = Harness(Workflow.load(source / 'synthetic.yml'), store=store,
                               run_id=run_id, context=context, accounting=recorder)
            state = original.run({'task': 'Neutral budget fixture'})
            assert state['status'] == 'blocked'
            assert state['reason'] == reason
        # Reconstruct using a separate store/recorder and changed recorder defaults.
        changed = PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment=lab['environment'],
            defaults=ExecutionContext(tenant_id='other-tenant', billing_account_id='other-account'))
        with PostgresRunStore(lab['harness_dsn'], namespace=lab['namespace']) as store:
            recovered = Harness(Workflow.load(source / 'synthetic.yml'), store=store,
                                run_id=run_id, context=context, accounting=changed)
            state = recovered.resume(expected_revision=recovered.status().revision, retry_interrupted=True)
            assert state['status'] == 'blocked'
            assert state['reason'] == reason
        assert count(lab) == before + 1
        usage = changed.report(run_id=run_id, tenant_id='tenant-a', billing_account_id='account-a')
        assert usage['total_calls'] == 1
        assert changed.report(run_id=run_id, tenant_id='other-tenant')['total_calls'] == 0
        if scenario == 'missing_usage':
            assert usage['unresolved_calls'] == 1
            assert usage['estimated_amounts'] == {}
        else:
            assert usage['complete_calls'] == 1
    finally:
        httpx.post(lab['model'] + '/control', json={}, timeout=5).raise_for_status()


@pytest.mark.parametrize('table,column', [('prosaic_metering_intents', 'payload'),
                                         ('prosaic_metering_observations', 'payload_hash')])
def test_missing_accounting_contract_fails_readiness_without_repair(lab, table, column):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute(sql.SQL('ALTER TABLE {} RENAME COLUMN {} TO unavailable_column').format(
            sql.Identifier(table), sql.Identifier(column)))
    try:
        for replica in ('a', 'b'):
            response = httpx.get(lab[replica] + '/readyz', timeout=5)
            assert response.status_code == 503
            assert response.json() == {'detail': 'not_ready'}
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute(sql.SQL('ALTER TABLE {} RENAME COLUMN unavailable_column TO {}').format(
                sql.Identifier(table), sql.Identifier(column)))


@pytest.mark.parametrize('table,role', [('prosaic_metering_intents', 'accounting_runtime'),
    ('lab_app.runs', 'app_runtime'), ('prosaic_harness.receipts', 'harness_runtime')])
def test_missing_write_grant_fails_readiness_without_repair(lab, table, role):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute(sql.SQL('REVOKE INSERT ON {} FROM {}').format(
            sql.Identifier(*table.split('.')), sql.Identifier(role)))
    try:
        assert httpx.get(lab['a'] + '/readyz', timeout=5).status_code == 503
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute(sql.SQL('GRANT INSERT ON {} TO {}').format(
                sql.Identifier(*table.split('.')), sql.Identifier(role)))


def test_missing_harness_receipt_contract_fails_readiness_without_repair(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE prosaic_harness.receipts RENAME COLUMN document TO unavailable_document')
    try:
        for replica in ('a', 'b'):
            assert httpx.get(lab[replica] + '/readyz', timeout=5).status_code == 503
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('ALTER TABLE prosaic_harness.receipts RENAME COLUMN unavailable_document TO document')


def test_missing_application_uniqueness_fails_readiness_without_repair(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE lab_app.runs DROP CONSTRAINT runs_tenant_id_actor_id_idempotency_key_key')
    try:
        assert httpx.get(lab['a'] + '/readyz', timeout=5).status_code == 503
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('ALTER TABLE lab_app.runs ADD CONSTRAINT runs_tenant_id_actor_id_idempotency_key_key UNIQUE(tenant_id,actor_id,idempotency_key)')


def test_wrong_application_payload_type_fails_readiness_without_repair(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE lab_app.runs ALTER COLUMN request TYPE json USING request::json')
    try:
        assert httpx.get(lab['a'] + '/readyz', timeout=5).status_code == 503
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('ALTER TABLE lab_app.runs ALTER COLUMN request TYPE jsonb USING request::jsonb')


def test_missing_application_phase_grant_fails_readiness_without_repair(lab):
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('REVOKE UPDATE(phase) ON lab_app.runs FROM app_runtime')
    try:
        assert httpx.get(lab['a'] + '/readyz', timeout=5).status_code == 503
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('GRANT UPDATE(phase) ON lab_app.runs TO app_runtime')


def test_lost_http_response_does_not_authorize_duplicate_dispatch(lab):
    key = uuid.uuid4().hex
    before = count(lab)
    httpx.post(lab['model'] + '/control', json={'blocked': True}, timeout=5).raise_for_status()
    try:
        with pytest.raises(httpx.ReadTimeout):
            httpx.post(lab['a'] + '/runs', headers={**headers(lab), 'Idempotency-Key': key},
                json={'task': 'Neutral disconnect fixture', 'workflow': 'synthetic'}, timeout=0.2)
        wait_for(lambda: count(lab) == before + 1, timeout=5)
        assert httpx.get(lab['a'] + '/healthz', timeout=2).status_code == 200
    finally:
        httpx.post(lab['model'] + '/control', json={}, timeout=5).raise_for_status()
    def replay():
        response = start({**lab, 'a': lab['b']}, workflow='synthetic', key=key, task='Neutral disconnect fixture')
        assert response.status_code == 200
        return response.json() if response.json()['status'] == 'waiting' else None
    run = wait_for(replay, timeout=10)
    assert count(lab) == before + 1
    usage = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab), timeout=5).json()
    assert usage['total_calls'] == usage['complete_calls'] == 1


def test_overloaded_starts_do_not_grow_durable_reservations(lab):
    def rows():
        with psycopg.connect(lab['app_dsn']) as conn:
            return conn.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]
    before, initial = count(lab), rows()
    assert httpx.post(lab['model'] + '/control', json={'blocked': True}, timeout=5).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(start, lab, actor, 'synthetic') for actor in ('alice', 'bob')]
        try:
            wait_for(lambda: count(lab) == before + 2, timeout=5)
            assert httpx.get(lab['a'] + '/healthz', timeout=2).status_code == 200
            for _ in range(12):
                response = start(lab, 'carol', 'synthetic')
                assert response.status_code == 503
                assert response.json() == {'detail': 'capacity_exhausted'}
            assert count(lab) == before + 2
            assert rows() == initial + 2, 'capacity-rejected requests persisted new reservations'
        finally:
            httpx.post(lab['model'] + '/control', json={}, timeout=5).raise_for_status()
            for future in futures:
                future.result(timeout=20)


def test_private_inputs_and_credentials_absent_from_public_views_and_server_logs(lab):
    sentinel = 'AUDIT_PRIVATE_INPUT_' + uuid.uuid4().hex
    response = start(lab, workflow='synthetic', task=sentinel)
    assert response.status_code == 200
    run = response.json()
    public = [response.text]
    for replica in ('a', 'b'):
        for suffix in ('', '/usage'):
            response = httpx.get(lab[replica] + '/runs/' + run['run_id'] + suffix, headers=headers(lab), timeout=10)
            assert response.status_code == 200
            public.append(response.text)
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    for identifier in manifest['replica_ids'].values():
        state = json.loads(command(manifest['engine'], 'inspect', identifier))[0]
        validate_resource(state, identifier, manifest['owner'])
        logs = subprocess.run([manifest['engine'], 'logs', identifier], capture_output=True,
                              text=True, timeout=5)
        assert logs.returncode == 0, 'cannot inspect owned fixture logs'
        public.extend([logs.stdout, logs.stderr])
    private_markers = [sentinel, *lab['principals'], lab['app_dsn'], lab['accounting_dsn'], lab['harness_dsn']]
    assert not any(marker in output for marker in private_markers for output in public), 'private sentinel leaked'


@pytest.mark.parametrize('dsn_key', ['app_dsn', 'harness_dsn', 'accounting_dsn'])
def test_runtime_roles_are_not_admin_and_cannot_amend_application_identity(lab, dsn_key):
    with psycopg.connect(lab[dsn_key]) as conn:
        assert conn.execute('SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone() == (False, False, False, False)
        if dsn_key == 'app_dsn':
            assert conn.execute("SELECT has_table_privilege(current_user,'lab_app.runs','DELETE')").fetchone() == (False,)
            assert conn.execute("SELECT has_column_privilege(current_user,'lab_app.runs','tenant_id','UPDATE')").fetchone() == (False,)
        else:
            assert conn.execute("SELECT has_schema_privilege(current_user,'lab_app','USAGE')").fetchone() == (False,)

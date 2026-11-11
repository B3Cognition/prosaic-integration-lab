"""Required published-recorder/store compatibility on exact-owned PostgreSQL."""
from contextlib import contextmanager
from copy import deepcopy
import os
import runpy
import secrets
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from lab_runner.blueprints import copy_blueprint
from lab_runner.rule_admission.fixtures import scripted_provider


@contextmanager
def owned_database():
    base = os.environ.get('PROSAIC_RULE_POSTGRES_DSN')
    assert base, 'required metadata lane needs an explicitly owned disposable PROSAIC_RULE_POSTGRES_DSN'
    suffix = uuid4().hex
    name, role, password = 'metadata_lab_' + suffix, 'metadata_runtime_' + suffix, secrets.token_hex(24)
    role_created = False
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        with psycopg.connect(base, autocommit=True) as admin:
            admin.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
            role_created = True
        migration_dsn = make_conninfo(base, dbname=name)
        runtime_dsn = make_conninfo(base, dbname=name, user=role, password=password)
        from prosaic_runtime_postgres import PostgresRecorder
        from prosaic_harness_postgres import PostgresRunStore
        # Only this migration scope gets owner credentials. Replicas below use the runtime role.
        PostgresRecorder(migration_dsn, namespace='metadata', environment='test').initialize()
        migration_store = PostgresRunStore(migration_dsn, namespace='metadata')
        try: migration_store.initialize()
        finally: migration_store.close()
        with psycopg.connect(migration_dsn) as owner:
            owner.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
            for statement in (
                'GRANT USAGE ON SCHEMA public, prosaic_harness TO {}',
                'GRANT SELECT, INSERT ON prosaic_metering_intents, prosaic_metering_observations TO {}',
                'GRANT UPDATE ON prosaic_metering_intents TO {}',
                'GRANT SELECT ON prosaic_harness.schema_version, prosaic_harness.leases, prosaic_harness.runs, prosaic_harness.receipts TO {}',
                'GRANT INSERT, UPDATE ON prosaic_harness.leases, prosaic_harness.runs TO {}',
                'GRANT INSERT ON prosaic_harness.receipts TO {}',
            ): owner.execute(sql.SQL(statement).format(sql.Identifier(role)))
        yield runtime_dsn
    finally:
        with psycopg.connect(base, autocommit=True) as admin:
            # Only the allocated database/role are eligible for destructive cleanup.
            assert name == 'metadata_lab_' + suffix and role == 'metadata_runtime_' + suffix
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
            if role_created: admin.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
            assert admin.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone() is None
            assert admin.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone() is None


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
def test_published_recorder_labels_reopen_conflict_and_saved_receipt_no_call(tmp_path, monkeypatch, wire):
    from prosaic_harness import Harness
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_runtime import ExecutionContext, RateCard
    from prosaic_runtime.accounting import AccountingError
    from prosaic_runtime_postgres import PostgresRecorder
    monkeypatch.setenv('no_proxy', '*')
    monkeypatch.setenv('NO_PROXY', '*')
    project = copy_blueprint('accounting-metadata', tmp_path/'metadata')
    host = runpy.run_path(str(project/'host.py'))
    class LostAck(BaseException): pass
    class FaultStore(PostgresRunStore):
        def save_receipt(self, run_id, invocation_id, receipt, lease):
            super().save_receipt(run_id, invocation_id, receipt, lease)
            if receipt['step'] == 'second': raise LostAck()
    with owned_database() as dsn:
        store = None
        try:
            backend = PostgresRecorder(dsn, namespace='metadata', environment='test', provider_id=wire,
                                      rate_card=RateCard('synthetic-v1', 'synthetic-model', '2', '8'))
            assert backend.check_ready()
            store = FaultStore(dsn, namespace='metadata'); store.check_ready()
            with scripted_provider(wire) as provider:
                seen = []
                def before(labels):
                    assert len(provider.requests) == len(seen)
                    seen.append(dict(labels))
                recorder = host['LabelingRecorder'](backend, before)
                runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire, accounting=recorder)
                flow, run_id = host['workflow'](runtime, project=project), uuid4().hex
                context = host['trusted_context'](tenant_id='tenant', billing_account_id='payer',
                                                 benchmark_run='benchmark-42', variant='saved')
                provider.queue_text('{"approved":true}'); provider.queue_text('{"approved":true}')
                original = Harness(flow, store=store, run_id=run_id, runtime=runtime, context=context)
                assert original.run({})['status'] == 'waiting'
                with pytest.raises(LostAck):
                    original.resume(choice='approve', expected_revision=original.status().revision)
                rows = backend.calls()
                assert len(rows) == len(provider.requests) == 2
                assert seen == [{'run': 'benchmark-42', 'variant': 'saved'}] * 2
                store.close(); store = PostgresRunStore(dsn, namespace='metadata'); store.check_ready()
                # Reopen the actual public recorder and move defaults/new caller labels.
                backend = PostgresRecorder(dsn, namespace='metadata', environment='test', provider_id=wire,
                    defaults=ExecutionContext(tenant_id='changed', request_metadata={'variant': 'default'}))
                assert backend.check_ready()
                fresh_runtime = host['build_runtime'](project=project, base_url=provider.url, provider=wire,
                                                      accounting=host['LabelingRecorder'](backend))
                fresh = Harness(flow, store=store, run_id=run_id, runtime=fresh_runtime,
                                context=ExecutionContext(request_metadata={'variant': 'new-caller'}))
                assert fresh.recovery_evidence()['recoveryStatus'] == 'receiptAvailable'
                state = fresh.resume()
                assert state['status'] == 'completed' and len(provider.requests) == 2
                assert state['accounting_context']['request_metadata']['labels']['variant'] == 'saved'
                assert backend.calls() == rows
                first = rows[0]['intent']
                backend.prepare(deepcopy(first))
                backend.observe(first['provider_call_id'], rows[0]['observation'])
                changed = deepcopy(first)
                changed['context']['request_metadata']['labels']['variant'] = 'other'
                with pytest.raises(AccountingError, match='conflicting'): backend.prepare(changed)
                assert backend.calls() == rows
                assert backend.report(tenant_id='tenant')['complete_calls'] == 2
                assert backend.report(tenant_id='other')['total_calls'] == 0
                assert backend.report()['estimated_amounts'] == {'USD': '0.000056000000000000'}
                assert backend.report()['billing_eligible'] is False
                with pytest.raises(ValueError): backend.report(variant='saved')
        finally:
            if store is not None: store.close()

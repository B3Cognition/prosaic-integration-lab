"""Required installed sent-effort receipts on exact-owned PostgreSQL16/18."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import os,runpy,secrets,json
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
    assert base, 'required sent-effort lane needs an explicitly owned disposable PROSAIC_RULE_POSTGRES_DSN'
    suffix = uuid4().hex
    name, role, password = 'sent_effort_lab_' + suffix, 'sent_effort_runtime_' + suffix, secrets.token_hex(24)
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
        PostgresRecorder(migration_dsn, namespace='effort', environment='test').initialize()
        migration_store = PostgresRunStore(migration_dsn, namespace='effort')
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
            assert name == 'sent_effort_lab_' + suffix and role == 'sent_effort_runtime_' + suffix
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
            if role_created: admin.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
            assert admin.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone() is None
            assert admin.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone() is None



@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
def test_installed_recorder_and_store_keep_all_sent_rows_on_no_call_adoption(tmp_path,monkeypatch,wire):
    from prosaic_harness import Harness
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_runtime import ExecutionContext
    from prosaic_runtime_postgres import PostgresRecorder
    monkeypatch.setenv('no_proxy','*');monkeypatch.setenv('NO_PROXY','*')
    project=copy_blueprint('sent-effort',tmp_path/'effort');host=runpy.run_path(str(project/'host.py'));saved=[]
    class LostAck(BaseException):pass
    class FaultStore(PostgresRunStore):
        def save_receipt(self,run_id,invocation_id,receipt,lease):
            super().save_receipt(run_id,invocation_id,receipt,lease);saved.append(deepcopy(receipt))
            if receipt['step']=='second':raise LostAck()
    with owned_database() as dsn:
        store=None
        try:
            backend=PostgresRecorder(dsn,namespace='effort',environment='test',provider_id=wire);assert backend.check_ready()
            store=FaultStore(dsn,namespace='effort');store.check_ready()
            with scripted_provider(wire) as provider:
                rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=backend)
                flow=host['workflow'](rt,project=project);run_id=uuid4().hex
                provider.queue_text('{"approved":true}');provider.queue_text('{"approved":true}')
                h=Harness(flow,store=store,run_id=run_id,runtime=rt,context=ExecutionContext(tenant_id='trusted-tenant',billing_account_id='trusted-payer',request_metadata={'variant':'original'}))
                assert h.run({})['status']=='waiting'
                store.close();store=FaultStore(dsn,namespace='effort');store.check_ready();h=Harness(flow,store=store,run_id=run_id,runtime=rt)
                with pytest.raises(LostAck):h.resume(choice='approve',expected_revision=h.status().revision)
                assert len(saved)==len(provider.requests)==2
                calls=backend.calls();assert len(calls)==2
                docs=[r['result']['metadata']['reasoning_effort_v1'] for r in saved]
                assert all(d['attempt_count']==1 and d['complete'] is True and d['omitted_attempts']==0 for d in docs)
                assert {d['attempts'][0]['provider_call_id'] for d in docs}=={c['intent']['provider_call_id'] for c in calls}
                assert all(d['attempts'][0]['provider_confirmation']=='not_observed' for d in docs)
                receipt_bytes=[json.dumps(r,sort_keys=True,separators=(',',':')).encode() for r in saved]
                store.close();store=PostgresRunStore(dsn,namespace='effort');store.check_ready()
                reopened=PostgresRecorder(dsn,namespace='effort',environment='test',provider_id=wire);assert reopened.check_ready()
                fresh_rt=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=reopened)
                fresh=Harness(flow,store=store,run_id=run_id,runtime=fresh_rt)
                assert fresh.recovery_evidence()['recoveryStatus']=='receiptAvailable'
                assert fresh.resume()['status']=='completed' and len(provider.requests)==2
                assert reopened.calls()==calls
                for receipt,original_bytes in zip(saved,receipt_bytes):
                    loaded=store.load_receipt(run_id,receipt['id']);assert loaded==receipt
                    assert json.dumps(loaded,sort_keys=True,separators=(',',':')).encode()==original_bytes

        finally:
            if store is not None:store.close()


@pytest.mark.parametrize('wire',['openai-compatible','anthropic'])
def test_actual_pre_effort_postgres_receipts_adopt_without_inventing_trace(tmp_path,monkeypatch,wire,create_legacy_receipts):
    from types import SimpleNamespace
    from prosaic_harness import Harness
    from prosaic_harness_postgres import PostgresRunStore
    from prosaic_runtime_postgres import PostgresRecorder
    monkeypatch.setenv('NO_PROXY','*');monkeypatch.setenv('no_proxy','*')
    project=copy_blueprint('sent-effort',tmp_path/'legacy-effort');host=runpy.run_path(str(project/'host.py'))
    with owned_database() as dsn:
        with scripted_provider(wire) as provider:
            provider.queue_text('{"approved":true}');provider.queue_text('{"approved":true}')
            run_id=uuid4().hex
            old=create_legacy_receipts(kind='postgres',project=project,url=provider.url,wire=wire,run_id=run_id,dsn=dsn)
            assert old['runtimeVersion']=='0.9.17' and len(provider.requests)==len(old['accounting'])==2
            original=[json.dumps(r,sort_keys=True,separators=(',',':')).encode() for r in old['receipts']]
            recorder=PostgresRecorder(dsn,namespace='effort',environment='test',provider_id=wire);assert recorder.check_ready()
            runtime=host['build_runtime'](project=project,base_url=provider.url,provider=wire,accounting=recorder)
            store=PostgresRunStore(dsn,namespace='effort');store.check_ready()
            try:
                h=Harness(host['workflow'](runtime,project=project),store=store,run_id=run_id,runtime=runtime)
                assert h.recovery_evidence()['recoveryStatus']=='receiptAvailable'
                assert h.resume()['status']=='completed' and len(provider.requests)==2
                assert recorder.calls()==old['accounting']
                for receipt,encoded in zip(old['receipts'],original):
                    loaded=store.load_receipt(run_id,receipt['id'])
                    assert json.dumps(loaded,sort_keys=True,separators=(',',':')).encode()==encoded
                    assert 'reasoning_effort_v1' not in loaded['result']['metadata']
                    assert host['effort_report'](SimpleNamespace(metadata=loaded['result']['metadata']))=={'available':False,'trace':None}
            finally:store.close()

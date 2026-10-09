from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import pytest
import psycopg
from prosaic_integration_lab.billing_store import BillingStore
from prosaic_integration_lab.billing_projection import project


def projection(lab, name):
    from datetime import datetime,timezone
    r = dict(namespace=lab['namespace'],environment='sandbox',tenant_id='fixture',actor_id='actor',
             billing_account_id='account',run_id=name)
    c = dict(intent=dict(provider_call_id=name,requested_model='test-model',namespace=lab['namespace'],
        environment='sandbox',provider_id='openai-compatible',credential_account='platform',context=dict(
        application_id='integration-lab',tenant_id='fixture',actor_id='actor',billing_account_id='account',
        request_id=name,run_id=name)),measurement_state='complete',assessment={'normalization_version':1},
        observation=dict(response_model='test-model',finished_at=datetime.now(timezone.utc).isoformat(),
            usage=dict(status='reported',input_tokens=100,cached_input_tokens=20,output_tokens=25,
                       total_tokens=125,reasoning_output_tokens=None)))
    return project(c,r,dict(subscription='fixture-sub',revision='fixture-v1'))


def test_atomic_enqueue_and_conflict(lab):
    store = BillingStore(lab['billing_dsn'])
    p = projection(lab,'outbox-atomic')
    store.enqueue(p)
    store.enqueue(p)
    assert len(store.events(p['scope'])) == 3
    other = deepcopy(p)
    other['hash'] = 'f'*64
    with pytest.raises(ValueError): store.enqueue(other)
    assert store.summary(p['scope'])['conflict'] == 3


def test_concurrent_enqueue_and_claim_fencing(lab):
    store = BillingStore(lab['billing_dsn'])
    p = projection(lab,'outbox-concurrent')
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(store.enqueue,[p,p]))
    first = store.claim(3,30,scope=p['scope'])
    assert len(first) == 3
    assert store.claim(3,30,scope=p['scope']) == []
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute("UPDATE lab_billing.events SET lease_until=clock_timestamp()-interval '1 second' WHERE source=%s",(p['source'],))
    recovered = store.claim(3,30,scope=p['scope'])
    assert len(recovered) == 3
    assert store.ack(first[0]['key'],first[0]['token']) is False
    assert store.ack(recovered[0]['key'],recovered[0]['token']) is True


def test_pending_evidence_survives_reconstruction(lab):
    store = BillingStore(lab['billing_dsn'])
    p = projection(lab,'outbox-reconstruct')
    p['scope'] = 'a'*64
    store.enqueue(p)
    reconstructed = BillingStore(lab['billing_dsn'])
    assert reconstructed.summary(p['scope']) == {'pending':3}
    rows = reconstructed.claim(3,30,scope=p['scope'])
    reconstructed.fail(rows[0]['key'],rows[0]['token'],'transport',1)
    assert reconstructed.summary(p['scope']) == {'pending':3}
    store.mapping(p['scope'],p['mapping'])
    with pytest.raises(ValueError):
        reconstructed.mapping(p['scope'],{**p['mapping'],'revision':'changed-pricing','subscription':'other-sub'})
    assert reconstructed.get_mapping(p['scope']) == p['mapping']


def test_role_cannot_modify_source_or_replica_billing(lab):
    for dsn,statement in [(lab['billing_dsn'],'DELETE FROM prosaic_metering_intents'),
                          (lab['app_dsn'],'DELETE FROM lab_billing.events')]:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(dsn) as conn: conn.execute(statement)


def test_readiness_rejects_missing_fencing_grant(lab):
    store = BillingStore(lab['billing_dsn'])
    store.check_ready()
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('REVOKE UPDATE(token) ON lab_billing.events FROM billing_exporter')
    try:
        with pytest.raises(ValueError): store.check_ready()
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('GRANT UPDATE(token) ON lab_billing.events TO billing_exporter')


def test_readiness_rejects_missing_state_constraint(lab):
    store = BillingStore(lab['billing_dsn'])
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE lab_billing.events DROP CONSTRAINT events_state_check')
    try:
        with pytest.raises(ValueError): store.check_ready()
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute("ALTER TABLE lab_billing.events ADD CONSTRAINT events_state_check CHECK(state IN ('pending','acknowledged','failed','conflict'))")


def test_exporter_cannot_read_application_prompt(lab):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(lab['billing_dsn']) as conn:
            conn.execute('SELECT request FROM lab_app.runs')


def test_exporter_cannot_change_frozen_payload(lab):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(lab['billing_dsn']) as conn:
            conn.execute("UPDATE lab_billing.events SET payload='{}'::jsonb")


def test_readiness_rejects_wrong_fencing_column_type(lab):
    store = BillingStore(lab['billing_dsn'])
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE lab_billing.events ALTER COLUMN attempts TYPE text USING attempts::text')
    try:
        with pytest.raises(ValueError): store.check_ready()
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('ALTER TABLE lab_billing.events ALTER COLUMN attempts TYPE integer USING attempts::integer')


def test_stale_unresolved_scan_does_not_poison_complete_evidence(lab):
    store = BillingStore(lab['billing_dsn'])
    complete = projection(lab,'outbox-stale-scan')
    # Derive an earlier public-recorder-shaped snapshot from the same intent.
    # Complete call fixtures here use actual public projection, not hand-made hashes.
    r = complete['locator']['reservation']
    from datetime import datetime,timezone
    call = dict(intent=dict(namespace=lab['namespace'],environment='sandbox',provider_call_id='outbox-stale-scan',
        requested_model='test-model',provider_id='openai-compatible',credential_account='platform',
        context=dict(application_id='integration-lab',tenant_id=r['tenant_id'],actor_id=r['actor_id'],
            billing_account_id=r['billing_account_id'],request_id=r['run_id'],run_id=r['run_id'])),
        observation=None,assessment=None,measurement_state='unresolved')
    old = project(call,r,complete['mapping'])
    store.enqueue(old)
    store.enqueue(complete)
    store.enqueue(old)
    assert not any(s['conflict'] for s in store.sources() if s['source']==complete['source'])
    assert len([e for e in store.events(complete['scope']) if e['source']==complete['source'] and e['state']=='pending']) == 3


def test_remote_conflict_blocks_all_dimensions(lab):
    store = BillingStore(lab['billing_dsn'])
    p = projection(lab,'outbox-remote-conflict')
    p['scope'] = 'b'*64
    store.enqueue(p)
    row = store.claim(1,30,scope=p['scope'])[0]
    assert store.fail(row['key'],row['token'],'conflict')
    assert store.summary(p['scope']) == {'conflict':3}
    assert store.claim(3,30,scope=p['scope']) == []

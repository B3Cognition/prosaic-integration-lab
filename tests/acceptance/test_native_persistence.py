"""Required owned PostgreSQL tests; missing infrastructure fails qualification."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import uuid

from fastapi import HTTPException
import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.metadata import Metadata, RequestConflict
from prosaic_integration_lab.migrations import migrate
from prosaic_integration_lab.proposals import ProposalStore


@pytest.fixture
def principal(lab):
    return Principal(**next(iter(lab['principals'].values())))


@pytest.fixture
def proposals(lab):
    return ProposalStore(lab['app_dsn'])


def reserve(proposals, principal, prepared, key=None, **limits):
    return proposals.reserve(principal,key or uuid.uuid4().hex,prepared,
        maximum_records=limits.get('maximum_records',10000),
        maximum_tenant_records=limits.get('maximum_tenant_records',10000))


def test_proposal_replay_after_bundle_upgrade_keeps_original_reference(proposals,principal,prepared_v1,prepared_v2):
    key = uuid.uuid4().hex
    original = reserve(proposals,principal,prepared_v1,key)
    replay = proposals.replay(principal,key,original['request_digest'])
    assert replay == original
    assert replay['proposal_json'] == prepared_v1.proposal_json
    assert replay['reference'] == prepared_v1.reference.to_dict()
    assert replay['reference'] != prepared_v2.reference.to_dict()
    assert reserve(proposals,principal,prepared_v2,key,maximum_records=1,maximum_tenant_records=1) == original


def test_concurrent_bundle_admission_returns_only_original_winning_reference(proposals,principal,prepared_v1,prepared_v2):
    key = uuid.uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda prepared:reserve(proposals,principal,prepared,key),[prepared_v1,prepared_v2]))
    assert rows[0] == rows[1]
    assert rows[0]['reference'] in [prepared_v1.reference.to_dict(),prepared_v2.reference.to_dict()]
    assert proposals.replay(principal,key,rows[0]['request_digest']) == rows[0]


def test_body_conflict_and_other_owner_lookup_do_not_expose_original(proposals,principal,prepared_v1,bundle_factory,proposal_text):
    key = uuid.uuid4().hex
    original = reserve(proposals,principal,prepared_v1,key)
    changed = bundle_factory().prepare_json(proposal_text.replace('Accept žluť?','Changed?'))
    with pytest.raises(RequestConflict,match='idempotency_conflict'):
        reserve(proposals,principal,changed,key)
    with pytest.raises(RequestConflict):
        proposals.replay(principal,key,hashlib.sha256(changed.proposal_json.encode()).hexdigest())
    stranger = Principal(principal.tenant_id,uuid.uuid4().hex,'other-billing')
    assert proposals.owned(stranger,original['proposal_id']) is None
    assert proposals.replay(stranger,key,original['request_digest']) is None


def test_native_reservation_keeps_original_owner_billing_scope_and_inputs(lab,proposals,principal,prepared_v1):
    original = reserve(proposals,principal,prepared_v1)
    metadata = Metadata(lab['app_dsn'])
    key = uuid.uuid4().hex
    inputs = prepared_v1.workflow.prepare_inputs({})
    row = metadata.reserve_native(principal,key,original,inputs,namespace='historical-native',environment='sandbox')
    changed_host = Principal(principal.tenant_id,principal.actor_id,'new-account')
    replay = metadata.reserve_native(changed_host,key,original,{},namespace='new-default',environment='production',
        max_runs=1,max_tenant_runs=1)
    assert replay == row
    assert row['billing_account_id'] == principal.billing_account_id
    assert row['namespace'] == 'historical-native' and row['environment'] == 'sandbox'
    assert row['request'] == {'proposal_id':original['proposal_id'],'inputs':{}}
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT proposal_id,tenant_id,actor_id FROM lab_app.native_runs WHERE run_id=%s',
            (row['run_id'],)).fetchone() == (original['proposal_id'],principal.tenant_id,principal.actor_id)
    with pytest.raises(RequestConflict):
        metadata.reserve_native(principal,key,original,{'changed':True},namespace='x',environment='sandbox')
    stranger = Principal(principal.tenant_id,uuid.uuid4().hex,'other')
    with pytest.raises(HTTPException) as error:
        metadata.reserve_native(stranger,uuid.uuid4().hex,original,{},namespace='x',environment='sandbox')
    assert error.value.status_code == 404


@pytest.mark.parametrize('value',[None,True,42,1.25,'hello',['hello'],{'x':1},
    {'z':[{'ž':True},None],'a':['hello',42]}],
    ids=['null','boolean','integer','float','string','array','object','nested'])
def test_public_json_input_type_survives_native_reservation_and_replay(lab,proposals,principal,prepared_finish,value):
    original = reserve(proposals,principal,prepared_finish)
    metadata = Metadata(lab['app_dsn'])
    key = uuid.uuid4().hex
    inputs = prepared_finish.workflow.prepare_inputs(value)
    first = metadata.reserve_native(principal,key,original,inputs,namespace='original-json',environment='sandbox')
    assert first['request']['inputs'] == value and type(first['request']['inputs']) is type(value)
    replay = metadata.reserve_native(principal,key,original,prepared_finish.workflow.prepare_inputs(value),
        namespace='current-default',environment='production',max_runs=1,max_tenant_runs=1)
    assert replay == first
    changed = True if value is None else None
    with pytest.raises(RequestConflict):
        metadata.reserve_native(principal,key,original,prepared_finish.workflow.prepare_inputs(changed),
            namespace='original-json',environment='sandbox')
    assert metadata.owned(principal,first['run_id']) == first


def test_runtime_role_cannot_mutate_immutable_proposals_or_migrate(lab,proposals,principal,prepared_v1):
    row = reserve(proposals,principal,prepared_v1)
    for statement in ('UPDATE lab_app.proposals SET proposal_json=proposal_json WHERE proposal_id=%s',
                      'DELETE FROM lab_app.proposals WHERE proposal_id=%s'):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with psycopg.connect(lab['app_dsn']) as connection:
                connection.execute(statement,(row['proposal_id'],))
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        migrate(lab['app_dsn'])
    Metadata(lab['app_dsn']).check_ready()


def test_capacity_exhaustion_keeps_replay_and_blocks_new_key(proposals,principal,prepared_v1):
    first_key, second_key = uuid.uuid4().hex,uuid.uuid4().hex
    first = reserve(proposals,principal,prepared_v1,first_key)
    reserve(proposals,principal,prepared_v1,second_key)
    assert reserve(proposals,principal,prepared_v1,first_key,maximum_records=1,maximum_tenant_records=1) == first
    with pytest.raises(HTTPException) as error:
        reserve(proposals,principal,prepared_v1,maximum_records=1,maximum_tenant_records=1)
    assert error.value.status_code == 503


def test_schema_constraints_bound_raw_immutable_storage(lab,proposals,principal,prepared_v1):
    from psycopg.types.json import Jsonb
    first = reserve(proposals,principal,prepared_v1)
    for column, value in [('proposal_json','x'*65537),('reference',Jsonb({'private':'x'*4096})),
                          ('bundle_version','x'*129)]:
        with pytest.raises(psycopg.errors.CheckViolation):
            with psycopg.connect(lab['migration_dsn']) as connection:
                connection.execute(f'UPDATE lab_app.proposals SET {column}=%s WHERE proposal_id=%s',
                    (value,first['proposal_id']))
    assert proposals.owned(principal,first['proposal_id']) == first


def test_readiness_rejects_accidentally_granted_proposal_update(lab,owned_database):
    private = owned_database('grants')
    migrate(private['migration_dsn'],runtime_role='app_runtime')
    Metadata(private['app_dsn']).check_ready()
    with psycopg.connect(private['migration_dsn']) as connection:
        connection.execute('GRANT UPDATE(proposal_json) ON lab_app.proposals TO app_runtime')
    with pytest.raises(ValueError,match='mutable storage powers'):
        Metadata(private['app_dsn']).check_ready()


def test_concurrent_explicit_migrations_share_transaction_lock(owned_database):
    private = owned_database('migration_race')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _:migrate(private['migration_dsn'],runtime_role='app_runtime'),range(2)))
    assert sorted(result['from_version'] for result in results) == [0,3]
    assert all(result['to_version'] == 3 and result['rows_preserved'] == 0 for result in results)
    Metadata(private['app_dsn']).check_ready()


def test_version_two_upgrade_preserves_every_legacy_field_and_phase(lab):
    # A newly owned database, never downgrade or erase an active service schema.
    from pathlib import Path
    import json
    from lab_runner.stack import command
    from lab_runner.manifest import validate_resource
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['database_id']
    validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    database = 'native_v2_'+uuid.uuid4().hex
    command(manifest['engine'],'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',database)
    parameters = conninfo_to_dict(lab['migration_dsn']); parameters['dbname'] = database
    dsn = make_conninfo(**parameters)
    with psycopg.connect(dsn) as connection:
        connection.execute('CREATE SCHEMA lab_app')
        connection.execute('CREATE TABLE lab_app.schema_version(version integer PRIMARY KEY)')
        connection.execute('INSERT INTO lab_app.schema_version VALUES(2)')
        connection.execute('''CREATE TABLE lab_app.runs(run_id text PRIMARY KEY,tenant_id text NOT NULL,
            actor_id text NOT NULL,billing_account_id text NOT NULL,idempotency_key text NOT NULL,
            request_hash text NOT NULL,request jsonb NOT NULL,workflow text NOT NULL,assets_hash text NOT NULL,
            phase text NOT NULL CHECK(phase IN ('reserved','starting','started')),namespace text NOT NULL,
            environment text NOT NULL,UNIQUE(tenant_id,actor_id,idempotency_key))''')
        for phase in ('reserved','starting','started'):
            connection.execute('''INSERT INTO lab_app.runs VALUES(%s,'tenant','actor','billing',%s,'old-hash',
                '{"task":"historic"}','approval','old-assets',%s,'authoritative-original','sandbox')''',
                (uuid.uuid4().hex,uuid.uuid4().hex,phase))
        originals = connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id').fetchall()
    assert migrate(dsn,runtime_role='app_runtime') == {'from_version':2,'to_version':3,'rows_preserved':3}
    with psycopg.connect(dsn) as connection:
        assert connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id').fetchall() == originals
        assert connection.execute('SELECT version FROM lab_app.schema_version').fetchall() == [(3,)]
        assert connection.execute('SELECT count(*) FROM lab_app.proposals').fetchone() == (0,)
    parameters = conninfo_to_dict(lab['app_dsn']); parameters['dbname'] = database
    Metadata(make_conninfo(**parameters)).check_ready()

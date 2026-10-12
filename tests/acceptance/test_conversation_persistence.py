"""Actual distinct PostgreSQL roles, immutable registry/receipts and readiness."""
import hashlib
import json
import uuid

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
import pytest

from prosaic_harness import StoreIncompatible
from prosaic_harness_postgres import PostgresRunStore,PostgresSessionStore
from prosaic_runtime_postgres import PostgresRecorder
from prosaic_integration_lab.conversation_registry import ConversationRegistry
from lab_runner.conversation_scenarios import create,request,send
from lab_runner.native_faults import owned_stack
from test_conversation_journey import conversation_model,principal


@pytest.fixture(scope='module')
def persisted_session(lab):
    p=principal(lab,'user-0005');initial=create(lab,p,uuid.uuid4().hex)
    session=send(lab,p,initial,'persisted','Remember Prague')
    return p,session


def conversation_dsn(lab):return lab['conversation']['dsn']


def test_independent_conversation_and_legacy_adapters_ready_under_distinct_runtime_roles(lab):
    assert {conninfo_to_dict(lab[key])['user'] for key in
        ('migration_dsn','app_dsn','harness_dsn','accounting_dsn')}=={
            'lab_migration','app_runtime','harness_runtime','accounting_runtime'}
    assert conninfo_to_dict(conversation_dsn(lab))['user']=='conversation_runtime'
    with psycopg.connect(conversation_dsn(lab)) as connection:
        assert connection.execute("SELECT pg_has_role(nspowner,'USAGE') FROM pg_catalog.pg_namespace "
            "WHERE nspname='prosaic_harness_conversations'").fetchone()==(False,)
    with PostgresSessionStore(conversation_dsn(lab),namespace=lab['namespace']) as store:store.check_ready()
    with PostgresRunStore(lab['harness_dsn'],namespace=lab['namespace']) as store:store.check_ready()
    PostgresRecorder(lab['accounting_dsn'],namespace=lab['namespace'],environment=lab['environment']).check_ready()
    ConversationRegistry(lab['app_dsn'],namespace=lab['namespace'],environment=lab['environment']).check_ready()


def test_owned_worker_configuration_contains_no_migration_or_schema_owner_credential(lab):
    stack=owned_stack(lab);config=json.loads((stack.secrets/'service.json').read_text())
    has_migration='migration_dsn' in config
    assert has_migration is False
    dsns=[config[key] for key in ('app_dsn','harness_dsn','accounting_dsn')]+[config['conversation']['dsn']]
    assert {conninfo_to_dict(dsn)['user'] for dsn in dsns}=={
        'app_runtime','harness_runtime','accounting_runtime','conversation_runtime'}
    for dsn in dsns:
        fields=conninfo_to_dict(dsn)
        assert fields['user'] not in {'postgres','lab_migration'}


@pytest.mark.parametrize('statement',[
    'CREATE SCHEMA forbidden_conversation_ddl',
    'SELECT * FROM lab_chat.sessions','SELECT * FROM lab_app.runs',
    'SELECT * FROM prosaic_harness.runs','SELECT * FROM prosaic_metering_observations'])
def test_conversation_role_has_no_migration_application_workflow_or_accounting_authority(lab,statement):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(conversation_dsn(lab)) as connection:connection.execute(statement)


@pytest.mark.parametrize('column',['namespace','environment','application','tenant_id','actor_id',
    'billing_account_id','idempotency_key','binding_identity','binding_version','session_id'])
def test_app_runtime_cannot_rewrite_immutable_creation_authority(lab,persisted_session,column):
    p,session=persisted_session
    with psycopg.connect(lab['app_dsn']) as connection:
        original=connection.execute('SELECT * FROM lab_chat.sessions WHERE session_id=%s',(session['sessionId'],)).fetchone()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(lab['app_dsn']) as connection:
            connection.execute(sql.SQL('UPDATE lab_chat.sessions SET {}={} WHERE session_id=%s').format(
                sql.Identifier(column),sql.Identifier(column)),(session['sessionId'],))
    with psycopg.connect(lab['app_dsn']) as connection:
        assert connection.execute('SELECT * FROM lab_chat.sessions WHERE session_id=%s',
            (session['sessionId'],)).fetchone()==original
    assert request(lab,p,'GET','/conversations/'+session['sessionId'],replica='b').json()==session


@pytest.mark.parametrize('statement',[
    'UPDATE prosaic_harness_conversations.receipts SET document=document WHERE session_id=%s',
    'UPDATE prosaic_harness_conversations.receipts SET sha256=sha256 WHERE session_id=%s',
    'DELETE FROM prosaic_harness_conversations.receipts WHERE session_id=%s'])
def test_runtime_cannot_amend_or_remove_saved_invocation_receipts(lab,persisted_session,statement):
    _,session=persisted_session
    with psycopg.connect(conversation_dsn(lab)) as connection:
        receipts=connection.execute('SELECT invocation_id,document,sha256 FROM prosaic_harness_conversations.receipts '
            'WHERE namespace=%s AND session_id=%s ORDER BY invocation_id',(lab['namespace'],session['sessionId'])).fetchall()
    assert len(receipts)==1
    assert hashlib.sha256(receipts[0][1].encode()).hexdigest()==receipts[0][2]
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with psycopg.connect(conversation_dsn(lab)) as connection:connection.execute(statement,(session['sessionId'],))
    with psycopg.connect(conversation_dsn(lab)) as connection:
        assert connection.execute('SELECT invocation_id,document,sha256 FROM prosaic_harness_conversations.receipts '
            'WHERE namespace=%s AND session_id=%s ORDER BY invocation_id',
            (lab['namespace'],session['sessionId'])).fetchall()==receipts


@pytest.mark.parametrize('column,value',[('binding_version','x'*129),('binding_identity','x'*65),
    ('idempotency_key','é'*65),('environment','x'*33),('session_id','x'*33)],
    ids=['version-bytes','identity-bytes','unicode-key-bytes','environment-bytes','session-id-bytes'])
def test_registry_enforces_utf8_storage_bounds_even_for_migration_role(lab,persisted_session,column,value):
    _,session=persisted_session
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(lab['migration_dsn']) as connection:
            connection.execute(sql.SQL('UPDATE lab_chat.sessions SET {}=%s WHERE session_id=%s').format(
                sql.Identifier(column)),(value,session['sessionId']))


@pytest.mark.parametrize('table',['sessions','receipts'],ids=['snapshot-8mib','receipt-8mib'])
def test_postgres_hard_document_ceiling_cannot_be_exceeded_by_owner_write(lab,persisted_session,table):
    _,session=persisted_session
    statement=sql.SQL('SELECT document FROM prosaic_harness_conversations.{} WHERE namespace=%s AND session_id=%s').format(sql.Identifier(table))
    with psycopg.connect(conversation_dsn(lab)) as connection:
        original=connection.execute(statement,(lab['namespace'],session['sessionId'])).fetchall()
    assert len(original)==1
    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(lab['migration_dsn']) as connection:
            connection.execute(sql.SQL('UPDATE prosaic_harness_conversations.{} SET document=%s WHERE namespace=%s AND session_id=%s').format(
                sql.Identifier(table)),('x'*8388609,lab['namespace'],session['sessionId']))
    with psycopg.connect(conversation_dsn(lab)) as connection:
        assert connection.execute(statement,(lab['namespace'],session['sessionId'])).fetchall()==original


def test_conversation_registry_and_receipts_are_logged_primary_storage(lab):
    with psycopg.connect(lab['migration_dsn']) as connection:
        assert connection.execute('SELECT pg_is_in_recovery()').fetchone()==(False,)
        rows=connection.execute("SELECT n.nspname,c.relname,c.relpersistence FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' "
            "AND n.nspname IN ('lab_chat','prosaic_harness_conversations') ORDER BY n.nspname,c.relname").fetchall()
    assert len(rows)==7 and all(row[2]=='p' for row in rows)


@pytest.mark.parametrize('grant,check',[
    ('UPDATE(document) ON prosaic_harness_conversations.receipts TO conversation_runtime','session'),
    ('UPDATE(binding_identity) ON lab_chat.sessions TO app_runtime','registry')],
    ids=['receipt-update','registry-update'])
def test_readiness_rejects_accidental_mutable_receipt_or_registry_powers(lab,grant,check):
    owned_stack(lab)
    revoke='REVOKE '+grant.replace(' TO ',' FROM ')
    with psycopg.connect(lab['migration_dsn']) as connection:connection.execute('GRANT '+grant)
    try:
        if check=='session':
            with PostgresSessionStore(conversation_dsn(lab),namespace=lab['namespace']) as store:
                with pytest.raises(StoreIncompatible):store.check_ready()
        else:
            with pytest.raises(ValueError,match='grants unavailable'):
                ConversationRegistry(lab['app_dsn'],namespace=lab['namespace'],environment=lab['environment']).check_ready()
    finally:
        with psycopg.connect(lab['migration_dsn']) as connection:connection.execute(revoke)
    if check=='session':
        with PostgresSessionStore(conversation_dsn(lab),namespace=lab['namespace']) as store:store.check_ready()
    else:ConversationRegistry(lab['app_dsn'],namespace=lab['namespace'],environment=lab['environment']).check_ready()

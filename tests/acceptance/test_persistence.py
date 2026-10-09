"""Owned upgrade and backup/restore proof; never operates on a shared database."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import httpx
import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict,make_conninfo
from prosaic_integration_lab.migrations import migrate
from prosaic_integration_lab.metadata import Metadata
from lab_runner.manifest import validate_resource
from lab_runner.stack import command
from test_approval import headers,start
from test_accounting import count
from test_scope import deliver_owned_config
from test_recovery import mutate_replica,wait_for

def test_fresh_wrong_database_cannot_silently_ignore_legacy_scope_plan(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['database_id']
    validate_resource(json.loads(command(manifest['engine'],'inspect',identifier))[0],identifier,manifest['owner'])
    database = 'scope_'+uuid.uuid4().hex
    command(manifest['engine'],'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',database)
    parameters = conninfo_to_dict(lab['migration_dsn'])
    parameters['dbname'] = database
    dsn = make_conninfo(**parameters)
    with pytest.raises(ValueError,match='scope'):
        migrate(dsn,scope_records=[{'run_id':'a'*32,'namespace':'archived','environment':'sandbox'}])
    with psycopg.connect(dsn) as connection:
        assert connection.execute("SELECT to_regnamespace('lab_app')").fetchone() == (None,)

def test_versioned_upgrade_requires_scope_and_preserves_every_existing_field(lab):
    with psycopg.connect(lab['migration_dsn']) as connection:
        columns = [row[0] for row in connection.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='lab_app' AND table_name='runs' ORDER BY ordinal_position")]
        rows = connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id').fetchall()
        records = [{'run_id':row[columns.index('run_id')],'namespace':row[columns.index('namespace')],
                    'environment':row[columns.index('environment')]} for row in rows]
        legacy_columns = [column for column in columns if column not in {'namespace','environment'}]
        originals = [[row[columns.index(column)] for column in legacy_columns] for row in rows]
        connection.execute('ALTER TABLE lab_app.runs DROP COLUMN namespace,DROP COLUMN environment')
        connection.execute('UPDATE lab_app.schema_version SET version=1')
    try:
        with pytest.raises(ValueError,match='scope'):
            migrate(lab['migration_dsn'])
        with psycopg.connect(lab['migration_dsn']) as connection:
            assert connection.execute('SELECT version FROM lab_app.schema_version').fetchall() == [(1,)]
            assert [list(row) for row in connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id')] == originals
        result = migrate(lab['migration_dsn'],scope_records=records,runtime_role='app_runtime')
        assert result == {'from_version':1,'to_version':2,'rows_preserved':len(rows)}
        assert migrate(lab['migration_dsn'],scope_records=records)['from_version'] == 2
        Metadata(lab['app_dsn']).check_ready()
        with psycopg.connect(lab['migration_dsn']) as connection:
            assert connection.execute('SELECT * FROM lab_app.runs ORDER BY run_id').fetchall() == rows
    finally:
        # Restoring the fixture uses the exact archived scopes, never inference.
        migrate(lab['migration_dsn'],scope_records=records,runtime_role='app_runtime')

def test_migration_cli_works_only_with_explicit_operator_credentials(lab):
    environment = {**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[2]/'src'),
        'LAB_OPERATOR_DSN':lab['migration_dsn']}
    command_line = [sys.executable,'-m','prosaic_integration_lab.migrations','--dsn-env','LAB_OPERATOR_DSN']
    accepted = subprocess.run(command_line,env=environment,capture_output=True,text=True,timeout=20)
    assert accepted.returncode == 0
    assert json.loads(accepted.stdout)['to_version'] == 2
    environment['LAB_OPERATOR_DSN'] = lab['app_dsn']
    denied = subprocess.run(command_line,env=environment,capture_output=True,text=True,timeout=20)
    assert denied.returncode == 1
    assert json.loads(denied.stdout)['category'] == 'InsufficientPrivilege'
    assert denied.stderr == ''

def test_owned_backup_restore_keeps_waiting_unknown_and_uncertain_without_redispatch(lab):
    manifest = json.loads(Path(lab['fixture_manifest']).read_text())
    identifier = manifest['database_id']
    state = json.loads(command(manifest['engine'],'inspect',identifier))[0]
    validate_resource(state,identifier,manifest['owner'])
    normal = start(lab,workflow='synthetic').json()
    httpx.post(lab['model']+'/control',json={'scenario':'missing_usage'},timeout=5).raise_for_status()
    try:
        unknown = start(lab,workflow='synthetic').json()
    finally:
        httpx.post(lab['model']+'/control',json={'scenario':'normal'},timeout=5).raise_for_status()
    uncertain = uuid.uuid4().hex
    with psycopg.connect(lab['migration_dsn']) as connection:
        connection.execute('''INSERT INTO lab_app.runs SELECT %s,tenant_id,actor_id,billing_account_id,
            %s,request_hash,request,workflow,assets_hash,'starting',namespace,environment
            FROM lab_app.runs WHERE run_id=%s''',(uncertain,uuid.uuid4().hex,normal['run_id']))
    before = count(lab)
    engine = manifest['engine']
    exported = subprocess.run([engine,'exec',identifier,'pg_dump','-U','postgres','-Fc','lab'],
        capture_output=True,timeout=30)
    assert exported.returncode == 0
    assert len(exported.stdout) <= 128*1024*1024
    secret_dir = Path(lab['fixture_manifest']).parent/'secrets'
    archive = secret_dir/'backup.dump'
    descriptor = os.open(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'wb') as destination: destination.write(exported.stdout)
    restored_database = 'restore_'+manifest['owner']
    command(engine,'exec',identifier,'createdb','-U','postgres','--owner=lab_migration',restored_database)
    restored = subprocess.run([engine,'exec','-i',identifier,'pg_restore','-U','postgres',
        '--exit-on-error','-d',restored_database],input=archive.read_bytes(),capture_output=True,timeout=30)
    assert restored.returncode == 0
    service = secret_dir/'service.json'
    original = service.read_text()
    config = json.loads(original)
    for name in ('harness_dsn','accounting_dsn','app_dsn'):
        values = conninfo_to_dict(config[name])
        values['dbname'] = restored_database
        config[name] = make_conninfo(**values)
    try:
        service.write_text(json.dumps(config))
        deliver_owned_config(lab)
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)
        for run in (normal,unknown):
            view = httpx.get(lab['b']+'/runs/'+run['run_id'],headers=headers(lab),timeout=5)
            assert view.status_code == 200 and view.json()['revision'] == run['revision']
        usage = httpx.get(lab['b']+'/runs/'+unknown['run_id']+'/usage',headers=headers(lab),timeout=5).json()
        assert usage['unresolved_calls'] == 1 and usage['fully_costed'] is False
        view = httpx.get(lab['b']+'/runs/'+uncertain,headers=headers(lab),timeout=5)
        assert view.status_code == 200 and view.json()['status'] == 'start_uncertain'
        assert count(lab) == before
        complete = httpx.post(lab['b']+'/runs/'+normal['run_id']+'/resume',headers=headers(lab),
            json={'choice':'approve','expected_revision':normal['revision']},timeout=10)
        assert complete.status_code == 200 and complete.json()['status'] == 'completed'
        assert httpx.get(lab['a']+'/runs/'+normal['run_id'],headers=headers(lab),timeout=5).json()['status'] == 'waiting'
        assert count(lab) == before
    finally:
        service.write_text(original)
        deliver_owned_config(lab)
        mutate_replica(lab,'kill','b')
        mutate_replica(lab,'start','b')
        wait_for(lambda:httpx.get(lab['b']+'/readyz',timeout=2).status_code == 200)

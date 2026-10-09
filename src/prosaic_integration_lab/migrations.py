"""Explicit operator migrations. Runtime requests never invoke this module."""
import argparse
import json
import os
from pathlib import Path
import re
import psycopg
from psycopg import sql
from .app_schema import COLUMNS,validate_catalog

def scope_plan(run_ids,records):
    if not run_ids and records is None:
        return {}
    if not isinstance(records,list) or len(records) > 10000:
        raise ValueError('explicit legacy scope records are required')
    result = {}
    for record in records:
        if (not isinstance(record,dict) or set(record) != {'run_id','namespace','environment'} or
            type(record['run_id']) is not str or not re.fullmatch('[0-9a-f]{32}',record['run_id']) or
            record['run_id'] in result or type(record['namespace']) is not str or
            not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',record['namespace']) or
            type(record['environment']) is not str or record['environment'] not in {'sandbox','production'}):
            raise ValueError('invalid legacy scope record')
        result[record['run_id']] = (record['namespace'],record['environment'])
    if set(result) != set(run_ids): raise ValueError('legacy scope coverage must be exact')
    return result

def check_shape(connection,version):
    tables = connection.execute('''SELECT c.relname,c.relpersistence,c.relkind FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_app' AND c.relname = ANY(%s)''',(list(COLUMNS),)).fetchall()
    columns = connection.execute('''SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_app' AND c.relname = ANY(%s) AND a.attnum>0 AND NOT a.attisdropped''',(list(COLUMNS),)).fetchall()
    constraints = connection.execute('''SELECT c.relname,pg_catalog.pg_get_constraintdef(k.oid),k.convalidated,k.contype
        FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_class c ON c.oid=k.conrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_app' AND c.relname = ANY(%s)''',(list(COLUMNS),)).fetchall()
    if version == 1:
        actual = {(table,name) for table,name,_,_ in columns}
        expected = {(table,name) for table,names in COLUMNS.items() for name in names}
        legacy = {('runs','namespace'),('runs','environment')}
        if actual != expected-legacy: raise ValueError('incompatible legacy application schema')
        # V1 differs only in these two absent scope columns. Validate all other
        # physical properties against the same application-owned catalog contract.
        columns.extend([('runs',name,'text',True) for name in ('namespace','environment')])
    validate_catalog(tables,columns,constraints)

def migrate(dsn,*,scope_records=None,runtime_role=None):
    with psycopg.connect(dsn,connect_timeout=5,
            options='-c statement_timeout=10000 -c lock_timeout=1000') as connection:
        connection.execute("SELECT pg_advisory_xact_lock(hashtext('prosaic.lab_app.migration'))")
        existing = connection.execute("SELECT to_regclass('lab_app.schema_version')").fetchone()[0]
        if existing is None:
            scope_plan([],scope_records)
            objects = connection.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='lab_app'").fetchone()[0]
            if objects: raise ValueError('unversioned application schema requires operator review')
            version = 0
            connection.execute('CREATE SCHEMA IF NOT EXISTS lab_app')
            connection.execute('CREATE TABLE lab_app.schema_version (version integer PRIMARY KEY)')
            connection.execute('''CREATE TABLE lab_app.runs (
                run_id text PRIMARY KEY,tenant_id text NOT NULL,actor_id text NOT NULL,
                billing_account_id text NOT NULL,idempotency_key text NOT NULL,request_hash text NOT NULL,
                request jsonb NOT NULL,workflow text NOT NULL,assets_hash text NOT NULL,
                phase text NOT NULL CHECK (phase IN ('reserved','starting','started')),
                namespace text NOT NULL,environment text NOT NULL,UNIQUE(tenant_id,actor_id,idempotency_key))''')
            connection.execute('INSERT INTO lab_app.schema_version VALUES (2)')
        else:
            versions = connection.execute('SELECT version FROM lab_app.schema_version FOR UPDATE').fetchall()
            if versions not in ([(1,)],[(2,)]): raise ValueError('unsupported application schema version')
            version = versions[0][0]
            check_shape(connection,version)
            if version == 1:
                identifiers = [row[0] for row in connection.execute('SELECT run_id FROM lab_app.runs FOR UPDATE').fetchall()]
                plan = scope_plan(identifiers,scope_records)
                connection.execute('ALTER TABLE lab_app.runs ADD COLUMN namespace text,ADD COLUMN environment text')
                for identifier,(namespace,environment) in plan.items():
                    connection.execute('UPDATE lab_app.runs SET namespace=%s,environment=%s WHERE run_id=%s',
                        (namespace,environment,identifier))
                connection.execute('ALTER TABLE lab_app.runs ALTER COLUMN namespace SET NOT NULL,ALTER COLUMN environment SET NOT NULL')
                connection.execute('UPDATE lab_app.schema_version SET version=2 WHERE version=1')
        check_shape(connection,2)
        if version == 2 and scope_records is not None:
            existing_scope = {row[0]:(row[1],row[2]) for row in connection.execute(
                'SELECT run_id,namespace,environment FROM lab_app.runs').fetchall()}
            if scope_plan(list(existing_scope),scope_records) != existing_scope:
                raise ValueError('existing frozen scope cannot be changed')
        rows = connection.execute('SELECT count(*) FROM lab_app.runs').fetchone()[0]
        if runtime_role is not None:
            if type(runtime_role) is not str or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,62}',runtime_role):
                raise ValueError('invalid runtime role')
            role = sql.Identifier(runtime_role)
            connection.execute(sql.SQL('GRANT USAGE ON SCHEMA lab_app TO {}').format(role))
            connection.execute(sql.SQL('GRANT SELECT ON lab_app.schema_version TO {}').format(role))
            connection.execute(sql.SQL('GRANT SELECT,INSERT ON lab_app.runs TO {}').format(role))
            connection.execute(sql.SQL('GRANT UPDATE(phase) ON lab_app.runs TO {}').format(role))
    return {'from_version':version,'to_version':2,'rows_preserved':rows}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dsn-env',required=True)
    parser.add_argument('--scope-records',type=Path)
    parser.add_argument('--runtime-role')
    args = parser.parse_args()
    try:
        dsn = os.environ.get(args.dsn_env)
        if not dsn: raise ValueError('operator DSN is missing')
        records = None
        if args.scope_records:
            if args.scope_records.stat().st_size > 1048576: raise ValueError('scope records too large')
            records = json.loads(args.scope_records.read_text())
        result = migrate(dsn,scope_records=records,runtime_role=args.runtime_role)
        print(json.dumps({'event':'migration_complete',**result}))
        return 0
    except Exception as error:
        print(json.dumps({'event':'migration_failed','category':type(error).__name__}))
        return 1

if __name__ == '__main__': raise SystemExit(main())

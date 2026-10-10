"""Execute adapter SQL locally; this is not PostgreSQL qualification evidence.

Only placeholders, Jsonb transport and PostgreSQL advisory lock calls are
translated. Real engine locking, DDL/grants and migration need the owned lane.
"""
from contextlib import contextmanager
import json
import sqlite3
from psycopg.types.json import Jsonb


class Result:
    def __init__(self, cursor):
        self.cursor = cursor
        self.rowcount = cursor.rowcount

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        value = dict(row)
        for name in ('request','reference','outcome'):
            if value.get(name) is not None:
                value[name] = json.loads(value[name])
        return value


class Connection:
    def __init__(self, db): self.db = db
    def execute(self, statement, params=()):
        if statement.startswith('SELECT pg_advisory_xact_lock'):
            return Result(self.db.execute('SELECT 1'))
        return Result(self.db.execute(statement.replace('%s','?'),
            tuple(json.dumps(value.obj) if isinstance(value,Jsonb) else value for value in params)))


def database(path):
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE runs (run_id TEXT PRIMARY KEY, tenant_id TEXT, actor_id TEXT,
                billing_account_id TEXT, idempotency_key TEXT, request_hash TEXT,request TEXT,
                workflow TEXT, assets_hash TEXT,phase TEXT,namespace TEXT,environment TEXT,
                UNIQUE(tenant_id,actor_id,idempotency_key));
            CREATE TABLE proposals (proposal_id TEXT PRIMARY KEY,tenant_id TEXT,actor_id TEXT,
                idempotency_key TEXT,request_digest TEXT,proposal_json TEXT,bundle_version TEXT,
                bundle_identity TEXT,policy_digest TEXT,workflow_fingerprint TEXT,reference TEXT,
                UNIQUE(tenant_id,actor_id,idempotency_key));
            CREATE TABLE native_runs (run_id TEXT PRIMARY KEY,proposal_id TEXT,tenant_id TEXT,actor_id TEXT);
            CREATE TABLE tool_operations (operation_namespace TEXT,operation_key TEXT,signature TEXT,
                claim_token TEXT,state TEXT,outcome TEXT,PRIMARY KEY(operation_namespace,operation_key));
        ''')
    @contextmanager
    def connect():
        db = sqlite3.connect(':memory:', timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('ATTACH DATABASE ? AS lab_app',(str(path),))
        db.execute('BEGIN IMMEDIATE')
        try:
            with db:
                yield Connection(db)
        finally:
            db.close()
    return connect

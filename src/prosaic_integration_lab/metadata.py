import hashlib
import json
import uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

def canonical_request(request):
    if set(request) - {'task', 'workflow'} or not isinstance(request.get('task'), str) or len(request['task']) > 2048:
        raise ValueError('invalid request')
    if request.get('workflow', 'approval') not in {'approval', 'synthetic'}:
        raise ValueError('invalid workflow')
    content = json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(content.encode()) > 8192:
        raise ValueError('request too large')
    return content

class RequestConflict(ValueError):
    pass

class Metadata:
    def __init__(self, dsn):
        self.dsn = dsn

    def connection(self):
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5,
                               options='-c statement_timeout=5000 -c lock_timeout=1000')

    def check_ready(self):
        with self.connection() as conn:
            if conn.execute('SELECT version FROM lab_app.schema_version').fetchall() != [{'version': 2}]:
                raise ValueError('incompatible app schema')
            conn.execute('''SELECT run_id,tenant_id,actor_id,billing_account_id,idempotency_key,
                request_hash,request,workflow,assets_hash,phase,namespace,environment
                FROM lab_app.runs LIMIT 0''')

    def reserve(self, principal, key, payload, assets_hash, *, namespace, environment):
        request_hash = hashlib.sha256(canonical_request(payload).encode()).hexdigest()
        with self.connection() as conn:
            conn.execute('''INSERT INTO lab_app.runs
                (run_id,tenant_id,actor_id,billing_account_id,idempotency_key,request_hash,
                 request,workflow,assets_hash,phase,namespace,environment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'reserved',%s,%s)
                ON CONFLICT(tenant_id,actor_id,idempotency_key) DO NOTHING''',
                (uuid.uuid4().hex, principal.tenant_id, principal.actor_id, principal.billing_account_id,
                 key, request_hash, Jsonb(payload), payload['workflow'], assets_hash, namespace, environment))
            row = conn.execute('SELECT * FROM lab_app.runs WHERE tenant_id=%s AND actor_id=%s AND idempotency_key=%s',
                               (principal.tenant_id, principal.actor_id, key)).fetchone()
            if row['request_hash'] != request_hash:
                raise RequestConflict('idempotency_conflict')
            return row

    def owned(self, principal, run_id):
        with self.connection() as conn:
            return conn.execute('SELECT * FROM lab_app.runs WHERE run_id=%s AND tenant_id=%s AND actor_id=%s',
                                (run_id, principal.tenant_id, principal.actor_id)).fetchone()

    def claim_start(self, run_id):
        with self.connection() as conn:
            return conn.execute("UPDATE lab_app.runs SET phase='starting' WHERE run_id=%s AND phase='reserved' RETURNING run_id",
                                (run_id,)).fetchone() is not None

    def started(self, run_id):
        with self.connection() as conn:
            conn.execute("UPDATE lab_app.runs SET phase='started' WHERE run_id=%s AND phase='starting'", (run_id,))

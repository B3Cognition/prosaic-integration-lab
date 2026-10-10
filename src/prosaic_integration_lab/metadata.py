import hashlib
import json
import uuid
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from fastapi import HTTPException

RESERVATION_LOCK_ID=0x505253414943

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


def canonical_native_request(proposal_id, inputs):
    from .proposals import bounded_text, canonical_proposal
    try:
        bounded_text(proposal_id)
        if type(inputs) not in (type(None),bool,int,float,str,list,dict):
            raise ValueError('invalid_request')
        body = json.dumps({'proposal_id':proposal_id, 'inputs':inputs}, ensure_ascii=False,
                          sort_keys=True, separators=(',', ':'), allow_nan=False)
        return 'native-run-v1\n' + canonical_proposal(body)
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError):
        raise ValueError('invalid_request') from None

class Metadata:
    def __init__(self, dsn):
        self.dsn = dsn

    def connection(self):
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5,
                               options='-c statement_timeout=5000 -c lock_timeout=1000')

    def check_ready(self):
        from .app_schema import check_ready
        with self.connection() as conn:
            check_ready(conn)

    def phase_counts(self,namespace,environment):
        with self.connection() as conn:
            rows=conn.execute('''SELECT phase,count(*) AS count FROM lab_app.runs
                WHERE namespace=%s AND environment=%s GROUP BY phase''',(namespace,environment)).fetchall()
            return {row['phase']:row['count'] for row in rows}

    def retention_page(self,namespace,environment,after='',limit=100):
        if type(limit) is not int or not 1 <= limit <= 100: raise ValueError('invalid archive page size')
        with self.connection() as conn:
            return conn.execute('''SELECT * FROM lab_app.runs WHERE namespace=%s AND environment=%s
                AND run_id>%s ORDER BY run_id LIMIT %s''',(namespace,environment,after,limit)).fetchall()

    def billing_reservations(self):
        with self.connection() as conn:
            return conn.execute('''SELECT namespace,environment,tenant_id,actor_id,
                billing_account_id,run_id FROM lab_app.runs ORDER BY run_id''').fetchall()

    def reserve(self, principal, key, payload, assets_hash, *, namespace, environment,max_runs=10000,max_tenant_runs=10000):
        if (type(max_runs) is not int or type(max_tenant_runs) is not int or
            not 1 <= max_tenant_runs <= max_runs <= 10000): raise ValueError('invalid retention capacity')
        request_hash = hashlib.sha256(canonical_request(payload).encode()).hexdigest()
        with self.connection() as conn:
            lookup='SELECT * FROM lab_app.runs WHERE tenant_id=%s AND actor_id=%s AND idempotency_key=%s'
            identity=(principal.tenant_id,principal.actor_id,key)
            row=conn.execute(lookup,identity).fetchone()
            if row is not None:
                if row['request_hash']!=request_hash: raise RequestConflict('idempotency_conflict')
                return row
            conn.execute('SELECT pg_advisory_xact_lock(%s::bigint)',(RESERVATION_LOCK_ID,))
            row=conn.execute(lookup,identity).fetchone()
            if row is not None:
                if row['request_hash']!=request_hash: raise RequestConflict('idempotency_conflict')
                return row
            counts=conn.execute('''SELECT count(*) AS total,
                count(*) FILTER (WHERE tenant_id=%s) AS tenant FROM lab_app.runs''',(principal.tenant_id,)).fetchone()
            if counts['total']>=max_runs or counts['tenant']>=max_tenant_runs:
                raise HTTPException(503,'retention_capacity_exhausted')
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

    def reserve_native(self, principal, key, proposal, inputs, *, namespace, environment,
                       max_runs=10000, max_tenant_runs=10000):
        from .proposals import bounded_text, capacity
        proposal_id = proposal['proposal_id']
        content = canonical_native_request(proposal_id, inputs)
        request_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        lookup = 'SELECT * FROM lab_app.runs WHERE tenant_id=%s AND actor_id=%s AND idempotency_key=%s'
        identity = (principal.tenant_id, principal.actor_id, key)
        with self.connection() as connection:
            def replay():
                row = connection.execute(lookup, identity).fetchone()
                if row is not None and row['request_hash'] != request_hash:
                    raise RequestConflict('idempotency_conflict')
                return row
            row = replay()
            if row is not None:
                return row
            capacity(max_runs,max_tenant_runs)
            for value in (*identity, principal.billing_account_id, namespace):
                bounded_text(value)
            if environment not in {'sandbox','production'}:
                raise ValueError('invalid_request')
            connection.execute('SELECT pg_advisory_xact_lock(%s::bigint)', (RESERVATION_LOCK_ID,))
            row = replay()
            if row is not None:
                return row
            owned = connection.execute('''SELECT * FROM lab_app.proposals
                WHERE proposal_id=%s AND tenant_id=%s AND actor_id=%s''',
                (proposal_id, principal.tenant_id, principal.actor_id)).fetchone()
            if owned is None:
                raise HTTPException(404,'not_found')
            counts = connection.execute('''SELECT count(*) AS total,
                count(*) FILTER (WHERE tenant_id=%s) AS tenant FROM lab_app.runs''',
                (principal.tenant_id,)).fetchone()
            if counts['total'] >= max_runs or counts['tenant'] >= max_tenant_runs:
                raise HTTPException(503,'retention_capacity_exhausted')
            run_id = uuid.uuid4().hex
            connection.execute('''INSERT INTO lab_app.runs
                (run_id,tenant_id,actor_id,billing_account_id,idempotency_key,request_hash,
                 request,workflow,assets_hash,phase,namespace,environment)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'native',%s,'reserved',%s,%s)''',
                (run_id,principal.tenant_id,principal.actor_id,principal.billing_account_id,key,request_hash,
                 Jsonb({'proposal_id':proposal_id,'inputs':inputs}),owned['bundle_identity'],namespace,environment))
            connection.execute('''INSERT INTO lab_app.native_runs(run_id,proposal_id,tenant_id,actor_id)
                VALUES (%s,%s,%s,%s)''',(run_id,proposal_id,principal.tenant_id,principal.actor_id))
            return replay()

    def claim_start(self, run_id):
        with self.connection() as conn:
            return conn.execute("UPDATE lab_app.runs SET phase='starting' WHERE run_id=%s AND phase='reserved' RETURNING run_id",
                                (run_id,)).fetchone() is not None

    def started(self, run_id):
        with self.connection() as conn:
            conn.execute("UPDATE lab_app.runs SET phase='started' WHERE run_id=%s AND phase='starting'", (run_id,))

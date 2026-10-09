"""Application-owned outbox. Migration is explicit; payloads are immutable."""
import uuid
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def migrate(dsn,role='billing_exporter'):
    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('lab_billing.migration'))")
        conn.execute('CREATE SCHEMA IF NOT EXISTS lab_billing')
        conn.execute('CREATE TABLE IF NOT EXISTS lab_billing.version (version integer PRIMARY KEY CHECK(version=1))')
        conn.execute('INSERT INTO lab_billing.version VALUES (1) ON CONFLICT DO NOTHING')
        conn.execute('''CREATE TABLE IF NOT EXISTS lab_billing.sources (
            source text PRIMARY KEY,scope text NOT NULL,hash text NOT NULL,
            evidence_hash text NOT NULL,mapping jsonb NOT NULL,locator jsonb NOT NULL,exclusion text,
            conflict boolean NOT NULL DEFAULT false)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS lab_billing.events (
            key text PRIMARY KEY,source text NOT NULL REFERENCES lab_billing.sources(source),
            payload jsonb NOT NULL,state text NOT NULL DEFAULT 'pending'
                CHECK(state IN ('pending','acknowledged','failed','conflict')),
            token text,lease_until timestamptz,attempts integer NOT NULL DEFAULT 0,
            retry_at timestamptz NOT NULL DEFAULT clock_timestamp(),category text)''')
        conn.execute('CREATE TABLE IF NOT EXISTS lab_billing.mappings (scope text PRIMARY KEY,payload jsonb NOT NULL)')
        target = sql.Identifier(role)
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA lab_billing,lab_app TO {}').format(target))
        conn.execute(sql.SQL('GRANT SELECT ON lab_billing.version TO {}').format(target))
        conn.execute(sql.SQL('GRANT SELECT,INSERT ON lab_billing.sources,lab_billing.events,lab_billing.mappings TO {}').format(target))
        conn.execute(sql.SQL('GRANT UPDATE(hash,evidence_hash,exclusion,conflict) ON lab_billing.sources TO {}').format(target))
        conn.execute(sql.SQL('GRANT UPDATE(state,token,lease_until,attempts,retry_at,category) ON lab_billing.events TO {}').format(target))
        conn.execute(sql.SQL('GRANT SELECT(namespace,environment,tenant_id,actor_id,billing_account_id,run_id) ON lab_app.runs TO {}').format(target))
        conn.execute(sql.SQL('GRANT SELECT ON prosaic_metering_intents,prosaic_metering_observations TO {}').format(target))


class BillingStore:
    def __init__(self,dsn):
        self.dsn = dsn

    def connection(self):
        return psycopg.connect(self.dsn,row_factory=dict_row,connect_timeout=5,
            options='-c statement_timeout=5000 -c lock_timeout=2000 -c synchronous_commit=on')

    def check_ready(self):
        with self.connection() as conn:
            if conn.execute('SELECT version FROM lab_billing.version').fetchall() != [{'version':1}]:
                raise ValueError('billing schema incompatible')
            conn.execute('SELECT source,scope,hash,evidence_hash,mapping,locator,exclusion,conflict FROM lab_billing.sources LIMIT 0')
            conn.execute('SELECT key,source,payload,state,token,lease_until,attempts,retry_at,category FROM lab_billing.events LIMIT 0')
            conn.execute('SELECT scope,payload FROM lab_billing.mappings LIMIT 0')
            contracts = {
                'version': {'version':('integer',True)},
                'sources': {**{k:('text',True) for k in ('source','scope','hash','evidence_hash')},
                    'mapping':('jsonb',True),'locator':('jsonb',True),'exclusion':('text',False),'conflict':('boolean',True)},
                'events': {**{k:('text',True) for k in ('key','source','state')},'payload':('jsonb',True),
                    'token':('text',False),'lease_until':('timestamp with time zone',False),
                    'attempts':('integer',True),'retry_at':('timestamp with time zone',True),'category':('text',False)},
                'mappings': {'scope':('text',True),'payload':('jsonb',True)},
            }
            rows = conn.execute('''SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod) AS kind,
                a.attnotnull,c.relpersistence,c.relkind FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='lab_billing'
                AND c.relname=ANY(%s) AND a.attnum>0 AND NOT a.attisdropped''',(list(contracts),)).fetchall()
            actual = {table:{} for table in contracts}
            for row in rows:
                if row['relpersistence'] != 'p' or row['relkind'] != 'r':
                    raise ValueError('billing storage must be durable tables')
                actual[row['relname']][row['attname']] = (row['kind'],row['attnotnull'])
            if actual != contracts: raise ValueError('billing column contract incompatible')
            for table in ('sources','events','mappings'):
                for privilege in ('SELECT','INSERT'):
                    if not conn.execute('SELECT has_table_privilege(current_user,%s,%s) AS ok',
                            ('lab_billing.'+table,privilege)).fetchone()['ok']:
                        raise ValueError('billing grants missing')
            for table,columns in [('sources',('hash','evidence_hash','exclusion','conflict')),
                ('events',('state','token','lease_until','attempts','retry_at','category'))]:
                for column in columns:
                    if not conn.execute('SELECT has_column_privilege(current_user,%s,%s,%s) AS ok',
                            ('lab_billing.'+table,column,'UPDATE')).fetchone()['ok']:
                        raise ValueError('billing update grant missing')
            required = {
                ('version','version_pkey'): 'PRIMARY KEY (version)',
                ('version','version_version_check'): 'CHECK ((version = 1))',
                ('sources','sources_pkey'): 'PRIMARY KEY (source)',
                ('events','events_pkey'): 'PRIMARY KEY (key)',
                ('events','events_source_fkey'): 'FOREIGN KEY (source) REFERENCES lab_billing.sources(source)',
                ('events','events_state_check'): "CHECK ((state = ANY (ARRAY['pending'::text, 'acknowledged'::text, 'failed'::text, 'conflict'::text])))",
                ('mappings','mappings_pkey'): 'PRIMARY KEY (scope)',
            }
            rows = conn.execute('''SELECT c.relname,k.conname,k.convalidated,pg_get_constraintdef(k.oid) AS definition
                FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
                JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='lab_billing' ''').fetchall()
            constraints = {(r['relname'],r['conname']):r['definition'] for r in rows if r['convalidated']}
            if any(constraints.get(k) != v for k,v in required.items()):
                raise ValueError('billing constraint contract incompatible')

    def mapping(self,scope,payload):
        with self.connection() as conn:
            conn.execute('INSERT INTO lab_billing.mappings VALUES (%s,%s) ON CONFLICT DO NOTHING',(scope,Jsonb(payload)))
            stored = conn.execute('SELECT payload FROM lab_billing.mappings WHERE scope=%s',(scope,)).fetchone()['payload']
            if stored != payload: raise ValueError('billing mapping conflict')
            return stored

    def get_mapping(self,scope):
        with self.connection() as conn:
            row = conn.execute('SELECT payload FROM lab_billing.mappings WHERE scope=%s',(scope,)).fetchone()
            if row is None: raise ValueError('billing mapping missing')
            return row['payload']

    def enqueue(self,p):
        conflict = False
        with self.connection() as conn:
            conn.execute('''INSERT INTO lab_billing.sources (source,scope,hash,evidence_hash,mapping,locator,exclusion)
                VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
                (p['source'],p['scope'],p['hash'],p['evidence_hash'],Jsonb(p['mapping']),Jsonb(p['locator']),p['exclusion']))
            existing = conn.execute('SELECT * FROM lab_billing.sources WHERE source=%s FOR UPDATE',(p['source'],)).fetchone()
            if existing['conflict']:
                conflict = True
            elif existing['hash'] != p['hash']:
                same_intent = (existing['mapping'] == p['mapping'] and existing['scope'] == p['scope']
                               and existing['locator'] == p['locator'])
                # A scan started before observation may finish after a newer scan.
                # Ignore only that provably older no-observation snapshot.
                if (same_intent and p['exclusion'] == 'unresolved' and p['evidence_hash'] == p['unobserved_hash']
                        and existing['evidence_hash'] != p['unobserved_hash']):
                    return
                # Only absence of an observation permits a first observation,
                # never replacement of a persisted partial/unknown observation.
                if same_intent and existing['exclusion'] == 'unresolved' and existing['evidence_hash'] == p['unobserved_hash']:
                    conn.execute('UPDATE lab_billing.sources SET hash=%s,evidence_hash=%s,exclusion=%s WHERE source=%s',
                        (p['hash'],p['evidence_hash'],p['exclusion'],p['source']))
                else:
                    conflict = True
                    conn.execute('UPDATE lab_billing.sources SET conflict=true WHERE source=%s',(p['source'],))
                    conn.execute("UPDATE lab_billing.events SET state='conflict',token=NULL,lease_until=NULL WHERE source=%s",(p['source'],))
            if not conflict:
                for event in p['events']:
                    conn.execute('INSERT INTO lab_billing.events (key,source,payload) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                        (event['transaction_id'],p['source'],Jsonb(event)))
        if conflict: raise ValueError('billing projection conflict')

    def claim(self,limit=30,lease_seconds=30,*,scope=None):
        if type(limit) is not int or not 1 <= limit <= 100 or type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ValueError('invalid billing claim limits')
        with self.connection() as conn:
            rows = conn.execute('''SELECT e.key,e.payload,s.locator,s.mapping,s.hash FROM lab_billing.events e
                JOIN lab_billing.sources s ON s.source=e.source WHERE e.state='pending' AND NOT s.conflict
                AND NOT EXISTS (SELECT 1 FROM lab_billing.events bad WHERE bad.source=e.source AND bad.state IN ('failed','conflict'))
                AND e.retry_at<=clock_timestamp() AND (e.lease_until IS NULL OR e.lease_until<clock_timestamp())
                AND (%s::text IS NULL OR s.scope=%s) ORDER BY e.key FOR UPDATE OF e SKIP LOCKED LIMIT %s''',
                (scope,scope,limit)).fetchall()
            for row in rows:
                row['token'] = uuid.uuid4().hex
                conn.execute('''UPDATE lab_billing.events SET token=%s,
                    lease_until=clock_timestamp()+%s*interval '1 second',attempts=attempts+1 WHERE key=%s''',
                    (row['token'],lease_seconds,row['key']))
                row['attempts'] = conn.execute('SELECT attempts FROM lab_billing.events WHERE key=%s',(row['key'],)).fetchone()['attempts']
            return rows

    def ack(self,key,token):
        with self.connection() as conn:
            return conn.execute('''UPDATE lab_billing.events SET state='acknowledged',token=NULL,lease_until=NULL,category=NULL
                WHERE key=%s AND token=%s AND state='pending' AND lease_until>clock_timestamp() RETURNING key''',
                (key,token)).fetchone() is not None

    def fail(self,key,token,category,delay=None):
        if category not in {'transport','throttled','server','authentication','validation','conflict','exhausted','period'}:
            raise ValueError('invalid failure category')
        state = 'pending' if delay is not None else 'conflict' if category == 'conflict' else 'failed'
        with self.connection() as conn:
            # Match enqueue's source-before-event lock order to avoid deadlock.
            source = conn.execute('SELECT source FROM lab_billing.events WHERE key=%s',(key,)).fetchone()
            if source is None: return False
            conn.execute('SELECT source FROM lab_billing.sources WHERE source=%s FOR UPDATE',(source['source'],))
            updated = conn.execute('''UPDATE lab_billing.events SET state=%s,token=NULL,lease_until=NULL,category=%s,
                retry_at=clock_timestamp()+%s*interval '1 second'
                WHERE key=%s AND token=%s AND state='pending' AND lease_until>clock_timestamp() RETURNING key''',
                (state,category,delay or 0,key,token)).fetchone() is not None
            if updated and category == 'conflict':
                conn.execute('UPDATE lab_billing.sources SET conflict=true WHERE source=%s',(source['source'],))
                conn.execute("UPDATE lab_billing.events SET state='conflict',token=NULL,lease_until=NULL,category='conflict' WHERE source=%s",(source['source'],))
            return updated

    def events(self,scope):
        with self.connection() as conn:
            return conn.execute('''SELECT e.* FROM lab_billing.events e JOIN lab_billing.sources s USING(source)
                WHERE s.scope=%s ORDER BY e.key''',(scope,)).fetchall()

    def summary(self,scope=None):
        with self.connection() as conn:
            return {r['state']:r['n'] for r in conn.execute('''SELECT state,count(*) AS n FROM lab_billing.events e
                JOIN lab_billing.sources s USING(source) WHERE (%s::text IS NULL OR s.scope=%s) GROUP BY state''',(scope,scope))}

    def sources(self):
        with self.connection() as conn:
            return conn.execute('SELECT source,scope,exclusion,conflict FROM lab_billing.sources ORDER BY source').fetchall()

"""Explicit host registry initialization; workers only check this separate schema."""
import psycopg
from psycopg import sql
from psycopg.rows import tuple_row


TEXT_LIMITS={'session_id':32,'tenant_id':128,'actor_id':128,'billing_account_id':128,
    'idempotency_key':128,'binding_identity':64,'binding_version':128,'namespace':128,
    'environment':32,'application':128,'phase':16}
LINK_LIMITS={'session_id':32,'registration':128,'source_message_id':128,'source_revision':64,'phase':16}
COLUMNS={'schema_version':{'version':('integer',True)},
    'sessions':{name:('text',True) for name in TEXT_LIMITS},
    'workflow_links':{name:('text',True) for name in LINK_LIMITS}}
CONSTRAINTS={'schema_version':{'PRIMARY KEY (version)'},'sessions':{
    'PRIMARY KEY (session_id)',
    'UNIQUE (namespace, environment, tenant_id, actor_id, idempotency_key)',
    "CHECK ((phase = ANY (ARRAY['reserved'::text, 'created'::text])))",
    *{f'CHECK ((octet_length({name}) <= {limit}))' for name,limit in TEXT_LIMITS.items()}},
    'workflow_links':{'PRIMARY KEY (session_id)',
    'FOREIGN KEY (session_id) REFERENCES lab_chat.sessions(session_id)',
    "CHECK ((phase = ANY (ARRAY['reserved'::text, 'starting'::text, 'started'::text, 'attached'::text])))",
    *{f'CHECK ((octet_length({name}) <= {limit}))' for name,limit in LINK_LIMITS.items()}}}


def validate_catalog(tables,columns,constraints):
    actual={table:{} for table in COLUMNS}
    if {row[0] for row in tables}!=set(COLUMNS) or any(row[1:]!=('p','r') for row in tables):
        raise ValueError('incompatible conversation registry')
    for table,name,kind,notnull in columns:
        if table not in actual:raise ValueError('incompatible conversation registry')
        actual[table][name]=(kind,notnull)
    if actual!=COLUMNS:raise ValueError('incompatible conversation registry')
    checks={table:set() for table in COLUMNS}
    for table,definition,validated,kind in constraints:
        if table not in checks or not validated:raise ValueError('incompatible conversation registry')
        if kind!='n':checks[table].add(definition)
    if checks!=CONSTRAINTS:raise ValueError('incompatible conversation registry')


def _contract(cursor):
    cursor.execute('''SELECT c.relname,c.relpersistence,c.relkind FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_chat' AND c.relname=ANY(%s)''',(list(COLUMNS),))
    tables=cursor.fetchall()
    cursor.execute('''SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_chat' AND c.relname=ANY(%s) AND a.attnum>0 AND NOT a.attisdropped''',(list(COLUMNS),))
    columns=cursor.fetchall()
    cursor.execute('''SELECT c.relname,pg_catalog.pg_get_constraintdef(k.oid),k.convalidated,k.contype
        FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_class c ON c.oid=k.conrelid
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='lab_chat' AND c.relname=ANY(%s)''',(list(COLUMNS),))
    validate_catalog(tables,columns,cursor.fetchall())
    cursor.execute('SELECT version FROM lab_chat.schema_version')
    if cursor.fetchall()!=[(1,)]:raise ValueError('incompatible conversation registry version')


def check_ready(connection):
    with connection.cursor(row_factory=tuple_row) as cursor:
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        _contract(cursor)
        def required(statement,params,expected):
            cursor.execute(statement,params)
            if cursor.fetchone()!=(expected,):raise ValueError('conversation registry grants unavailable')
        required("SELECT has_schema_privilege(current_user,'lab_chat','USAGE')",(),True)
        required("SELECT has_schema_privilege(current_user,'lab_chat','CREATE')",(),False)
        for table,privileges in (('schema_version',('SELECT',)),('sessions',('SELECT','INSERT')),
                                ('workflow_links',('SELECT','INSERT'))):
            for privilege in privileges:
                required('SELECT has_table_privilege(current_user,%s,%s)',('lab_chat.'+table,privilege),True)
            for privilege in ('DELETE','TRUNCATE','TRIGGER'):
                required('SELECT has_table_privilege(current_user,%s,%s)',('lab_chat.'+table,privilege),False)
            for column in COLUMNS[table]:
                required('SELECT has_column_privilege(current_user,%s,%s,\'UPDATE\')',
                    ('lab_chat.'+table,column),table in {'sessions','workflow_links'} and column=='phase')
        required("SELECT has_table_privilege(current_user,'lab_chat.schema_version','INSERT')",(),False)


def initialize(dsn,*,runtime_role='app_runtime'):
    """Operator-only creation. Existing incompatible state is never repaired."""
    with psycopg.connect(dsn,connect_timeout=5,options='-c statement_timeout=5000 -c lock_timeout=1000') as connection:
        with connection.cursor(row_factory=tuple_row) as cursor:
            cursor.execute("SELECT to_regnamespace('lab_chat')")
            if cursor.fetchone()==(None,):
                cursor.execute('CREATE SCHEMA lab_chat')
                cursor.execute('CREATE TABLE lab_chat.schema_version(version integer PRIMARY KEY)')
                fields=sql.SQL(',').join(sql.SQL('{} text NOT NULL CHECK(octet_length({}) <= {})').format(
                    sql.Identifier(name),sql.Identifier(name),sql.Literal(limit)) for name,limit in TEXT_LIMITS.items())
                cursor.execute(sql.SQL('''CREATE TABLE lab_chat.sessions({},PRIMARY KEY(session_id),
                    UNIQUE(namespace,environment,tenant_id,actor_id,idempotency_key),
                    CHECK(phase IN ('reserved','created')))''').format(fields))
                fields=sql.SQL(',').join(sql.SQL('{} text NOT NULL CHECK(octet_length({}) <= {})').format(
                    sql.Identifier(name),sql.Identifier(name),sql.Literal(limit)) for name,limit in LINK_LIMITS.items())
                cursor.execute(sql.SQL('''CREATE TABLE lab_chat.workflow_links({},PRIMARY KEY(session_id),
                    FOREIGN KEY(session_id) REFERENCES lab_chat.sessions(session_id),
                    CHECK(phase IN ('reserved','starting','started','attached')))''').format(fields))
                cursor.execute('INSERT INTO lab_chat.schema_version VALUES(1)')
            _contract(cursor)
            cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA lab_chat TO {}').format(sql.Identifier(runtime_role)))
            cursor.execute(sql.SQL('GRANT SELECT ON lab_chat.schema_version TO {}').format(sql.Identifier(runtime_role)))
            for table in ('sessions','workflow_links'):
                cursor.execute(sql.SQL('GRANT SELECT,INSERT ON lab_chat.{} TO {}').format(
                    sql.Identifier(table),sql.Identifier(runtime_role)))
                cursor.execute(sql.SQL('GRANT UPDATE(phase) ON lab_chat.{} TO {}').format(
                    sql.Identifier(table),sql.Identifier(runtime_role)))

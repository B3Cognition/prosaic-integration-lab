"""Application-owned schema contract; readiness never repairs storage."""
COLUMNS_V2 = {
    'schema_version': {'version': ('integer',True)},
    'runs': {name: ('jsonb' if name == 'request' else 'text',True) for name in
        ('run_id','tenant_id','actor_id','billing_account_id','idempotency_key','request_hash',
         'request','workflow','assets_hash','phase','namespace','environment')},
}
CONSTRAINTS_V2 = {
    'schema_version': {'PRIMARY KEY (version)'},
    'runs': {'PRIMARY KEY (run_id)', 'UNIQUE (tenant_id, actor_id, idempotency_key)',
             "CHECK ((phase = ANY (ARRAY['reserved'::text, 'starting'::text, 'started'::text])))"},
}

COLUMNS_V1 = {table: {name: kind for name, kind in columns.items()
    if (table, name) not in {('runs', 'namespace'), ('runs', 'environment')}}
    for table, columns in COLUMNS_V2.items()}
COLUMNS = {**COLUMNS_V2,
    'proposals': {name: ('jsonb' if name == 'reference' else 'text', True) for name in
        ('proposal_id','tenant_id','actor_id','idempotency_key','request_digest','proposal_json',
         'bundle_version','bundle_identity','policy_digest','workflow_fingerprint','reference')},
    'native_runs': {name: ('text',True) for name in ('run_id','proposal_id','tenant_id','actor_id')},
    'tool_operations': {**{name: ('text',True) for name in
        ('operation_namespace','operation_key','signature','claim_token','state')}, 'outcome': ('jsonb',False)},
}
TEXT_LIMITS = {
    'proposals': {'proposal_id':128,'tenant_id':128,'actor_id':128,'idempotency_key':128,
        'request_digest':64,'proposal_json':65536,'bundle_version':128,'bundle_identity':64,
        'policy_digest':64,'workflow_fingerprint':64},
    'native_runs': {name:128 for name in ('run_id','proposal_id','tenant_id','actor_id')},
    'tool_operations': {'operation_namespace':128,'operation_key':128,'signature':64,'claim_token':128,'state':16},
}
CONSTRAINTS = {**CONSTRAINTS_V2,
    'proposals': {'PRIMARY KEY (proposal_id)', 'UNIQUE (tenant_id, actor_id, idempotency_key)',
        'UNIQUE (proposal_id, tenant_id, actor_id)', 'CHECK ((octet_length((reference)::text) <= 4096))'},
    'native_runs': {'PRIMARY KEY (run_id)', 'FOREIGN KEY (run_id) REFERENCES lab_app.runs(run_id)',
        'FOREIGN KEY (proposal_id, tenant_id, actor_id) REFERENCES lab_app.proposals(proposal_id, tenant_id, actor_id)'},
    'tool_operations': {'PRIMARY KEY (operation_namespace, operation_key)',
        "CHECK ((state = ANY (ARRAY['uncertain'::text, 'completed'::text])))",
        "CHECK ((((state = 'uncertain'::text) AND (outcome IS NULL)) OR ((state = 'completed'::text) AND (outcome IS NOT NULL))))",
        'CHECK ((octet_length((outcome)::text) <= 262144))'},
}
for _table, _limits in TEXT_LIMITS.items():
    CONSTRAINTS[_table].update(f'CHECK ((octet_length({field}) <= {limit}))' for field,limit in _limits.items())


def validate_catalog(tables, columns, constraints, *, version=3):
    expected_columns = {1:COLUMNS_V1,2:COLUMNS_V2,3:COLUMNS}.get(version)
    expected_constraints = CONSTRAINTS if version == 3 else CONSTRAINTS_V2
    def incompatible():
        raise ValueError('incompatible application storage contract')
    if expected_columns is None or {r[0] for r in tables} != set(expected_columns) or any(r[1:] != ('p','r') for r in tables):
        incompatible()
    actual = {table: {} for table in expected_columns}
    for table, name, kind, notnull in columns:
        if table not in actual:
            incompatible()
        actual[table][name] = (kind,notnull)
    if actual != expected_columns:
        incompatible()
    actual_constraints = {table: set() for table in expected_columns}
    for table, definition, validated, kind in constraints:
        if table not in actual_constraints or not validated:
            incompatible()
        if kind != 'n':
            actual_constraints[table].add(definition)
    if actual_constraints != expected_constraints:
        incompatible()


def check_ready(connection):
    from psycopg.rows import tuple_row
    with connection.cursor(row_factory=tuple_row) as cursor:
        cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        cursor.execute("SELECT has_schema_privilege(current_user,'lab_app','USAGE')")
        if cursor.fetchone() != (True,):
            raise ValueError('application schema access is missing')
        cursor.execute('''SELECT c.relname,c.relpersistence,c.relkind FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='lab_app' AND c.relname = ANY(%s)''', (list(COLUMNS),))
        tables = cursor.fetchall()
        cursor.execute('''SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull
            FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='lab_app' AND c.relname = ANY(%s) AND a.attnum>0 AND NOT a.attisdropped''', (list(COLUMNS),))
        columns = cursor.fetchall()
        cursor.execute('''SELECT c.relname,pg_catalog.pg_get_constraintdef(k.oid),k.convalidated,k.contype
            FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_class c ON c.oid=k.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='lab_app' AND c.relname = ANY(%s)''', (list(COLUMNS),))
        validate_catalog(tables,columns,cursor.fetchall())
        cursor.execute('SELECT version FROM lab_app.schema_version')
        if cursor.fetchall() != [(3,)]:
            raise ValueError('incompatible application schema version')
        for table, privileges in [('lab_app.schema_version', ('SELECT',)),
                *[(f'lab_app.{name}', ('SELECT','INSERT')) for name in
                  ('runs','proposals','native_runs','tool_operations')]]:
            for privilege in privileges:
                cursor.execute('SELECT has_table_privilege(current_user,%s,%s)', (table,privilege))
                if cursor.fetchone() != (True,):
                    raise ValueError('required application table privileges are missing')
        cursor.execute("SELECT has_column_privilege(current_user,'lab_app.runs','phase','UPDATE')")
        if cursor.fetchone() != (True,):
            raise ValueError('required application phase privilege is missing')
        for column in ('state','outcome'):
            cursor.execute("SELECT has_column_privilege(current_user,'lab_app.tool_operations',%s,'UPDATE')", (column,))
            if cursor.fetchone() != (True,):
                raise ValueError('required application journal privilege is missing')
        cursor.execute("SELECT has_schema_privilege(current_user,'lab_app','CREATE')")
        if cursor.fetchone() != (False,):
            raise ValueError('application role has schema owner powers')
        for table in ('proposals','native_runs','tool_operations'):
            for privilege in ('DELETE','TRUNCATE','TRIGGER'):
                cursor.execute('SELECT has_table_privilege(current_user,%s,%s)', (f'lab_app.{table}',privilege))
                if cursor.fetchone() != (False,):
                    raise ValueError('application role has mutable storage powers')
            immutable = list(COLUMNS[table]) if table != 'tool_operations' else [
                'operation_namespace','operation_key','signature','claim_token']
            for column in immutable:
                cursor.execute('SELECT has_column_privilege(current_user,%s,%s,\'UPDATE\')', (f'lab_app.{table}',column))
                if cursor.fetchone() != (False,):
                    raise ValueError('application role has mutable storage powers')

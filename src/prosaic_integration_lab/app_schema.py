"""Application-owned schema contract; readiness never repairs storage."""
COLUMNS = {
    'schema_version': {'version': ('integer',True)},
    'runs': {name: ('jsonb' if name == 'request' else 'text',True) for name in
        ('run_id','tenant_id','actor_id','billing_account_id','idempotency_key','request_hash',
         'request','workflow','assets_hash','phase','namespace','environment')},
}
CONSTRAINTS = {
    'schema_version': {'PRIMARY KEY (version)'},
    'runs': {'PRIMARY KEY (run_id)', 'UNIQUE (tenant_id, actor_id, idempotency_key)',
             "CHECK ((phase = ANY (ARRAY['reserved'::text, 'starting'::text, 'started'::text])))"},
}


def validate_catalog(tables, columns, constraints):
    def incompatible():
        raise ValueError('incompatible application storage contract')
    if {r[0] for r in tables} != set(COLUMNS) or any(r[1:] != ('p','r') for r in tables):
        incompatible()
    actual = {table: {} for table in COLUMNS}
    for table, name, kind, notnull in columns:
        if table not in actual:
            incompatible()
        actual[table][name] = (kind,notnull)
    if actual != COLUMNS:
        incompatible()
    actual_constraints = {table: set() for table in COLUMNS}
    for table, definition, validated, kind in constraints:
        if table not in actual_constraints or not validated:
            incompatible()
        if kind != 'n':
            actual_constraints[table].add(definition)
    if actual_constraints != CONSTRAINTS:
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
        if cursor.fetchall() != [(2,)]:
            raise ValueError('incompatible application schema version')
        for table, privileges in [('lab_app.schema_version', ('SELECT',)), ('lab_app.runs', ('SELECT','INSERT'))]:
            for privilege in privileges:
                cursor.execute('SELECT has_table_privilege(current_user,%s,%s)', (table,privilege))
                if cursor.fetchone() != (True,):
                    raise ValueError('required application table privileges are missing')
        cursor.execute("SELECT has_column_privilege(current_user,'lab_app.runs','phase','UPDATE')")
        if cursor.fetchone() != (True,):
            raise ValueError('required application phase privilege is missing')

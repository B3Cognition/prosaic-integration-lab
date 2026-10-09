"""Explicit provisioning job. This secret is never mounted in replicas."""
import json
import os
from pathlib import Path
import subprocess

import psycopg
from psycopg import sql
from prosaic_runtime_postgres import PostgresRecorder
from prosaic_integration_lab.migrations import migrate


def main():
    config = json.loads(Path('/run/secrets/provision.json').read_text())
    admin_dsn = f'host=database dbname=postgres user=postgres password={config["admin_password"]}'
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        for role, password in config['roles'].items():
            conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
        conn.execute('CREATE DATABASE lab OWNER lab_migration')
    migration = f'host=database dbname=lab user=lab_migration password={config["roles"]["lab_migration"]}'
    env = {**os.environ, 'HARNESS_MIGRATION_DSN': migration}
    result = subprocess.run(['prosaic-harness-postgres', 'init', '--dsn-env', 'HARNESS_MIGRATION_DSN'],
                            env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError('Harness explicit migration failed')
    PostgresRecorder(migration, namespace='provision', environment='sandbox').initialize()
    migrate(migration,runtime_role='app_runtime')
    if 'billing_exporter' in config['roles']:
        from prosaic_integration_lab.billing_store import migrate as migrate_billing
        migrate_billing(migration)
    with psycopg.connect(migration) as conn:
        conn.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
        conn.execute('GRANT USAGE ON SCHEMA prosaic_harness TO harness_runtime')
        conn.execute('GRANT SELECT ON ALL TABLES IN SCHEMA prosaic_harness TO harness_runtime')
        conn.execute('GRANT INSERT,UPDATE ON prosaic_harness.leases,prosaic_harness.runs TO harness_runtime')
        conn.execute('GRANT INSERT ON prosaic_harness.receipts TO harness_runtime')
        conn.execute('GRANT SELECT,INSERT ON prosaic_metering_intents,prosaic_metering_observations TO accounting_runtime')
        conn.execute('GRANT UPDATE ON prosaic_metering_intents TO accounting_runtime')
        conn.execute('GRANT USAGE ON SCHEMA lab_app TO app_runtime')
        conn.execute('GRANT SELECT ON lab_app.schema_version TO app_runtime')
        conn.execute('GRANT SELECT,INSERT ON lab_app.runs TO app_runtime')
        conn.execute('GRANT UPDATE(phase) ON lab_app.runs TO app_runtime')
    print('Explicit schemas and restricted roles provisioned')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Provisioning failed; secret-bearing diagnostics suppressed')

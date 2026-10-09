import psycopg
import pytest
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime_postgres import PostgresRecorder


def test_released_adapters_ready_with_restricted_credentials(lab):
    with PostgresRunStore(lab['harness_dsn'], namespace=lab['namespace']) as store:
        store.check_ready()
    PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment='sandbox').check_ready()


@pytest.mark.parametrize('dsn_key', ['harness_dsn', 'accounting_dsn', 'app_dsn'])
def test_runtime_roles_cannot_create_schema(lab, dsn_key):
    with psycopg.connect(lab[dsn_key]) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute('CREATE SCHEMA forbidden_runtime_ddl')


def test_app_schema_and_primary_durability(lab):
    with psycopg.connect(lab['app_dsn']) as conn:
        assert conn.execute('SELECT version FROM lab_app.schema_version').fetchone() == (2,)
        assert conn.execute('SELECT pg_is_in_recovery()').fetchone() == (False,)
        for setting in ('fsync', 'full_page_writes'):
            assert conn.execute('SELECT current_setting(%s)', (setting,)).fetchone() == ('on',)


def test_receipts_and_accounting_observations_are_not_amendable(lab):
    with psycopg.connect(lab['harness_dsn']) as conn:
        assert conn.execute("SELECT has_table_privilege(current_user,'prosaic_harness.receipts','UPDATE')").fetchone() == (False,)
        assert conn.execute("SELECT has_table_privilege(current_user,'prosaic_harness.receipts','DELETE')").fetchone() == (False,)
    with psycopg.connect(lab['accounting_dsn']) as conn:
        assert conn.execute("SELECT has_table_privilege(current_user,'prosaic_metering_observations','UPDATE')").fetchone() == (False,)
        assert conn.execute("SELECT has_table_privilege(current_user,'prosaic_metering_observations','DELETE')").fetchone() == (False,)

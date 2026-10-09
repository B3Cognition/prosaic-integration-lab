import uuid
import httpx

from prosaic_integration_lab.identity import Principal
from prosaic_integration_lab.metadata import Metadata
from test_approval import headers, start
from test_accounting import count


def test_starting_without_checkpoint_never_redispatches(lab):
    key = uuid.uuid4().hex
    metadata = Metadata(lab['app_dsn'])
    owner = Principal('tenant-a', 'alice', 'account-a')
    # Use the same immutable fingerprint as the existing application reservation.
    initial = start(lab).json()
    row = metadata.owned(owner, initial['run_id'])
    reservation = metadata.reserve(owner, key, {'task': 'uncertain', 'workflow': 'synthetic'}, row['assets_hash'],
                                   namespace=lab['namespace'], environment=lab['environment'])
    assert metadata.claim_start(reservation['run_id']) is True
    assert metadata.claim_start(reservation['run_id']) is False
    before = count(lab)
    response = start(lab, workflow='synthetic', key=key, task='uncertain')
    assert response.status_code == 200
    assert response.json()['status'] == 'start_uncertain'
    assert count(lab) == before
    resumed = httpx.post(lab['b'] + '/runs/' + reservation['run_id'] + '/resume', headers=headers(lab),
                        json={'expected_revision': 'unavailable', 'retry_interrupted': True}, timeout=10)
    assert resumed.status_code != 200
    assert count(lab) == before


def test_asset_mismatch_refused_before_start(lab):
    key = uuid.uuid4().hex
    metadata = Metadata(lab['app_dsn'])
    metadata.reserve(Principal('tenant-a', 'alice', 'account-a'), key,
                     {'task': 'drift', 'workflow': 'synthetic'}, 'wrong-fingerprint',
                     namespace=lab['namespace'], environment=lab['environment'])
    before = count(lab)
    response = start(lab, workflow='synthetic', key=key, task='drift')
    assert response.status_code == 409
    assert count(lab) == before


def test_missing_application_run_table_fails_readiness_without_repair(lab):
    import psycopg
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('ALTER TABLE lab_app.runs RENAME TO runs_unavailable')
    try:
        response = httpx.get(lab['a'] + '/readyz', timeout=5)
        assert response.status_code == 503
        assert response.json() == {'detail': 'not_ready'}
        with psycopg.connect(lab['migration_dsn']) as conn:
            assert conn.execute("SELECT to_regclass('lab_app.runs')").fetchone() == (None,)
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('ALTER TABLE lab_app.runs_unavailable RENAME TO runs')

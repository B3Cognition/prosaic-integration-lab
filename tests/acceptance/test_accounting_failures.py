import httpx
import psycopg

from test_approval import start, headers
from test_accounting import count


def test_prepare_failure_prevents_dispatch(lab):
    before = count(lab)
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('REVOKE INSERT ON prosaic_metering_intents FROM accounting_runtime')
    try:
        run = start(lab, workflow='synthetic').json()
        assert run['status'] == 'blocked'
        assert count(lab) == before
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('GRANT INSERT ON prosaic_metering_intents TO accounting_runtime')


def test_observation_failure_retains_unknown_without_redispatch(lab):
    before = count(lab)
    with psycopg.connect(lab['migration_dsn']) as conn:
        conn.execute('REVOKE INSERT ON prosaic_metering_observations FROM accounting_runtime')
    try:
        run = start(lab, workflow='synthetic').json()
        assert run['status'] == 'blocked'
        assert count(lab) == before + 1
        usage = httpx.get(lab['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers(lab), timeout=10).json()
        assert usage['unresolved_calls'] == 1
        assert usage['fully_costed'] is False
        assert usage['estimated_amounts'] == {}
        response = httpx.post(lab['b'] + '/runs/' + run['run_id'] + '/resume', headers=headers(lab),
                             json={'expected_revision': run['revision']}, timeout=10)
        assert response.status_code == 200
        assert count(lab) == before + 1
    finally:
        with psycopg.connect(lab['migration_dsn']) as conn:
            conn.execute('GRANT INSERT ON prosaic_metering_observations TO accounting_runtime')


def test_identical_observation_replay_does_not_duplicate_estimates(lab):
    from prosaic_runtime_postgres import PostgresRecorder
    run = start(lab, workflow='synthetic').json()
    recorder = PostgresRecorder(lab['accounting_dsn'], namespace=lab['namespace'], environment='sandbox')
    call = recorder.calls(run_id=run['run_id'])[0]
    before = recorder.report(run_id=run['run_id'])
    recorder.prepare(call['intent'])
    recorder.observe(call['intent']['provider_call_id'], call['observation'])
    after = recorder.report(run_id=run['run_id'])
    assert after['total_calls'] == before['total_calls'] == 1
    assert after['estimated_amounts'] == before['estimated_amounts']

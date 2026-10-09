"""Exercise public installed SDKs/HTTP APIs and retain filtered usage evidence."""
import uuid
import httpx
from prosaic_runtime_postgres import PostgresRecorder


def capture_accounting(config, ownership_id):
    recorder = PostgresRecorder(config['accounting_dsn'], namespace=config['namespace'],
                                environment=config['environment'])
    runs = []
    scenarios = [('alice', 'normal', 'Accepted output'), ('bob', 'normal', 'Accepted output'),
                 ('carol', 'normal', 'Accepted output'), ('alice', 'invalid_output', 'Rejected output'),
                 ('bob', 'missing_usage', 'Missing final usage')]
    with httpx.Client(timeout=30) as client:
        before = client.get(config['model'] + '/stats').json()['calls']
        try:
            for actor, scenario, label in scenarios:
                token, principal = next((token, identity) for token, identity in config['principals'].items()
                                        if identity['actor_id'] == actor)
                headers = {'Authorization': 'Bearer ' + token}
                control = client.post(config['model'] + '/control', json={'scenario': scenario})
                control.raise_for_status()
                response = client.post(config['a'] + '/runs',
                    headers={**headers, 'Idempotency-Key': uuid.uuid4().hex},
                    json={'workflow': 'synthetic', 'task': 'Neutral accounting demonstration'})
                response.raise_for_status()
                run = response.json()
                if run['status'] != ('blocked' if scenario == 'invalid_output' else 'waiting'):
                    raise ValueError('demo workflow did not reach the expected state')
                # Approve normal results on B. Rejected/missing cases retain
                # their state; no automatic retries or billing consent.
                if scenario == 'normal':
                    response = client.post(config['b'] + '/runs/' + run['run_id'] + '/resume',
                        headers=headers, json={'choice': 'approve', 'expected_revision': run['revision']})
                    response.raise_for_status()
                    run = response.json()
                    if run['status'] != 'completed':
                        raise ValueError('cross-replica approval failed')
                response = client.get(config['b'] + '/runs/' + run['run_id'] + '/usage', headers=headers)
                response.raise_for_status()
                usage = response.json()
                calls = recorder.calls(application_id='integration-lab', tenant_id=principal['tenant_id'],
                    actor_id=actor, billing_account_id=principal['billing_account_id'],
                    request_id=run['run_id'], run_id=run['run_id'])
                expected = 2 if scenario == 'invalid_output' else 1
                if usage['total_calls'] != expected or len(calls) != expected or usage['billing_eligible'] is not False:
                    raise ValueError('demo accounting evidence mismatch')
                public_calls = []
                for call in calls:
                    observation = call['observation'] or {}
                    measured = observation.get('usage') or {}
                    assessment = call['assessment'] or {}
                    public_calls.append({
                        'provider_call_id': call['intent']['provider_call_id'],
                        'provider_response_id': observation.get('provider_request_id'),
                        'response_model': observation.get('response_model'),
                        **{name: measured.get(name) for name in ('input_tokens', 'output_tokens', 'cached_input_tokens', 'total_tokens')},
                        'measurement_state': call['measurement_state'],
                        'estimate_usd': assessment.get('amount') if assessment.get('status') == 'estimated' and assessment.get('currency') == 'USD' else None,
                    })
                runs.append({'actor': actor, 'tenant': principal['tenant_id'], 'billing_account': principal['billing_account_id'],
                             'case': label, 'run_id': run['run_id'], 'status': run['status'], 'usage': usage, 'calls': public_calls})
        finally:
            client.post(config['model'] + '/control', json={}).raise_for_status()
        observed = client.get(config['model'] + '/stats').json()['calls'] - before
    if observed != sum(run['usage']['total_calls'] for run in runs):
        raise ValueError('independent endpoint count differs from ledger calls')
    return {'version': 1, 'ownership_id': ownership_id, 'independent_model_calls': observed, 'runs': runs}
